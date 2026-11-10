local logic = require('script.campaign.xatw3_move_capital.logic')
local environment = getfenv(1)
local runtime = require('script.campaign.xatw3_move_capital.runtime').new(logic, environment)
local ui = require('script.campaign.xatw3_move_capital.ui').new(runtime, logic, environment)

xatw3_move_capital = {logic = logic, runtime = runtime, ui = ui, version = '0.2.0'}

core:add_listener('xatw3mc_requests', 'UITrigger', function(context)
    return type(context:trigger()) == 'string' and context:trigger():sub(1, 9) == 'xatw3mc|1'
end, function(context)
    if cm:is_multiplayer() then return end -- MP uses the shared, voted channel
    if #context:trigger() > 4096 then return end
    local parts = {}
    for part in (context:trigger() .. '|'):gmatch('(.-)|') do parts[#parts + 1] = part end
    if #parts ~= 7 or parts[3] ~= 'capital' then return end
    if context:faction_cqi() ~= cm:get_local_faction():command_queue_index() then return end
    runtime.execute({version = tonumber(parts[2]), action = parts[3], sequence = tonumber(parts[4]),
        turn = tonumber(parts[5]), target = parts[6], expected = parts[7], faction = cm:get_local_faction_name()})
end, true)

cm:add_first_tick_callback(function()
    runtime.initialize()
    if cm:is_multiplayer() then runtime.install_multiplayer() end
    if runtime.campaign_supported() then ui.install() end
    runtime.log('loaded version=0.2.0 campaign=' .. cm:get_campaign_name())
end)
