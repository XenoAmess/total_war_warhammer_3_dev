-- Shared by both packs. UI timers may report readiness, never mutate the model.
local M = {}
function M.identity() return require('script.xatw3_transport_identity') end
local LIMIT = 16000000 -- exact in the game's float Lua
local function integer(n) return type(n) == 'number' and n >= 1 and n < LIMIT and n == math.floor(n) end
local function key(s) return type(s) == 'string' and #s > 0 and #s <= 160 and s:match('^[%w_]+$') end
local function hex(s) return (tostring(s):gsub('.', function(c) return string.format('%02x', string.byte(c)) end)) end
local function unhex(s)
    if #s % 2 ~= 0 or s:match('[^%da-f]') then return nil end
    return (s:gsub('..', function(c) return string.char(tonumber(c, 16)) end))
end
function M.fields(values)
    local out = {}
    for i, v in ipairs(values) do out[i] = hex(v) end
    return table.concat(out, '|')
end
local function split(text)
    local out = {}
    for token in (text .. '|'):gmatch('(.-)|') do
        local value = unhex(token); if value == nil then return nil end
        out[#out + 1] = value
    end
    return out
end

-- Pure transport, exercised with independent Lua states and one ordered event log.
function M.new(host, saved)
    if saved ~= nil and type(saved) ~= 'table' then
        saved = {schema = 1, epoch = 0, counters = {}, blocked = true}
    end
    saved = saved or {schema = 1, epoch = 0, counters = {}}
    local self = {handlers = {}, state = saved, active = nil}
    if saved.schema ~= 1 or not integer((saved.epoch or 0) + 1) or type(saved.counters) ~= 'table' then
        saved.blocked = true; saved.epoch = 0; saved.counters = {}
    end
    if saved.pending then saved.blocked = true end -- never replay interrupted work
    saved.epoch = saved.epoch + 1
    host.persist(saved)
    local function members()
        local list, seen = host.members(), {}
        if type(list) ~= 'table' or #list < 2 or #list > 8 then return nil end
        local copy = {}
        for _, name in ipairs(list) do
            if not key(name) or seen[name] then return nil end
            seen[name] = true; copy[#copy + 1] = name
        end
        table.sort(copy); return copy, table.concat(copy, ',')
    end
    local fragments, fragment_count, message_id = {}, 0, 0
    local function send(kind, tx, values)
        local packet = 'xatw3mp|1|' .. M.fields({saved.epoch, kind, tx.owner, tx.faction, tx.nonce})
        if values then packet = packet .. '|' .. M.fields(values) end
        if #packet > 65536 then return false end
        if #packet <= 240 then host.send(packet); return true end
        -- Exact snapshots can exceed one engine event. Bound every wire event;
        -- partial delivery never produces a readiness vote or model operation.
        message_id = message_id + 1
        if not integer(message_id) then return false end
        local count = math.ceil(#packet / 90)
        for index = 1, count do
            host.send(table.concat({'xatw3frag', '1', saved.epoch, message_id, index, count,
                hex(packet:sub((index - 1) * 90 + 1, index * 90))}, '|'))
        end
        return true
    end
    local function finish(result, blocked)
        local tx = self.active
        if blocked then saved.blocked = true end
        saved.pending = nil; self.active = nil; host.persist(saved)
        if tx then
            local h = self.handlers[tx.owner]
            if h then h.release() end
            result.faction, result.request_id = tx.faction, tx.nonce
            if h then h.result(result) end
        end
    end
    local function all(votes, tx)
        for _, name in ipairs(tx.members) do if votes[name] == nil then return false end end
        return true
    end
    local function same(votes, tx)
        local reference = votes[tx.members[1]]
        for _, name in ipairs(tx.members) do if votes[name] ~= reference then return nil end end
        return reference
    end
    local function checked(handler, request)
        local called, ok, snapshot = pcall(handler.check, request)
        if not called or type(snapshot) ~= 'string' then return false, 'preflight_error' end
        return ok == true, snapshot
    end
    function self.available()
        local list = members()
        return not saved.blocked and not self.active and list ~= nil
    end
    function self.submit(owner, request)
        local faction = host.local_faction()
        if not self.available() or not key(owner) or request.faction ~= faction
            or not integer(request.turn) or not key(request.target) then return false end
        local nonce = (saved.counters[owner .. ':' .. faction] or 0) + 1
        if not integer(nonce) then return false end
        local _, roster = members()
        return send('request', {owner = owner, faction = faction, nonce = nonce},
            {request.action, request.turn, request.target, request.expected or '', roster})
    end
    function self.cancel()
        if self.active and self.active.phase ~= 'results' then send('cancel', self.active) end
    end
    function self.receive(sender, text, assembled)
        if type(text) ~= 'string' or #text > (assembled and 65536 or 240) then return end
        if not assembled and text:sub(1, 12) == 'xatw3frag|1|' then
            local epoch, id, index, count, chunk = text:match('^xatw3frag|1|(%d+)|(%d+)|(%d+)|(%d+)|([%da-f]+)$')
            epoch, id, index, count = tonumber(epoch), tonumber(id), tonumber(index), tonumber(count)
            if epoch ~= saved.epoch or not integer(id) or not integer(index) or not integer(count)
                or count > 729 or index > count or #chunk > 180 then return end
            chunk = unhex(chunk); if not chunk then return end
            local list = members(); if not list then return end
            local included = false; for _, name in ipairs(list) do if name == sender then included = true end end
            if not included then return end
            local buffer_id = M.fields({sender, epoch, id})
            local buffer = fragments[buffer_id]
            if not buffer then
                if fragment_count >= 32 then return end
                buffer = {count = count, parts = {}, received = 0}; fragments[buffer_id] = buffer
                fragment_count = fragment_count + 1
            end
            if count ~= buffer.count then return end
            if buffer.parts[index] then return end
            buffer.parts[index] = chunk; buffer.received = buffer.received + 1
            if buffer.received == count then
                fragments[buffer_id] = nil; fragment_count = fragment_count - 1
                local packet = table.concat(buffer.parts)
                self.receive(sender, packet, true)
            end
            return
        end
        if text:sub(1, 10) ~= 'xatw3mp|1|' then return end
        local p = split(text:sub(11)); if not p or #p < 5 then return end
        local epoch, kind, owner, faction, nonce = tonumber(p[1]), p[2], p[3], p[4], tonumber(p[5])
        if epoch ~= saved.epoch or not key(owner) or not key(faction) or not integer(nonce) then return end
        if kind == 'request' then
            if #p ~= 10 or sender ~= faction or saved.blocked then return end
            local list, roster = members(); if not list or p[10] ~= roster then return end
            local included = false; for _, name in ipairs(list) do if name == sender then included = true end end
            if not included or not integer(tonumber(p[7])) or not key(p[8]) then return end
            local counter = owner .. ':' .. faction
            if nonce ~= (saved.counters[counter] or 0) + 1 then return end
            saved.counters[counter] = nonce; host.persist(saved)
            local h = self.handlers[owner]
            if self.active then
                if h then h.result({status = 'REJECTED', reason = 'multiplayer_busy', faction = faction,
                    request_id = nonce}) end
                return
            end
            if not h then return end -- missing Mod never supplies a ready vote
            local tx = {owner = owner, faction = faction, nonce = nonce, members = list,
                roster = roster, votes = {}, phase = 'ready', request = {version = 1,
                action = p[6], turn = tonumber(p[7]), target = p[8], expected = p[9], faction = faction}}
            self.active = tx; saved.pending = {owner = owner, faction = faction, nonce = nonce}
            host.persist(saved)
            local prepared = pcall(h.prepare, tx.request, function(ok, snapshot)
                if self.active ~= tx or tx.phase ~= 'ready' then return end
                snapshot = type(snapshot) == 'string' and snapshot or 'invalid_snapshot'
                if not send('ready', tx, {ok and 'yes' or 'no', snapshot}) then
                    send('ready', tx, {'no', 'snapshot_too_large'})
                end
            end)
            if not prepared then send('ready', tx, {'no', 'prepare_error'}) end
            return
        end
        local tx = self.active
        if not tx or tx.owner ~= owner or tx.faction ~= faction or tx.nonce ~= nonce then return end
        local included = false; for _, name in ipairs(tx.members) do if name == sender then included = true end end
        if not included then return end
        local _, roster = members()
        if roster ~= tx.roster then finish({status = 'UNKNOWN', reason = 'multiplayer_members_changed'}, true); return end
        if kind == 'cancel' and #p == 5 and tx.phase ~= 'results' then
            finish({status = 'REJECTED', reason = 'multiplayer_cancelled'}); return
        end
        if kind ~= tx.phase or #p ~= 7 or tx.votes[sender] ~= nil then return end
        tx.votes[sender] = M.fields({p[6], p[7]})
        if not all(tx.votes, tx) then return end
        local agreed = same(tx.votes, tx)
        if kind == 'ready' then
            if not agreed or p[6] ~= 'yes' then
                finish({status = 'REJECTED', reason = 'multiplayer_preflight_failed'}); return
            end
            tx.snapshot = p[7]; tx.phase = 'arm'; tx.votes = {}
            local ok, snapshot = checked(self.handlers[owner], tx.request)
            if not send('arm', tx, {ok and 'yes' or 'no', snapshot or ''}) then
                send('arm', tx, {'no', 'snapshot_too_large'})
            end
        elseif kind == 'arm' then
            if not agreed or p[6] ~= 'yes' or p[7] ~= tx.snapshot then
                finish({status = 'REJECTED', reason = 'multiplayer_stale'}); return
            end
            -- Final local readback is a safety check, not an atomic rollback promise.
            tx.phase = 'results'; tx.votes = {}
            local h = self.handlers[owner]
            local ok, snapshot = checked(h, tx.request)
            local result
            if ok and snapshot == tx.snapshot then
                local called, value = pcall(h.execute, tx.request)
                result = called and type(value) == 'table' and value or {status = 'UNKNOWN', reason = 'engine_error'}
            else result = {status = 'UNKNOWN', reason = 'commit_precondition_changed'} end
            tx.result = result
            local read, after = pcall(h.after, tx.request, result)
            if not read or type(after) ~= 'string' then result = {status = 'UNKNOWN', reason = 'result_readback_failed'}; tx.result = result; after = '' end
            local body = (result.status or 'UNKNOWN') .. ':' .. (result.reason or '') .. ':' .. (after or '')
            if not send('results', tx, {result.status or 'UNKNOWN', body}) then
                tx.result = {status = 'UNKNOWN', reason = 'result_too_large'}
                send('results', tx, {'UNKNOWN', 'result_too_large'})
            end
        elseif kind == 'results' then
            if not agreed or p[6] == 'UNKNOWN' or p[6] == 'PARTIAL' then
                finish({status = 'UNKNOWN', reason = 'multiplayer_result_mismatch'}, true)
            else finish(tx.result) end
        end
    end
    return self
end

-- Engine adapter. One instance serializes both Mods in this campaign.
function M.attach(environment, owner, handler)
    local cm, core = environment.cm, environment.core
    if not M.bus or M.manager ~= cm then
        M.manager = cm
        local function local_faction() return cm:get_local_faction_name(true) end
        M.bus = M.new({local_faction = local_faction,
            members = function() return cm:get_active_human_factions() end,
            persist = function(s) cm:set_saved_value('xatw3_multiplayer_v1', s) end,
            send = function(packet)
                local faction = cm:get_faction(local_faction())
                if faction and not faction:is_null_interface() then
                    environment.CampaignUI.TriggerCampaignScriptEvent(faction:command_queue_index(), packet)
                end
            end}, cm:get_saved_value('xatw3_multiplayer_v1'))
        core:add_listener('xatw3_multiplayer_v1', 'UITrigger', true, function(context)
            local faction = cm:model():faction_for_command_queue_index(context:faction_cqi())
            if faction and not faction:is_null_interface() then M.bus.receive(faction:name(), context:trigger()) end
        end, true)
    end
    M.bus.handlers[owner] = handler
    return M.bus
end

function M.install(environment, owner, runtime, close_panel)
    local cm, core, ui = environment.cm, environment.core, environment.CampaignUI
    local guarding = false
    local function panel() return environment.find_uicomponent(core:get_ui_root(), 'character_panel') end
    local function close()
        ui.ClosePanel('character_panel'); ui.CloseCurrentHUDPanel()
    end
    local handler = {}
    handler.check = runtime.multiplayer_check
    function handler.prepare(request, done)
        guarding = close_panel
        if not close_panel then
            local ok, snapshot = handler.check(request); done(ok, snapshot); return
        end
        close()
        local attempts = 0
        local function poll()
            local p = panel()
            if not guarding then return end
            attempts = attempts + 1
            if p and p:Visible() then
                if attempts >= 30 then done(false, 'panel_close_failed'); return end
                close(); cm:callback(poll, 0.1); return
            end
            local ok, snapshot = handler.check(request); done(ok, snapshot)
        end
        cm:callback(poll, 0.1)
    end
    function handler.execute(request)
        runtime.multiplayer_executing = true
        request.sequence = runtime.state.next_sequence -- bus is serialized on every peer
        local ok, result = pcall(runtime.execute, request)
        runtime.multiplayer_executing = false
        if not ok then return {status = 'UNKNOWN', reason = 'engine_error'} end
        return result
    end
    handler.after = runtime.multiplayer_after
    function handler.release() guarding = false end
    function handler.result(result)
        if result.faction == cm:get_local_faction_name(true) then runtime.report(result) end
    end
    runtime.multiplayer = M.attach(environment, owner, handler)
    if close_panel then
        core:add_listener(owner .. '_mp_close', 'PanelOpenedCampaign', function(context)
            return guarding and context.string == 'character_panel'
        end, close, true)
    end
end
return M
