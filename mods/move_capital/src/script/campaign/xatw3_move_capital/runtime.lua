local M = {}
local PREFIX = 'xatw3_move_capital'

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
    local self = {logic = logic, state = nil, initialized = false}

    function self.log(message)
        out('[' .. PREFIX .. '] ' .. tostring(message))
    end

    function self.persist(state)
        cm:set_saved_value(PREFIX .. '_state', state)
    end

    function self.initialize()
        self.state = cm:get_saved_value(PREFIX .. '_state')
        if type(self.state) ~= 'table' then
            self.state = {schema_version = 1, next_sequence = 1, locked = false}
        end
        if self.state.schema_version ~= 1 then self.state.locked = true end
        if self.state.last and self.state.last.status == 'EXECUTING' then
            self.state.last.status, self.state.last.reason = 'UNKNOWN', 'interrupted'
            self.state.locked = true
        end
        self.initialized = true
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
        require('script.xatw3_multiplayer').install(environment, PREFIX, self, false)
    end

    function self.capital(faction_key)
        local faction = cm:get_faction(faction_key)
        if not faction or not faction:has_home_region() then return nil end
        return faction:home_region():name()
    end

    function self.region(key)
        local region = cm:get_region(key)
        if not valid(region) then return nil end
        local settlement = region:settlement()
        return {
            key = key, exists = true, owner = region:owning_faction():name(),
            settlement = valid(settlement), abandoned = region:is_abandoned(),
            besieged = safe(function() return region:garrison_residence():is_under_siege() end, true),
            level = safe(function() return settlement:primary_slot():building():building_level() end, 0),
            province_capital = region:is_province_capital()
        }
    end

    function self.move_capital(faction_key, region_key)
        cm:change_home_region_of_faction(cm:get_faction(faction_key), cm:get_region(region_key))
    end

    function self.report(result)
        self.log('RESULT sequence=' .. tostring(result.sequence) .. ' action=' .. tostring(result.action)
            .. ' status=' .. result.status .. ' reason=' .. tostring(result.reason))
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
        if request.action ~= 'capital' or request.turn ~= self.turn()
            or not self.model_can_act(request.faction) or self.state.locked then return false, 'not_available' end
        local current = self.capital(request.faction)
        local target = self.region(request.target)
        if current ~= request.expected or not logic.capital_eligible(target, request.faction, current) then
            return false, 'stale_or_invalid_target'
        end
        return true, sync.fields({'0.2.0', require('script.xatw3_release_move_capital'), sync.identity(), self.state.next_sequence, current, target.owner,
            target.level, tostring(target.province_capital)})
    end

    function self.multiplayer_after(request, result)
        local sync = require('script.xatw3_multiplayer')
        local region = self.region(request.target)
        return sync.fields({self.state.next_sequence, tostring(self.state.locked),
            self.capital(request.faction) or '', region and region.owner or '',
            region and region.level or '', region and tostring(region.province_capital) or ''})
    end

    return self
end

return M
