local passed = {}
local function check(value, message) if not value then error(message or 'check failed', 2) end end
local function test(name, callback)
    local ok, err = pcall(callback)
    if not ok then error(name .. ': ' .. tostring(err)) end
    passed[#passed + 1] = name
end

local function target(key, overrides)
    local value = {key = key, exists = true, settlement = true, owner = 'empire',
        level = 2, province_capital = false, abandoned = false, besieged = false}
    for k, v in pairs(overrides or {}) do value[k] = v end
    return value
end

local function adapter(options)
    options = options or {}
    local capital = options.capital or 'altdorf'
    local region = options.region or target('grunburg')
    local calls = {move = 0, persist = 0}
    local a = {}
    function a.capital() return capital end
    function a.region() return region end
    function a.move_capital(faction, key)
        calls.move = calls.move + 1
        if not options.capital_lies then capital = key end
        if options.changes_city then region.level = 3 end
        if options.changes_owner then region.owner = 'cathay' end
        if options.changes_province_capital then region.province_capital = true end
    end
    function a.turn() return 7 end
    function a.can_act(faction) return faction == 'empire' and not options.blocked end
    function a.persist() calls.persist = calls.persist + 1 end
    return a, calls
end

test('valid_key_accepts_normal', function()
    check(logic.valid_key('empire'))
    check(logic.valid_key('grunburg'))
    check(logic.valid_key('a_b_c'))
end)

test('valid_key_rejects_empty', function()
    check(not logic.valid_key(''))
end)

test('valid_key_rejects_non_string', function()
    check(not logic.valid_key(123))
    check(not logic.valid_key(nil))
end)

test('valid_key_rejects_too_long', function()
    check(not logic.valid_key(string.rep('a', 161)))
end)

test('valid_key_rejects_invalid_chars', function()
    check(not logic.valid_key('a b'))
    check(not logic.valid_key('a.b'))
    check(not logic.valid_key('a-b'))
end)

test('capital_eligible_normal', function()
    local t = target('grunburg')
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(ok, reason)
end)

test('capital_eligible_not_owned', function()
    local t = target('grunburg', {owner = 'cathay'})
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'not_owned')
end)

test('capital_eligible_already_capital', function()
    local t = target('altdorf')
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'already_capital')
end)

test('capital_eligible_no_capital', function()
    local t = target('grunburg')
    local ok, reason = logic.capital_eligible(t, 'empire', nil)
    check(not ok and reason == 'no_capital')
end)

test('capital_eligible_besieged', function()
    local t = target('grunburg', {besieged = true})
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'besieged')
end)

test('capital_eligible_abandoned', function()
    local t = target('grunburg', {abandoned = true})
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'invalid_target')
end)

test('capital_eligible_no_settlement', function()
    local t = target('grunburg', {settlement = false})
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'invalid_target')
end)

test('capital_eligible_not_exists', function()
    local t = target('grunburg', {exists = false})
    local ok, reason = logic.capital_eligible(t, 'empire', 'altdorf')
    check(not ok and reason == 'invalid_target')
end)

test('capital_eligible_nil_target', function()
    local ok, reason = logic.capital_eligible(nil, 'empire', 'altdorf')
    check(not ok and reason == 'invalid_target')
end)

test('move_capital_success', function()
    local a, calls = adapter()
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'SUCCEEDED' and result.previous == 'altdorf' and result.target == 'grunburg')
    check(calls.move == 1)
end)

test('move_capital_stale_expected', function()
    local a, calls = adapter()
    local result = logic.move_capital(a, 'empire', 'grunburg', 'wrong')
    check(result.status == 'REJECTED' and result.reason == 'stale')
    check(calls.move == 0)
end)

test('move_capital_not_owned', function()
    local a, calls = adapter({region = target('grunburg', {owner = 'cathay'})})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'REJECTED' and result.reason == 'not_owned')
    check(calls.move == 0)
end)

test('move_capital_already_capital', function()
    local a, calls = adapter({region = target('altdorf')})
    local result = logic.move_capital(a, 'empire', 'altdorf', 'altdorf')
    check(result.status == 'REJECTED' and result.reason == 'already_capital')
    check(calls.move == 0)
end)

test('move_capital_besieged', function()
    local a, calls = adapter({region = target('grunburg', {besieged = true})})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'REJECTED' and result.reason == 'besieged')
    check(calls.move == 0)
end)

test('move_capital_readback_capital_mismatch', function()
    local a, calls = adapter({capital_lies = true})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'UNKNOWN' and result.reason == 'readback_failed')
    check(calls.move == 1)
end)

test('move_capital_readback_level_changed', function()
    local a, calls = adapter({changes_city = true})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'UNKNOWN' and result.reason == 'readback_failed')
    check(calls.move == 1)
end)

test('move_capital_readback_owner_changed', function()
    local a, calls = adapter({changes_owner = true})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'UNKNOWN' and result.reason == 'readback_failed')
    check(calls.move == 1)
end)

test('move_capital_readback_province_capital_changed', function()
    local a, calls = adapter({changes_province_capital = true})
    local result = logic.move_capital(a, 'empire', 'grunburg', 'altdorf')
    check(result.status == 'UNKNOWN' and result.reason == 'readback_failed')
    check(calls.move == 1)
end)

test('execute_success_capital', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'SUCCEEDED' and result.sequence == 1 and result.action == 'capital')
    check(state.next_sequence == 2 and not state.locked)
    check(calls.move == 1 and calls.persist >= 2)
end)

test('execute_invalid_action', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'refresh', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_action')
    check(calls.move == 0 and state.next_sequence == 1)
end)

test('execute_duplicate_sequence', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    logic.execute(state, request, a)
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'duplicate_or_invalid_sequence')
    check(calls.move == 1)
end)

test('execute_stale_expected', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'wrong'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'stale')
    check(calls.move == 0)
end)

test('execute_wrong_faction', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'cathay',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_past_turn', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 6, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_locked_state', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = true}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'unresolved_operation')
    check(calls.move == 0)
end)

test('execute_invalid_version', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 2, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_invalid_faction_key', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'a b',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_invalid_target_key', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'a b', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_can_act_false', function()
    local a, calls = adapter({blocked = true})
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'REJECTED' and result.reason == 'invalid_request')
    check(calls.move == 0)
end)

test('execute_engine_error_locks', function()
    local a, calls = adapter()
    function a.move_capital() error('boom') end
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'UNKNOWN' and result.reason == 'engine_error')
    check(state.locked)
end)

test('execute_readback_failure_locks', function()
    local a, calls = adapter({capital_lies = true})
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    local result = logic.execute(state, request, a)
    check(result.status == 'UNKNOWN' and state.locked)
    check(calls.move == 1)
end)

test('execute_preserves_attributes_on_success', function()
    local a, calls = adapter()
    local state = {schema_version = 1, next_sequence = 1, locked = false}
    local request = {version = 1, action = 'capital', faction = 'empire',
        sequence = 1, turn = 7, target = 'grunburg', expected = 'altdorf'}
    logic.execute(state, request, a)
    local r = a.region()
    check(r.owner == 'empire' and r.level == 2 and r.province_capital == false)
end)

return passed
