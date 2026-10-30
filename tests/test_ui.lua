-- Exercise the production UI controller through its registered events.
local passed, listeners, dispatched = {}, {}, {}
local function component(id, parent, subtype)
    local c = {id = id, parent = parent, subtype = subtype, visible = true, children = {}}
    function c:Id() return self.id end
    function c:Parent() return self.parent end
    function c:Visible() return self.visible end
    function c:SetVisible(value) self.visible = value end
    function c:SetStateText(value) self.text = value end
    function c:PropagatePriority() end
    function c:GetContextObjectId(kind)
        return kind == 'CcoAgentSubtypeRecord' and self.subtype or ''
    end
    return c
end
local root = component('root')
local dialog = component('xatw3_confirm_action', root)
for _, id in ipairs({'DY_text', 'purchase_options', 'both_group', 'ok_group'}) do
    dialog.children[id] = component(id, dialog)
end
UIComponent = function(c) return c end
find_uicomponent = function(parent, id) return parent.children[id] or false end
common = {
    get_localised_string = function(key) return key end,
    get_context_value = function(_, id) return id end
}
cm = {
    callback = function(_, fn) fn() end,
    get_local_faction_name = function() return 'test_faction' end,
    get_local_faction = function() return {command_queue_index = function() return 17 end} end
}
core = {
    get_ui_root = function() return root end,
    get_or_create_component = function() return dialog end,
    add_listener = function(_, name, event, condition, callback)
        listeners[name] = {event = event, condition = condition, callback = callback}
    end
}
CampaignUI = {TriggerCampaignScriptEvent = function(cqi, payload)
    dispatched[#dispatched + 1] = {cqi, payload}
end}
local runtime = {initialized = true, state = {locked = false}, can_act = function() return true end}
runtime.supported = function(key) return key == 'supported' end
local ui = ui_module.new(runtime, {})
ui.install()
local function emit(event, context)
    for _, listener in pairs(listeners) do
        if listener.event == event and (listener.condition == true or listener.condition(context)) then
            listener.callback(context)
        end
    end
end
local function click(c)
    emit('ComponentLClickUp', {string = c.id, component = c})
end
local function test(name, fn) fn(); passed[#passed + 1] = name end
test('candidate_click_selects_its_subtype', function()
    click(component('candidate', root, 'supported'))
    assert(ui.selected_subtype == 'supported')
end)
test('category_switch_clears_previous_refresh_target', function()
    click(component('type_button', root))
    assert(ui.selected_subtype == nil)
end)
test('opening_and_closing_recruitment_clear_selection', function()
    for _, event in ipairs({'PanelClosedCampaign', 'PanelOpenedCampaign'}) do
        ui.selected_subtype = 'supported'
        emit(event, {string = 'character_panel'})
        assert(ui.selected_subtype == nil)
    end
end)
local request = {action = 'refresh', sequence = 8, turn = 3, target = 'supported', expected = 'snapshot'}
test('cancel_confirmation_never_dispatches', function()
    ui.confirm(request, 'confirm')
    click(component('button_cancel', dialog))
    assert(#dispatched == 0 and ui.pending == nil and not dialog.visible)
end)
test('confirm_dispatches_frozen_request_once', function()
    ui.confirm(request, 'confirm')
    ui.selected_subtype = 'different'
    click(component('button_tick', dialog))
    click(component('button_tick', dialog))
    assert(#dispatched == 1 and dispatched[1][1] == 17)
    assert(dispatched[1][2] == 'xatw3|1|refresh|8|3|supported|snapshot')
end)
test('result_dialog_cannot_replay_previous_request', function()
    runtime.on_result({status = 'SUCCEEDED'})
    click(component('button_tick', dialog))
    assert(#dispatched == 1 and ui.pending == nil)
end)
return passed
