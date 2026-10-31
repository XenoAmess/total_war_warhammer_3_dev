local passed = {}
local function test(name, fn) fn(); passed[#passed + 1] = name end
local function fixture(saved)
    local values = saved or {}
    local reads, writes, moves, home = {}, {}, 0, 'old_home'
    local region = {is_null_interface = function() return false end,
        owning_faction = function() return {name = function() return 'player' end} end,
        settlement = function() return {is_null_interface = function() return false end,
            primary_slot = function() return {building = function() return {building_level = function() return 2 end} end} end} end,
        is_abandoned = function() return false end,
        garrison_residence = function() return {is_under_siege = function() return false end} end,
        is_province_capital = function() return false end}
    local faction = {is_human = function() return true end, name = function() return 'player' end,
        is_factions_turn = function() return true end, has_home_region = function() return true end,
        home_region = function() return {name = function() return home end} end}
    local cm = {
        get_saved_value = function(_, key) reads[#reads + 1] = key; return values[key] end,
        set_saved_value = function(_, key, state)
            values[key] = state; writes[#writes + 1] = {key = key, status = state.last and state.last.status}
        end,
        get_campaign_name = function() return 'main_warhammer' end,
        is_multiplayer = function() return false end,
        get_local_faction_name = function() return 'player' end,
        get_faction = function(_, key) if key == 'player' then return faction end end,
        get_region = function() return region end,
        model = function() return {turn_number = function() return 3 end,
            pending_battle = function() return {is_active = function() return false end} end} end,
        change_home_region_of_faction = function()
            assert(writes[#writes].status == 'EXECUTING', 'Mutation preceded durable EXECUTING record')
            moves = moves + 1; home = 'new_home'
        end
    }
    local rt = runtime_module.new(logic, {cm = cm, out = function() end})
    return rt, values, reads, writes, function() return moves end, cm
end

test('independent_save_key_preserves_legacy_state', function()
    local old = {next_sequence = 57, history = {known = true}}
    local rt, values, reads = fixture({xatw3_campaign_utilities_state = old})
    assert(rt.state == nil); rt.initialize()
    assert(#reads == 1 and reads[1] == 'xatw3_move_capital_state')
    assert(rt.state.next_sequence == 1 and not rt.state.locked)
    assert(values.xatw3_campaign_utilities_state == old and old.next_sequence == 57 and old.history.known)
end)

test('interrupted_move_locks_without_replay', function()
    local rt, _, _, _, moves = fixture({xatw3_move_capital_state = {
        schema_version = 1, next_sequence = 2, locked = false, last = {status = 'EXECUTING', action = 'capital'}}})
    rt.initialize()
    assert(rt.state.locked and rt.state.last.status == 'UNKNOWN' and moves() == 0)
end)

test('runtime_moves_once_and_reads_back_model', function()
    local rt, _, _, writes, moves = fixture(); rt.initialize()
    local request = {version = 1, action = 'capital', faction = 'player', sequence = 1,
        turn = 3, target = 'new_home', expected = 'old_home'}
    assert(rt.execute(request).status == 'SUCCEEDED')
    assert(moves() == 1 and rt.capital('player') == 'new_home' and not rt.state.locked)
    assert(writes[2].status == 'EXECUTING' and writes[3].status == 'SUCCEEDED')
    assert(rt.execute(request).reason == 'duplicate_or_invalid_sequence' and moves() == 1)
end)

test('multiplayer_is_rejected_before_mutation', function()
    local rt, _, _, _, moves, cm = fixture(); rt.initialize()
    cm.is_multiplayer = function() return true end
    local result = rt.execute({version = 1, action = 'capital', faction = 'player', sequence = 1,
        turn = 3, target = 'new_home', expected = 'old_home'})
    assert(result.status == 'REJECTED' and moves() == 0 and rt.state.next_sequence == 1)
end)
return passed
