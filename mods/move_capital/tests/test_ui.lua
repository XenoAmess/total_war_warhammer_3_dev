local passed = {}
local function test(name, fn) fn(); passed[#passed + 1] = name end
local function fixture()
    local listeners, dispatched = {}, {}
    local function component(id, parent)
        local c = {id = id, parent = parent, visible = true, children = {}}
        function c:Id() return self.id end
        function c:Parent() return self.parent end
        function c:Visible() return self.visible end
        function c:SetVisible(v) self.visible = v end
        function c:SetStateText(v) self.text = v end
        function c:PropagatePriority() end
        return c
    end
    local root = component('root')
    local dialog = component('xatw3mc_confirm_action', root)
    for _, id in ipairs({'DY_text', 'purchase_options', 'both_group', 'ok_group'}) do
        dialog.children[id] = component(id, dialog)
    end
    local runtime = {initialized = true, state = {locked = false, next_sequence = 1},
        can_act = function() return true end, turn = function() return 3 end,
        capital = function() return 'old_home' end,
        region = function(key) return {key = key, exists = true, settlement = true, owner = 'player'} end}
    local env = {
        core = {get_ui_root = function() return root end,
            get_or_create_component = function() return dialog end,
            add_listener = function(_, name, event, condition, callback)
                listeners[name] = {event = event, condition = condition, callback = callback}
            end},
        cm = {callback = function(_, fn) fn() end, get_local_faction_name = function() return 'player' end,
            get_local_faction = function() return {command_queue_index = function() return 17 end} end},
        common = {get_localised_string = function(key) return key end},
        find_uicomponent = function(parent, id) return parent.children[id] or false end,
        UIComponent = function(c) return c end,
        CampaignUI = {TriggerCampaignScriptEvent = function(cqi, payload)
            dispatched[#dispatched + 1] = {cqi = cqi, payload = payload}
        end}
    }
    local ui = ui_module.new(runtime, logic, env); ui.install()
    local function emit(event, context)
        for _, listener in pairs(listeners) do
            if listener.event == event and (listener.condition == true or listener.condition(context)) then listener.callback(context) end
        end
    end
    local function click(id) emit('ComponentLClickUp', {string = id, component = component(id, dialog)}) end
    return ui, runtime, dispatched, emit, click
end
local function request() return {action = 'capital', sequence = 1, turn = 3, target = 'new_home', expected = 'old_home'} end

test('cancel_never_dispatches', function()
    local ui, _, sent, _, click = fixture(); ui.confirm(request(), 'confirm'); click('button_cancel')
    assert(#sent == 0 and ui.pending == nil and not ui.dialog.visible)
end)
test('confirm_uses_new_channel_once_and_frozen_target', function()
    local ui, rt, sent, _, click = fixture(); ui.confirm(request(), 'confirm'); ui.selected_region = 'different'
    click('button_tick'); click('button_tick')
    assert(#sent == 1 and sent[1].cqi == 17 and sent[1].payload == 'xatw3mc|1|capital|1|3|new_home|old_home')
    rt.on_result({status = 'SUCCEEDED'}); click('button_tick')
    assert(#sent == 1 and not ui.submitting and ui.pending == nil)
end)
test('settlement_selection_updates_target', function()
    local ui, _, _, emit = fixture()
    emit('SettlementSelected', {garrison_residence = function() return {region = function()
        return {name = function() return 'new_home' end}
    end} end})
    assert(ui.selected_region == 'new_home')
    ui.prepare('capital'); assert(ui.pending and ui.pending.target == 'new_home')
end)
return passed
