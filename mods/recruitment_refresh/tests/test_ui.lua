-- Registered events with queued callbacks: closing native cards is asynchronous.
local passed = {}
local function component(id, parent, subtype)
    local c = {id=id, parent=parent, subtype=subtype, visible=true, children={}, state='active'}
    function c:Id() return self.id end
    function c:Parent() return self.parent end
    function c:Visible() return self.visible end
    function c:SetVisible(v) self.visible=v end
    function c:SetStateText(v) self.text=v end
    function c:SetTooltipText(v) self.tooltip=v end
    function c:SetInteractive(v) self.interactive=v end
    function c:PropagatePriority() end
    function c:CurrentState() return self.state end
    function c:GetContextObject(kind)
        if kind=='CcoAgentSubtypeRecord' and self.subtype then
            return {Call=function() return self.subtype end}
        end
    end
    if parent then parent.children[id]=c end
    return c
end
local function find(parent, ...)
    for _,id in ipairs({...}) do
        local function descend(node)
            if not node then return false end
            if node.children[id] then return node.children[id] end
            for _,child in pairs(node.children) do
                local found=descend(child); if found then return found end
            end
            return false
        end
        parent=descend(parent); if not parent then return false end
    end
    return parent
end
local function fixture()
    local f={queue={}, listeners={}, dispatched={}, closed=0, dialogs=0,
        allowed=true, pool={}, replace_count=1, fingerprint='snapshot', turn=3}
    f.root=component('root')
    f.panel=component('character_panel') -- Attached only when the test opens recruitment.
    f.dialog=component('xatw3_confirm_action',f.root); f.dialog.visible=false
    for _,id in ipairs({'DY_text','purchase_options','both_group','ok_group'}) do component(id,f.dialog) end
    local hud=component('hud_center_docker',component('hud_campaign',f.root))
    for _,id in ipairs({'button_create_army','button_agents'}) do
        local b=component(id,hud)
        function b:SimulateLClick()
            f.reopened=self.id; f.root.children.character_panel=f.panel; f.panel.visible=true
        end
    end
    local tab=component('supported',component('lords_and_agents_holder',f.panel))
    function tab:SimulateLClick() self.state='selected'; f.tab_clicked=true end
    f.runtime={initialized=true,state={locked=false,next_sequence=8},refresh_verified=true,subtypes={supported='general'}}
    f.runtime.supported=function(key) return key=='supported' end
    f.runtime.can_act=function() return f.allowed end
    f.runtime.turn=function() return f.turn end
    f.runtime.read_pool=function() return f.pool end
    local environment={UIComponent=function(c) return c end,find_uicomponent=find,
        common={get_localised_string=function(key) return key end},
        cm={callback=function(_,fn) f.queue[#f.queue+1]=fn end,
            get_local_faction_name=function() return 'test_faction' end,
            get_local_faction=function() return {command_queue_index=function() return 17 end} end},
        core={get_ui_root=function() return f.root end,
            get_or_create_component=function(_,id,_,parent)
                if id==f.dialog.id then f.dialogs=f.dialogs+1; return f.dialog end
                return parent.children[id] or component(id,parent)
            end,
            add_listener=function(_,name,event,condition,callback)
                f.listeners[name]={event=event,condition=condition,callback=callback}
            end},
        CampaignUI={ClosePanel=function(name) assert(name=='character_panel'); f.closed=f.closed+1 end,
            CloseCurrentHUDPanel=function() end,
            TriggerCampaignScriptEvent=function(cqi,payload)
                assert(not f.panel.visible,'Native cards must close before dispatch')
                f.dispatched[#f.dispatched+1]={cqi,payload}
            end}}
    local logic_mock={plan=function() return {replace=f.replace_count>0 and {1} or {},
        add=f.add_count or 0,fingerprint=f.fingerprint} end}
    f.ui=ui_module.new(f.runtime,logic_mock,environment)
    function f.emit(event,context)
        for _,listener in pairs(f.listeners) do
            if listener.event==event and (listener.condition==true or listener.condition(context)) then listener.callback(context) end
        end
    end
    function f.click(c) f.emit('ComponentLClickUp',{string=c.id,component=c}) end
    function f.step() assert(#f.queue>0); table.remove(f.queue,1)() end
    function f.drain()
        local n=0
        while #f.queue>0 do n=n+1; assert(n<100); f.step() end
    end
    function f.start()
        f.root.children.character_panel=f.panel; f.panel.visible=true; f.ui.selected_subtype='supported'
        f.click(component('xatw3_refresh_candidates'))
    end
    f.ui.install()
    return f
end
local function test(name,fn) fn(fixture()); passed[#passed+1]=name end
test('candidate_selection_and_category_switch',function(f)
    f.click(component('candidate',nil,'supported')); assert(f.ui.selected_subtype=='supported')
    f.click(component('type_button')); assert(f.ui.selected_subtype==nil)
end)
test('panel_events_clear_previous_target',function(f)
    for _,event in ipairs({'PanelClosedCampaign','PanelOpenedCampaign'}) do
        f.ui.selected_subtype='supported'; f.emit(event,{string='character_panel'}); assert(f.ui.selected_subtype==nil)
    end
end)
test('single_click_closes_without_confirmation_and_dispatches_once',function(f)
    f.start(); assert(f.closed==1 and f.dialogs==0 and #f.dispatched==0 and f.ui.submitting)
    f.click(component('xatw3_refresh_candidates')); assert(f.closed==1)
    f.panel.visible=false; f.drain()
    assert(#f.dispatched==1 and f.dispatched[1][1]==17)
    assert(f.dispatched[1][2]=='xatw3|1|refresh|8|3|supported|snapshot')
    f.click(component('xatw3_refresh_candidates')); assert(#f.dispatched==1)
end)
test('delayed_close_uses_frozen_request',function(f)
    f.start(); f.step(); f.step(); assert(#f.dispatched==0)
    f.ui.selected_subtype,f.turn,f.runtime.state.next_sequence,f.fingerprint='other',99,99,'changed'
    f.panel.visible=false; f.drain()
    assert(#f.dispatched==1 and f.dispatched[1][2]=='xatw3|1|refresh|8|3|supported|snapshot')
end)
test('closure_timeout_never_dispatches_or_replays',function(f)
    f.start(); f.drain()
    assert(#f.dispatched==0 and not f.ui.submitting and f.ui.reopen==nil)
    assert(f.dialog.visible and f.dialogs==1)
    f.click(component('button_tick',f.dialog)); f.click(component('button_tick',f.dialog))
    assert(#f.dispatched==0 and not f.dialog.visible)
end)
test('success_reopens_lord_tab_without_modal',function(f)
    f.start(); f.panel.visible=false; f.drain(); f.runtime.on_result({status='SUCCEEDED'}); f.drain()
    assert(f.reopened=='button_create_army' and f.tab_clicked)
    assert(f.ui.selected_subtype=='supported' and f.dialogs==0 and not f.ui.submitting)
end)
test('success_reopens_hero_panel_without_modal',function(f)
    f.runtime.subtypes.supported='champion'
    f.start(); f.panel.visible=false; f.drain(); f.runtime.on_result({status='SUCCEEDED'}); f.drain()
    assert(f.reopened=='button_agents' and f.dialogs==0)
end)
test('rejected_result_reopens_then_shows_dismiss_only_error',function(f)
    f.start(); f.panel.visible=false; f.drain(); f.runtime.on_result({status='REJECTED',reason='stale'}); f.drain()
    assert(f.reopened and f.dialog.visible and f.dialog.children.DY_text.text=='xatw3_error\n\nxatw3_stale')
    assert(not f.dialog.children.both_group.visible and f.dialog.children.ok_group.visible)
    f.click(component('button_tick',f.dialog)); f.drain(); assert(#f.dispatched==1 and not f.dialog.visible)
end)
test('uncertain_result_keeps_error_and_does_not_reopen',function(f)
    f.start(); f.panel.visible=false; f.drain(); f.runtime.on_result({status='PARTIAL'}); f.drain()
    assert(f.reopened==nil and f.dialog.visible and f.dialog.children.DY_text.text=='xatw3_error\n\nxatw3_uncertain')
    f.click(component('button_cancel',f.dialog)); assert(#f.dispatched==1)
end)

test('native_layout_rejection_explains_compatibility_without_replaying',function(f)
    f.start();f.panel.visible=false;f.drain()
    f.runtime.on_result({status='REJECTED',reason='native_pool_unavailable'});f.drain()
    assert(f.dialog.children.DY_text.text=='xatw3_error\n\nxatw3_native_pool_unavailable')
    f.click(component('button_tick',f.dialog));assert(#f.dispatched==1)
end)
test('small_protected_pool_can_submit_additions_without_confirmation',function()
    local f=fixture();f.replace_count=0;f.add_count=2
    f.start();f.panel.visible=false;f.drain()
    assert(f.closed==1 and #f.dispatched==1 and f.dialogs==0)
end)

test('unsafe_actions_and_unavailable_pool_do_not_close_panel',function()
    for _,reason in ipairs({'locked','disallowed','unverified','pool','empty','unsupported'}) do
        local f=fixture()
        if reason=='locked' then f.runtime.state.locked=true
        elseif reason=='disallowed' then f.allowed=false
        elseif reason=='unverified' then f.runtime.refresh_verified=false
        elseif reason=='pool' then f.pool=nil
        elseif reason=='empty' then f.replace_count=0
        else f.runtime.supported=function() return false end end
        f.start(); f.drain(); assert(f.closed==0 and #f.dispatched==0)
        assert(f.dialogs==((reason=='unverified' or reason=='pool' or reason=='empty') and 1 or 0))
    end
end)
return passed
