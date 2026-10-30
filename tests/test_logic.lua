local passed = {}
local function check(value, message) if not value then error(message or 'check failed', 2) end end
local function test(name, callback)
    local ok, err = pcall(callback)
    if not ok then error(name .. ': ' .. tostring(err)) end
    passed[#passed + 1] = name
end

local function candidate(id, overrides)
    local value = {id = id, faction = 'empire', subtype = 'general', in_pool = true,
        provenance = 'ordinary_generated', recruited = false, wounded = false}
    for key, item in pairs(overrides or {}) do value[key] = item end
    return value
end

local function fixture(options)
    options = options or {}
    local pool = {candidate(1), candidate(2), candidate(3, {unique = true})}
    local capital = 'altdorf'
    local calls = {spawn = 0, remove = 0, capital = 0, persist = 0}
    local target = {key = 'grunburg', owner = 'empire', exists = true, settlement = true,
        level = 2, province_capital = false, abandoned = false, besieged = false}
    local a = {}
    function a.read_pool() if options.unreadable then return nil end; return pool end
    function a.spawn_candidate(faction, subtype)
        calls.spawn = calls.spawn + 1
        if options.spawn_fail or (options.fail_second and calls.spawn == 2) then return nil end
        local item = candidate(100 + calls.spawn)
        local copy = {}
        for _, v in ipairs(pool) do copy[#copy + 1] = v end
        copy[#copy + 1] = item
        pool = copy
        if options.overflow_evicts then table.remove(pool, 3) end
        return item
    end
    function a.verify_candidate() return not options.invalid_new end
    function a.remove_candidate(id)
        calls.remove = calls.remove + 1
        if options.remove_fail then return false end
        if not options.remove_lies then
            local copy = {}
            for _, item in ipairs(pool) do if item.id ~= id then copy[#copy + 1] = item end end
            pool = copy
        end
        return true
    end
    function a.turn() return 7 end
    function a.can_act(faction) return faction == 'empire' and not options.blocked end
    function a.persist() calls.persist = calls.persist + 1 end
    function a.supported(subtype) return subtype == 'general' end
    function a.capital() return capital end
    function a.region() return target end
    function a.move_capital(faction, key)
        calls.capital = calls.capital + 1
        if not options.capital_lies then capital = key end
        if options.changes_city then target.level = 3 end
    end
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, sequence = 1, action = 'refresh', faction = 'empire',
        target = 'general', turn = 7, expected = logic.fingerprint(pool)}
    return a, state, request, calls, target
end

for _, field in ipairs({'unique', 'immortal', 'leader', 'wounded', 'starting', 'recruited', 'special'}) do
    test('protect_' .. field, function()
        check(not logic.eligible(candidate(1, {[field] = true}), 'empire', 'general'))
    end)
end
test('protect_unknown_history', function()
    check(not logic.eligible(candidate(1, {provenance = 'unknown'}), 'empire', 'general'))
end)
test('protect_wrong_scope', function()
    check(not logic.eligible(candidate(1), 'cathay', 'general'))
    check(not logic.eligible(candidate(1), 'empire', 'wizard'))
    check(not logic.eligible(candidate(1, {in_pool = false}), 'empire', 'general'))
end)
test('pool_order_independent_fingerprint', function()
    check(logic.fingerprint({candidate(1), candidate(2)}) == logic.fingerprint({candidate(2), candidate(1)}))
end)
test('successful_replacement_preserves_protected', function()
    local a, state, request, calls = fixture()
    local result = logic.execute(state, request, a)
    check(result.status == 'SUCCEEDED' and result.completed == 2)
    check(calls.spawn == 2 and calls.remove == 2 and not state.locked)
    local ids = {}; for _, v in ipairs(a.read_pool()) do ids[v.id] = true end
    check(ids[3] and ids[101] and ids[102] and not ids[1] and not ids[2])
end)
test('ten_refreshes_do_not_accumulate', function()
    local a, state, request, calls = fixture()
    for _ = 1, 10 do
        request.sequence = state.next_sequence
        request.expected = logic.fingerprint(a.read_pool())
        check(logic.execute(state, request, a).status == 'SUCCEEDED')
        check(#a.read_pool() == 3)
    end
    check(calls.spawn == 20 and calls.remove == 20)
end)
test('duplicate_does_not_mutate', function()
    local a, state, request, calls = fixture()
    logic.execute(state, request, a)
    check(logic.execute(state, request, a).status == 'REJECTED')
    check(calls.spawn == 2 and calls.remove == 2)
end)
test('stale_pool_does_not_mutate', function()
    local a, state, request, calls = fixture(); request.expected = 'stale'
    check(logic.execute(state, request, a).reason == 'stale')
    check(calls.spawn == 0 and calls.remove == 0)
end)
test('past_turn_rejected', function()
    local a, state, request, calls = fixture(); request.turn = 6
    check(logic.execute(state, request, a).status == 'REJECTED' and calls.spawn == 0)
end)
test('wrong_faction_rejected', function()
    local a, state, request, calls = fixture(); request.faction = 'cathay'
    check(logic.execute(state, request, a).status == 'REJECTED' and calls.spawn == 0)
end)
test('invalid_action_rejected', function()
    local a, state, request, calls = fixture(); request.action = 'eval'
    check(logic.execute(state, request, a).status == 'REJECTED' and calls.spawn == 0)
end)
test('unsupported_subtype_rejected', function()
    local a, state, request, calls = fixture(); request.target = 'special'
    check(logic.execute(state, request, a).reason == 'unsupported' and calls.spawn == 0)
end)
test('spawn_failure_never_deletes_old', function()
    local a, state, request, calls = fixture({spawn_fail = true})
    check(logic.execute(state, request, a).status == 'REJECTED' and calls.remove == 0)
end)
for _, option in ipairs({'invalid_new', 'overflow_evicts', 'remove_fail', 'remove_lies'}) do
    test('uncertain_' .. option .. '_locks_operation', function()
        local a, state, request, calls = fixture({[option] = true})
        check(logic.execute(state, request, a).status == 'UNKNOWN' and state.locked)
        local spawned = calls.spawn
        request.sequence = state.next_sequence
        check(logic.execute(state, request, a).reason == 'unresolved_operation')
        check(calls.spawn == spawned)
    end)
end
test('partial_success_is_not_full_success', function()
    local a, state, request, calls = fixture({fail_second = true})
    local result = logic.execute(state, request, a)
    check(result.status == 'PARTIAL' and result.completed == 1 and state.locked)
    check(calls.remove == 1)
end)
test('successful_capital_move', function()
    local a, state, request, calls = fixture()
    request.action, request.target, request.expected = 'capital', 'grunburg', 'altdorf'
    local result = logic.execute(state, request, a)
    check(result.status == 'SUCCEEDED' and a.capital() == 'grunburg' and calls.capital == 1)
end)
for _, change in ipairs({'not_owned', 'abandoned', 'besieged', 'no_settlement'}) do
    test('reject_capital_' .. change, function()
        local a, state, request, calls, target = fixture()
        if change == 'not_owned' then target.owner = 'cathay'
        elseif change == 'abandoned' then target.abandoned = true
        elseif change == 'besieged' then target.besieged = true
        else target.settlement = false end
        request.action, request.target, request.expected = 'capital', 'grunburg', 'altdorf'
        check(logic.execute(state, request, a).status == 'REJECTED' and calls.capital == 0)
    end)
end
test('capital_readback_required', function()
    local a, state, request = fixture({capital_lies = true})
    request.action, request.target, request.expected = 'capital', 'grunburg', 'altdorf'
    check(logic.execute(state, request, a).status == 'UNKNOWN' and state.locked)
end)
test('capital_city_attributes_unchanged', function()
    local a, state, request = fixture({changes_city = true})
    request.action, request.target, request.expected = 'capital', 'grunburg', 'altdorf'
    check(logic.execute(state, request, a).status == 'UNKNOWN')
end)
test('unverified_refresh_never_mutates_or_consumes_sequence', function()
    local a, state, request, calls = fixture()
    a.refresh_verified = false
    check(logic.execute(state, request, a).reason == 'refresh_unverified')
    check(calls.spawn == 0 and calls.remove == 0 and state.next_sequence == 1)
end)

test('oversized_pool_never_creates_another_candidate', function()
    local a, state, request, calls = fixture()
    local pool = a.read_pool()
    pool[#pool + 1] = candidate(4)
    request.expected = logic.fingerprint(pool)
    check(logic.execute(state, request, a).reason == 'unsafe_pool_size')
    check(calls.spawn == 0 and calls.remove == 0)
end)
return passed
