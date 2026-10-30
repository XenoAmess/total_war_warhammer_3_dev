local passed = {}
local function test(name, fn) fn(); passed[#passed + 1] = name end
local generated, agent, calls = true, 'wizard', 0
local faction = {is_null_interface = function() return false end,
    command_queue_index = function() return 12 end}
local env = {
    cm = {get_faction = function() return faction end,
        get_local_faction_name = function() return 'empire' end},
    common = {get_context_value = function(kind, id, expression)
        calls = calls + 1
        if kind == 'CcoAgentSubtypeRecord' then
            assert(expression == 'AutoGenerate'); return generated
        end
        assert(id == 12 and expression:find('At%(0%).AgentRecordContext.Key'))
        return agent
    end}, out = function() end
}
local original = package.loaded['script.campaign.xatw3_campaign_utilities.native_pool']
package.loaded['script.campaign.xatw3_campaign_utilities.native_pool'] = {new = function() return {} end}
test('discover_ordinary_subtype_from_engine_metadata', function()
    local runtime = runtime_module.new(logic, env)
    assert(runtime.supported('test_fire_wizard'))
    assert(runtime.subtypes.test_fire_wizard == 'wizard')
end)
test('special_training_and_legendary_subtypes_are_not_auto_generated', function()
    generated = false
    local runtime = runtime_module.new(logic, env)
    assert(not runtime.supported('test_ice_court'))
    generated = true
end)
test('unknown_agent_and_unreadable_metadata_are_rejected', function()
    local runtime = runtime_module.new(logic, env)
    agent = 'special_agent'; assert(not runtime.supported('test_special_agent'))
    agent = nil; assert(not runtime.supported('test_unknown'))
    agent = 'wizard'
end)
test('subtype_key_is_validated_before_context_evaluation', function()
    local runtime = runtime_module.new(logic, env)
    local before = calls
    assert(not runtime.supported('bad"key'))
    assert(not runtime.supported(nil) and calls == before)
end)
test('discovered_types_do_not_leak_between_campaign_instances', function()
    assert(not runtime_module.new(logic, env).subtypes.test_fire_wizard)
end)
package.loaded['script.campaign.xatw3_campaign_utilities.native_pool'] = original
return passed
