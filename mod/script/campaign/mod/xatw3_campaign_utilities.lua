local logic = require('script.campaign.xatw3_campaign_utilities.logic')
local runtime = require('script.campaign.xatw3_campaign_utilities.runtime').new(logic)
local ui = require('script.campaign.xatw3_campaign_utilities.ui').new(runtime, logic)

-- This namespace is also the explicit entry point used by the separate acceptance fixture.
xatw3_campaign_utilities = {logic = logic, runtime = runtime, ui = ui, version = '0.1.0'}

core:add_listener('xatw3_pool_entries', 'ScriptEventNewCharacterEnteredRecruitmentPool', true,
    function(context) runtime.observe_entry(context:character_details()) end, true)

core:add_listener('xatw3_recruited', 'CharacterRecruited', true, function(context)
    local character = context:character()
    if character:faction():is_human() and runtime.supported(character:character_subtype_key()) then
        runtime.mark_recruited(character:family_member():command_queue_index())
    end
end, true)

core:add_listener('xatw3_created', 'CharacterCreated', true, function(context)
    local character = context:character()
    if character:faction():is_human() and runtime.supported(character:character_subtype_key()) then
        runtime.mark_recruited(character:family_member():command_queue_index())
    end
end, true)

core:add_listener('xatw3_requests', 'UITrigger', function(context)
    return type(context:trigger()) == 'string' and context:trigger():sub(1, 7) == 'xatw3|1'
end, function(context)
    if #context:trigger() > 4096 then return end
    local parts = {}
    for part in (context:trigger() .. '|'):gmatch('(.-)|') do parts[#parts + 1] = part end
    if #parts ~= 7 then return end
    if context:faction_cqi() ~= cm:get_local_faction():command_queue_index() then return end
    runtime.execute({version = tonumber(parts[2]), action = parts[3], sequence = tonumber(parts[4]),
        turn = tonumber(parts[5]), target = parts[6], expected = parts[7], faction = cm:get_local_faction_name()})
end, true)

cm:add_first_tick_callback(function()
    runtime.initialize()
    if cm:get_campaign_name() == 'wh3_main_combi' and not cm:is_multiplayer() then ui.install() end
    runtime.log('loaded version=0.1.0 campaign=' .. cm:get_campaign_name())
end)
