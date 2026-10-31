-- Pure business rules for Move Capital. This module also runs under Lua 5.1 in offline tests.
local M = {}

function M.valid_key(value)
    return type(value) == 'string' and #value > 0 and #value <= 160
        and value:match('^[%w_]+$') ~= nil
end

function M.capital_eligible(target, faction, current)
    if not target or not target.exists or not target.settlement or target.abandoned then return false, 'invalid_target' end
    if target.owner ~= faction then return false, 'not_owned' end
    if target.key == current then return false, 'already_capital' end
    if target.besieged then return false, 'besieged' end
    if not current then return false, 'no_capital' end
    return true
end

function M.move_capital(adapter, faction, target, expected)
    local current = adapter.capital(faction)
    if current ~= expected then return {status = 'REJECTED', reason = 'stale'} end
    local before = adapter.region(target)
    local allowed, reason = M.capital_eligible(before, faction, current)
    if not allowed then return {status = 'REJECTED', reason = reason} end
    local original_owner, original_level, original_province_capital = before.owner, before.level, before.province_capital
    adapter.move_capital(faction, target)
    local after = adapter.region(target)
    if adapter.capital(faction) ~= target or not after or after.owner ~= original_owner
        or after.level ~= original_level or after.province_capital ~= original_province_capital then
        return {status = 'UNKNOWN', reason = 'readback_failed'}
    end
    return {status = 'SUCCEEDED', previous = current, target = target}
end

function M.execute(state, request, adapter)
    if request.sequence ~= state.next_sequence then return {status = 'REJECTED', reason = 'duplicate_or_invalid_sequence'} end
    if state.locked then return {status = 'REJECTED', reason = 'unresolved_operation'} end
    if request.version ~= 1 or not M.valid_key(request.faction) or not M.valid_key(request.target)
        or request.turn ~= adapter.turn() or not adapter.can_act(request.faction) then
        return {status = 'REJECTED', reason = 'invalid_request'}
    end
    if request.action ~= 'capital' then
        return {status = 'REJECTED', reason = 'invalid_action'}
    end
    state.next_sequence = state.next_sequence + 1
    state.locked = true
    state.last = {status = 'EXECUTING', sequence = request.sequence, action = request.action}
    adapter.persist(state)
    local ok, result = pcall(function()
        return M.move_capital(adapter, request.faction, request.target, request.expected)
    end)
    if not ok then result = {status = 'UNKNOWN', reason = 'engine_error', detail = tostring(result)} end
    result.sequence, result.action = request.sequence, request.action
    state.last = result
    state.locked = result.status == 'UNKNOWN' or result.status == 'PARTIAL'
    adapter.persist(state)
    return result
end

return M
