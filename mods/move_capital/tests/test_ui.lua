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
test('native_button_label_stays_inside_reused_button', function()
    local function c(id,x,y,w,h)
        local t={id=id,x=x or 0,y=y or 0,w=w or 0,h=h or 0,children={},visible=true}
        function t:Visible() return self.visible end
        function t:SetVisible(v) self.visible=v end
        function t:Position() return self.x,self.y end
        function t:Dimensions() return self.w,self.h end
        function t:SetStateText(v) self.text=v end
        function t:SetTooltipText(v) self.tooltip=v end
        function t:SetInteractive(v) self.interactive=v end
        function t:SetCanResizeWidth() end
        function t:SetCanResizeHeight() end
        function t:SetDockingPoint(v) self.dock=v end
        function t:SetDockOffset(x,y) self.dx,self.dy=x,y end
        function t:Resize(w,h) self.w,self.h=w,h end
        function t:MoveTo(x,y) self.x,self.y=x,y end
        function t:SetTextHAlign(v) self.halign=v end
        function t:SetTextVAlign(v) self.valign=v end
        function t:SetTextXOffset(x,y) self.tx,self.tx2=x,y end
        function t:SetTextYOffset(x,y) self.ty,self.ty2=x,y end
        return t
    end
    local root,panel,anchor,b,label,flame=c('root'),c('settlement_panel'),c('button_rename',640,780),c('xatw3mc_move_capital'),c('button_txt'),c('button_flame')
    root.children.settlement_panel=panel;panel.children.button_rename=anchor;b.children.button_txt=label;b.children.button_flame=flame
    local rt={initialized=true,state={locked=false},can_act=function() return true end,capital=function() return 'old' end,region=function() return {key='new',exists=true,settlement=true,owner='player'} end}
    local ui=ui_module.new(rt,logic,{core={get_ui_root=function() return root end,get_or_create_component=function() return b end},cm={get_local_faction_name=function() return 'player' end},common={get_localised_string=function(k) return k end},find_uicomponent=function(p,id) return p.children[id] end})
    ui.selected_region='new';ui.refresh_buttons()
    assert(b.visible and b.interactive and b.text==nil and label.text=='xatw3mc_capital' and not flame.visible)
    assert(b.x==640 and b.y==735 and b.w==170 and b.h==34)
    assert(label.x>=b.x and label.y>=b.y and label.x+label.w<=b.x+b.w and label.y+label.h<=b.y+b.h)
    assert(label.halign=='centre' and label.valign=='centre' and label.dock==0 and label.dx==0 and label.dy==0)
    anchor.x=900;anchor.y=850;ui.refresh_buttons();assert(b.x==900 and b.y==805 and label.x>=900 and label.y>=805)
    b.children.button_txt=nil;ui.refresh_buttons();assert(not b.visible)
end)
return passed
