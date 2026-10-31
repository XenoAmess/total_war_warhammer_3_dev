-- Pure business rules. This module also runs under Lua 5.1 in offline tests.
local M = {}

function M.valid_key(value)
    return type(value) == 'string' and #value > 0 and #value <= 160
        and value:match('^[%w_]+$') ~= nil
end

function M.eligible(candidate, faction, subtype)
    if candidate.faction ~= faction or candidate.subtype ~= subtype then return false, 'wrong_scope' end
    if not candidate.in_pool then return false, 'not_in_pool' end
    if candidate.unique or candidate.immortal or candidate.leader or candidate.wounded
        or candidate.starting or candidate.recruited or candidate.special then
        return false, 'protected'
    end
    if candidate.provenance ~= 'ordinary_generated' then return false, 'unknown_history' end
    return true
end

function M.fingerprint(pool)
    local entries = {}
    for _, candidate in ipairs(pool) do
        entries[#entries + 1] = tostring(candidate.id) .. ':' .. tostring(candidate.recruited)
            .. ':' .. tostring(candidate.wounded) .. ':' .. tostring(candidate.provenance)
    end
    table.sort(entries)
    return table.concat(entries, ',')
end

function M.plan(pool, faction, subtype)
    local plan = {replace = {}, protected = {}, fingerprint = M.fingerprint(pool)}
    for _, candidate in ipairs(pool) do
        if M.eligible(candidate, faction, subtype) then
            plan.replace[#plan.replace + 1] = candidate
        else
            plan.protected[#plan.protected + 1] = candidate.id
        end
    end
    table.sort(plan.replace, function(a, b) return a.id < b.id end)
    return plan
end

local function contains(pool, id)
    for _, candidate in ipairs(pool) do if candidate.id == id then return true end end
    return false
end

function M.refresh(adapter, faction, subtype, expected)
    local before = adapter.read_pool(faction, subtype)
    if not before then return {status = 'REJECTED', reason = 'pool_unavailable', completed = 0} end
    if #before >= 100 then return {status = 'REJECTED', reason = 'unsafe_pool_size', completed = 0} end
    local plan = M.plan(before, faction, subtype)
    if plan.fingerprint ~= expected then
        return {status = 'REJECTED', reason = 'stale', completed = 0}
    end
    if #plan.replace == 0 then return {status = 'REJECTED', reason = 'no_candidates', completed = 0} end
    if adapter.can_remove_candidate then
        for _, candidate in ipairs(plan.replace) do
            if not adapter.can_remove_candidate(candidate.id) then
                return {status = 'REJECTED', reason = 'native_pool_unavailable', completed = 0}
            end
        end
    end
    local result = {status = 'SUCCEEDED', completed = 0, total = #plan.replace, pairs = {}}
    for _, old in ipairs(plan.replace) do
        local new, reason = adapter.spawn_candidate(faction, subtype, old)
        if not new then
            result.status = result.completed == 0 and 'REJECTED' or 'PARTIAL'
            result.reason = reason or 'spawn_failed'
            return result
        end
        result.pending_new_id = new.id
        local current = adapter.read_pool(faction, subtype)
        local safe = current and #current == #before + 1 and contains(current, new.id)
        if safe then
            for _, candidate in ipairs(before) do
                if not contains(current, candidate.id) then safe = false end
            end
        end
        if not safe or not adapter.verify_candidate(new) then
            result.status, result.reason = 'UNKNOWN', 'invalid_generated_candidate'
            return result
        end
        if not adapter.remove_candidate(old.id) then
            result.status, result.reason = 'UNKNOWN', 'remove_failed'
            return result
        end
        current = adapter.read_pool(faction, subtype)
        safe = current and #current == #before and not contains(current, old.id) and contains(current, new.id)
        if safe then
            for _, candidate in ipairs(before) do
                if candidate.id ~= old.id and not contains(current, candidate.id) then safe = false end
            end
        end
        if not safe then result.status, result.reason = 'UNKNOWN', 'readback_failed'; return result end
        result.completed = result.completed + 1
        result.pairs[#result.pairs + 1] = {old = old.id, new = new.id}
        result.pending_new_id = nil
        before = current
    end
    return result
end

function M.execute(state, request, adapter)
    if request.action == 'refresh' and adapter.refresh_verified == false then
        return {status = 'REJECTED', reason = 'refresh_unverified'}
    end
    if request.sequence ~= state.next_sequence then return {status = 'REJECTED', reason = 'duplicate_or_invalid_sequence'} end
    if state.locked then return {status = 'REJECTED', reason = 'unresolved_operation'} end
    if request.version ~= 1 or not M.valid_key(request.faction) or not M.valid_key(request.target)
        or request.turn ~= adapter.turn() or not adapter.can_act(request.faction) then
        return {status = 'REJECTED', reason = 'invalid_request'}
    end
    if request.action ~= 'refresh' then
        return {status = 'REJECTED', reason = 'invalid_action'}
    end
    state.next_sequence = state.next_sequence + 1
    state.locked = true
    state.last = {status = 'EXECUTING', sequence = request.sequence, action = request.action}
    adapter.persist(state)
    local ok, result = pcall(function()
        if not adapter.supported(request.target) then return {status = 'REJECTED', reason = 'unsupported'} end
        return M.refresh(adapter, request.faction, request.target, request.expected)
    end)
    if not ok then result = {status = 'UNKNOWN', reason = 'engine_error', detail = tostring(result)} end
    result.sequence, result.action = request.sequence, request.action
    state.last = result
    state.locked = result.status == 'UNKNOWN' or result.status == 'PARTIAL'
    adapter.persist(state)
    return result
end

return M
