local M = {}
local PREFIX = 'xatw3_campaign_utilities'

-- Seed types also let the UI identify an empty recruitment category.
M.subtypes = {
    wh3_main_ksl_boyar = 'general',
    wh3_main_ksl_patriarch = 'dignitary'
}

local function valid(object)
    return object and not object:is_null_interface()
end

local function safe(fn, fallback)
    local ok, value = pcall(fn)
    if ok and value ~= nil then return value end
    return fallback
end

function M.new(logic, environment)
    environment = environment or getfenv(2)
    local cm, common, out = environment.cm, environment.common, environment.out
    local self = {logic = logic, subtypes = M.subtypes, refresh_verified = false, state = nil,
        pending_entries = {}, pending_recruited = {}, initialized = false}
    self.native_pool = require('script.campaign.xatw3_campaign_utilities.native_pool').new(environment)
    self.subtypes = {}
    for subtype, agent in pairs(M.subtypes) do self.subtypes[subtype] = agent end
    local ordinary_agents = {general = true, dignitary = true, wizard = true, champion = true,
        engineer = true, runesmith = true, spy = true}

    function self.supported(subtype, faction_key)
        if not logic.valid_key(subtype) or logic.special_subtype(subtype) then return false end
        if self.subtypes[subtype] and not (cm.is_multiplayer and cm:is_multiplayer()) then return true end
        local generated = safe(function()
            return common.get_context_value('CcoAgentSubtypeRecord', subtype, 'AutoGenerate')
        end, false)
        if generated ~= true then return false end
        local faction = cm:get_faction(faction_key or cm:get_local_faction_name())
        if not valid(faction) then return false end
        local agent = safe(function()
            return common.get_context_value('CcoCampaignFaction', faction:command_queue_index(),
                'CharacterRecruitmentPoolEntriesForAgentSubtype(DatabaseRecordContext("CcoAgentSubtypeRecord","'
                .. subtype .. '")).At(0).AgentRecordContext.Key')
        end, nil)
        if not ordinary_agents[agent] then return false end
        self.subtypes[subtype] = agent
        return true
    end

    function self.log(message)
        out('[' .. PREFIX .. '] ' .. tostring(message))
    end

    function self.persist(state)
        cm:set_saved_value(PREFIX .. '_state', state)
    end

    function self.initialize()
        self.state = cm:get_saved_value(PREFIX .. '_state')
        if type(self.state) ~= 'table' then
            self.state = {schema_version = 1, next_sequence = 1, history = {}, locked = false}
        end
        if self.state.schema_version ~= 1 then self.state.locked = true end
        if self.state.last and self.state.last.status == 'EXECUTING' then
            self.state.last.status, self.state.last.reason = 'UNKNOWN', 'interrupted'
            self.state.locked = true
        end
        self.initialized = true
        self.refresh_verified = self.native_pool.initialize()
        self.log('NATIVE build=' .. tostring(self.native_pool.build) .. ' ready=' .. tostring(self.refresh_verified)
            .. ' reason=' .. tostring(self.native_pool.reason))
        for _, id in ipairs(self.pending_entries) do
            local fm = cm:get_family_member_by_cqi(id)
            if fm then self.observe_entry(fm:character_details()) end
        end
        for id in pairs(self.pending_recruited) do self.mark_recruited(id) end
        self.pending_entries, self.pending_recruited = {}, {}
        self.persist(self.state)
    end

    function self.observe_entry(details)
        if not valid(details) or not valid(details:faction()) or not details:faction():is_human() then return end
        local subtype = details:character_subtype_key()
        if not self.supported(subtype, details:faction():name()) then return end
        if not self.initialized then
            self.pending_entries[#self.pending_entries + 1] = details:family_member():command_queue_index()
            return
        end
        local id = details:family_member():command_queue_index()
        local key = tostring(id)
        if self.state.history[key] then return end
        local starting = details:start_pos_key()
        local actor = details:character()
        local normal = not details:is_unique() and not details:is_immortal()
            and (starting == nil or starting == '' or tostring(starting) == '0')
            and not valid(actor)
        self.state.history[key] = {
            faction = details:faction():name(), subtype = subtype,
            provenance = normal and 'ordinary_generated' or 'unknown', recruited = false
        }
        self.persist(self.state)
    end

    function self.mark_recruited(id)
        if not self.initialized then self.pending_recruited[id] = true; return end
        local key = tostring(id)
        self.state.history[key] = self.state.history[key] or {provenance = 'unknown'}
        self.state.history[key].recruited = true
        self.persist(self.state)
    end

    function self.turn() return cm:model():turn_number() end
    function self.campaign_supported() return cm:get_campaign_name() == 'main_warhammer' end

    function self.model_can_act(faction_key)
        if not self.campaign_supported() then return false end
        local faction = cm:get_faction(faction_key)
        return faction and faction:is_human() and faction:is_factions_turn()
            and not cm:model():pending_battle():is_active()
    end

    function self.can_act(faction_key)
        if not self.model_can_act(faction_key) then return false end
        if self.multiplayer_executing then return true end
        if faction_key ~= cm:get_local_faction_name() then return false end
        return not cm:is_multiplayer() or (self.multiplayer and self.multiplayer.available()) or false
    end

    function self.install_multiplayer()
        require('script.xatw3_multiplayer').install(environment, PREFIX, self, true)
    end

    function self.describe(id, in_pool)
        local fm = cm:get_family_member_by_cqi(id)
        if not fm then return nil end
        local details = fm:character_details()
        if not valid(details) then return nil end
        local actor = fm:character()
        local history = self.state.history[tostring(id)] or {}
        local start = details:start_pos_key()
        return {
            id = id, faction = details:faction():name(), subtype = details:character_subtype_key(),
            in_pool = in_pool, unique = details:is_unique(), immortal = details:is_immortal(),
            starting = start ~= nil and start ~= '' and tostring(start) ~= '0',
            wounded = valid(actor) and actor:is_wounded() or false,
            leader = valid(actor) and actor:is_faction_leader() or false,
            recruited = history.recruited == true,
            special = logic.special_subtype(details:character_subtype_key()),
            provenance = history.provenance or 'unknown',
            male = details:is_male(), forename = details:get_forename(), surname = details:get_surname(),
            background = details:background_skill()
        }
    end

    function self.read_pool(faction_key, subtype)
        if not logic.valid_key(faction_key) or not logic.valid_key(subtype) then return nil end
        local faction = cm:get_faction(faction_key)
        if not faction then return nil end
        local expression = 'CharacterRecruitmentPoolEntriesForAgentSubtype(DatabaseRecordContext("CcoAgentSubtypeRecord","'
            .. subtype .. '"))'
        local count = safe(function()
            return common.get_context_value('CcoCampaignFaction', faction:command_queue_index(), expression .. '.Size')
        end, nil)
        if type(count) ~= 'number' or count < 0 or count > 100 then return nil end
        local pool, seen = {}, {}
        for index = 0, count - 1 do
            local id = safe(function()
                return common.get_context_value('CcoCampaignFaction', faction:command_queue_index(),
                    expression .. '.At(' .. index .. ').CharacterContext.FamilyMemberCQI')
            end, nil)
            if type(id) ~= 'number' or seen[id] then return nil end
            local candidate = self.describe(id, true)
            if not candidate then return nil end
            seen[id], pool[#pool + 1] = true, candidate
        end
        return pool
    end

    function self.spawn_candidate(faction, subtype, old)
        if not self.supported(subtype, faction) then return nil, 'unsupported_subtype' end
        local details = cm:spawn_character_to_pool(faction, '', '', '', '', 30, old.male,
            self.subtypes[subtype], subtype, false, '')
        if not valid(details) then return nil, 'spawn_failed' end
        local id = details:family_member():command_queue_index()
        self.state.history[tostring(id)] = {faction = faction, subtype = subtype,
            provenance = 'ordinary_generated', recruited = false}
        self.persist(self.state)
        return self.describe(id, true)
    end

    function self.verify_candidate(candidate)
        local fm = cm:get_family_member_by_cqi(candidate.id)
        if not fm then return false end
        local details = fm:character_details()
        local name = safe(function() return details:get_forename() end, nil)
        return type(candidate.background) == 'string' and candidate.background ~= ''
            and type(name) == 'string' and name ~= ''
            and not candidate.unique and not candidate.immortal
    end

    function self.can_remove_candidate(id)
        local panel = environment.find_uicomponent(environment.core:get_ui_root(), 'character_panel')
        if not self.multiplayer_executing and panel and panel:Visible() then return false, 'recruitment_panel_open' end
        local fm = cm:get_family_member_by_cqi(id)
        if not fm then return false end
        return self.native_pool.can_remove(fm:character_details())
    end

    function self.remove_candidate(id)
        local fm = cm:get_family_member_by_cqi(id)
        if not fm then return false end
        return self.native_pool.remove(fm:character_details())
    end

    function self.report(result)
        self.log('RESULT sequence=' .. tostring(result.sequence) .. ' action=' .. tostring(result.action)
            .. ' status=' .. result.status .. ' reason=' .. tostring(result.reason)
            .. ' completed=' .. tostring(result.completed) .. ' added=' .. tostring(result.added))
        if result.detail then self.log('DETAIL ' .. tostring(result.detail)) end
        if self.on_result then self.on_result(result) end
    end

    function self.execute(request)
        if cm:is_multiplayer() and not self.multiplayer_executing then
            return {status = 'REJECTED', reason = 'multiplayer_protocol_required'}
        end
        local result = logic.execute(self.state, request, self)
        if not self.multiplayer_executing then self.report(result) end
        return result
    end

    function self.multiplayer_check(request)
        local sync = require('script.xatw3_multiplayer')
        if request.action ~= 'refresh' or request.turn ~= self.turn() or not self.refresh_verified
            or not self.model_can_act(request.faction) or self.state.locked
            or not self.supported(request.target, request.faction) then return false, 'not_available' end
        local panel = environment.find_uicomponent(environment.core:get_ui_root(), 'character_panel')
        if panel and panel:Visible() then return false, 'recruitment_panel_open' end
        local pool = self.read_pool(request.faction, request.target)
        if not pool or #pool >= 100 then return false, 'pool_unavailable' end
        local plan = logic.plan(pool, request.faction, request.target)
        if plan.fingerprint ~= request.expected or (#plan.replace == 0 and plan.add == 0) then
            return false, 'stale_or_empty'
        end
        for _, candidate in ipairs(plan.replace) do
            if not self.can_remove_candidate(candidate.id) then return false, 'native_pool_unavailable' end
        end
        local mr = (environment._G or _G).memreader_plus
        return true, sync.fields({'0.3.0', require('script.xatw3_release_recruitment_refresh'), sync.identity(), self.native_pool.build or '', mr and mr.plus_version or '',
            self.state.next_sequence, self.subtypes[request.target], plan.fingerprint})
    end

    function self.multiplayer_after(request, result)
        local sync = require('script.xatw3_multiplayer')
        local pool = self.read_pool(request.faction, request.target)
        return sync.fields({self.state.next_sequence, tostring(self.state.locked),
            result.completed or 0, result.added or 0, pool and logic.fingerprint(pool) or 'unreadable'})
    end

    return self
end

return M
