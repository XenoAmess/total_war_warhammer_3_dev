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

test('caravan_and_convoy_rejected_before_cache_metadata_or_spawn', function()
    local runtime=runtime_module.new(logic,env)
    for _,key in ipairs({'wh3_main_cth_lord_caravan_master','wh3_cp1_cth_sawai_caravan',
        'wh3_dlc23_chd_lord_convoy_overseer','other_mod_caravan_general'}) do
        runtime.subtypes[key]='general'
        local before=calls
        assert(not runtime.supported(key) and calls==before)
        local candidate,why=runtime.spawn_candidate('empire',key,{male=true})
        assert(candidate==nil and why==(policy_module.caravan(key) and 'caravan_identity_is_preserved' or 'unsupported_subtype') and calls==before)
        assert(not logic.eligible({faction='empire',subtype=key,in_pool=true,provenance='ordinary_generated'},'empire',key))
    end
end)
test('discovered_types_do_not_leak_between_campaign_instances', function()
    assert(not runtime_module.new(logic, env).subtypes.test_fire_wizard)
end)
test('multiplayer_metadata_uses_request_faction_and_bypasses_ui_cache', function()
    local mp_env = {out = env.out, cm = {is_multiplayer = function() return true end,
        get_local_faction_name = function() return 'observer' end,
        get_faction = function(_, key)
            assert(key == 'remote_player', 'Local UI faction leaked into preflight')
            return faction
        end}, common = env.common}
    local runtime = runtime_module.new(logic, mp_env)
    runtime.subtypes.test_fire_wizard = 'general'
    agent = 'wizard'; local before = calls
    assert(runtime.supported('test_fire_wizard', 'remote_player'))
    assert(calls == before + 2 and runtime.subtypes.test_fire_wizard == 'wizard')
    generated = false
    assert(not runtime.supported('test_fire_wizard', 'remote_player'))
    generated = true
end)
test('startup_observations_survive_unavailable_pool_metadata_without_losing_protections', function()
    local ready, metadata_calls, saved = false, 0, nil
    local owner = {is_null_interface = function() return false end, is_human = function() return true end,
        name = function() return 'empire' end, command_queue_index = function() return 12 end}
    local null = {is_null_interface = function() return true end}
    local details = {}
    for id = 101, 106 do
        local cqi = id
        details[id] = {is_null_interface = function() return false end,
            faction = function() return owner end, character_subtype_key = function() return 'test_startup_wizard' end,
            family_member = function() return {command_queue_index = function() return cqi end} end,
            start_pos_key = function() return cqi == 102 and 'startpos_character' or '' end,
            character = function() return null end,
            is_unique = function() return cqi == 103 end, is_immortal = function() return cqi == 104 end}
    end
    local startup_env = {out = env.out, common = {get_context_value = function(kind)
        metadata_calls = metadata_calls + 1
        if not ready then error('Pool not queryable before first tick') end
        return kind == 'CcoAgentSubtypeRecord' and true or 'wizard'
    end}, cm = {
        get_faction = function() return owner end, get_local_faction_name = function() return 'empire' end,
        get_family_member_by_cqi = function(_, id)
            return {character_details = function() return details[id] end}
        end,
        get_saved_value = function() return saved end, set_saved_value = function(_, _, value) saved = value end}}
    package.loaded['script.campaign.xatw3_campaign_utilities.native_pool'] = {new = function()
        return {initialize = function() return true end}
    end}
    local runtime = runtime_module.new(logic, startup_env)
    for id = 101, 106 do runtime.observe_entry(details[id]) end
    runtime.mark_recruited(105)
    assert(#runtime.pending_entries == 6 and metadata_calls == 0)
    ready = true
    runtime.initialize()
    assert(runtime.initialized and runtime.refresh_verified and #runtime.pending_entries == 0)
    assert(runtime.state.history['101'].provenance == 'ordinary_generated')
    for _, id in ipairs({102, 103, 104}) do assert(runtime.state.history[tostring(id)].provenance == 'unknown') end
    assert(runtime.state.history['105'].recruited)
    local existing = runtime.state.history['106']
    runtime.mark_recruited(106); runtime.observe_entry(details[106])
    assert(runtime.state.history['106'] == existing and existing.recruited)
    -- Loading an old save does not invent provenance for unobserved characters.
    local reloaded = runtime_module.new(logic, startup_env); reloaded.initialize()
    assert(reloaded.state.history['999'] == nil and reloaded.state.history['105'].recruited)
end)
test('finite_candidate_discovery_requires_a_live_pool_and_never_fixed_identity',function()
    generated=false;agent='general'
    local runtime=runtime_module.new(logic,env)
    assert(runtime.supported('wh2_main_lzd_slann_mage_priest'))
    assert(runtime.supported('wh2_dlc11_vmp_bloodline_blood_dragon'))
    assert(not runtime.supported('wh2_dlc09_tmb_tomb_king_alkhazzar_ii'))
    agent=nil;assert(not runtime.supported('wh2_main_lzd_slann_mage_priest'))
    generated=true;agent='wizard'
end)
test('finite_generation_copies_training_points_and_reports_created_but_unreadable',function()
    local added={};local spawned={is_null_interface=function() return false end,
        family_member=function() return {command_queue_index=function() return 501 end} end}
    local fixture={out=function() end,cm={spawn_character_to_pool=function() return spawned end,
        force_add_trait_to_character_details=function(_,details,key)
            assert(details==spawned);added[#added+1]=key
        end}}
    local runtime=runtime_module.new(logic,fixture);runtime.state={history={}}
    runtime.supported=function() return true end;runtime.persist=function() end
    runtime.describe=function() return nil end
    local c,why,id=runtime.spawn_candidate('kislev','wh2_main_lzd_slann_mage_priest',
        {male=false,traits={{key='training_one',points=1},{key='training_two',points=2}}})
    assert(c==nil and why=='spawn_readback_failed' and id==501)
    assert(#added==3 and added[1]=='training_one' and added[2]=='training_two' and added[3]=='training_two')
    assert(runtime.state.history['501'].provenance=='ordinary_generated')
end)
test('special_entry_and_recruit_events_never_query_transient_candidate_lists',function()
    local owner={is_null_interface=function() return false end,is_human=function() return true end,name=function() return 'cathay' end}
    local null={is_null_interface=function() return true end}
    local env={out=function() end,cm={model=function() error('must not inspect transient pool') end},
        common={get_context_value=function() error('must not query recruitment during lifecycle event') end}}
    local runtime=runtime_module.new(logic,env);runtime.state={history={}};runtime.initialized=true;runtime.persist=function() end
    local id=700
    for _,key in ipairs({'wh3_main_cth_lord_caravan_master','wh2_main_lzd_slann_mage_priest'}) do
        id=id+1;local cqi=id
        local fm={command_queue_index=function() return cqi end}
        local details={is_null_interface=function() return false end,faction=function() return owner end,
            character_subtype_key=function() return key end,character_type_key=function() return 'general' end,
            family_member=function() return fm end,start_pos_key=function() return '' end,character=function() return null end,
            is_unique=function() return false end,is_immortal=function() return false end}
        runtime.observe_entry(details);assert(runtime.state.history[tostring(cqi)].provenance=='ordinary_generated')
        local actor={is_null_interface=function() return false end,faction=function() return owner end,family_member=function() return fm end}
        runtime.observe_recruited(actor);assert(runtime.state.history[tostring(cqi)].recruited)
    end
end)
test('approved_caravans_never_use_generic_character_spawn',function()
    local runtime=runtime_module.new(logic,env)
    for _,key in ipairs({'wh3_main_cth_lord_caravan_master','wh3_dlc23_chd_lord_convoy_overseer','wh3_cp1_cth_sawai_caravan'}) do
        local candidate,reason=runtime.spawn_candidate('cathay',key,{male=true})
        assert(candidate==nil and reason=='caravan_identity_is_preserved')
    end
end)
package.loaded['script.campaign.xatw3_campaign_utilities.native_pool'] = original
return passed
