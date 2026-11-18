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
    function c:ChildCount() local n=0;for _ in pairs(self.children) do n=n+1 end;return n end
    function c:Find(index)
        local keys={};for key in pairs(self.children) do keys[#keys+1]=key end;table.sort(keys)
        return self.children[keys[index+1]]
    end
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
    f.environment=environment
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
    assert(f.dispatched[1][2]=='xatw3|1|refresh|8|3|supported|sp1')
    f.click(component('xatw3_refresh_candidates')); assert(#f.dispatched==1)
end)
test('delayed_close_uses_frozen_request',function(f)
    f.start(); f.step(); f.step(); assert(#f.dispatched==0)
    f.ui.selected_subtype,f.turn,f.runtime.state.next_sequence,f.fingerprint='other',99,99,'changed'
    f.panel.visible=false; f.drain()
    assert(#f.dispatched==1 and f.dispatched[1][2]=='xatw3|1|refresh|8|3|supported|sp1')
    local request=f.ui.consume_request({version=1,action='refresh',sequence=8,turn=3,
        target='supported',faction='test_faction'},'sp1')
    assert(request and request.expected=='snapshot')
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
test('success_restores_shared_agent_lore_after_native_rebuild',function(f)
    f.runtime.subtypes.supported='spy'
    local categories=f.panel.children.lords_and_agents_holder
    categories.children.supported=nil
    local agent=component('spy',categories)
    function agent:SimulateLClick()
        self.state='selected'
        f.queue[#f.queue+1]=function()
            local selection=component('general_selection_panel',f.panel)
            local holder=component('main_holder',selection)
            local lores=component('lore_select_parent',holder)
            local types=component('type_list',component('wizard_type',lores))
            local lore=component('supported',types)
            function lore:SimulateLClick()
                self.state='selected_hover';f.lore_clicked=true
                f.queue[#f.queue+1]=function() f.lore_native_ready=true end
            end
        end
    end
    f.start();f.panel.visible=false;f.drain()
    f.ui.refresh_buttons=function() assert(f.lore_native_ready,'Read cards before restoring the native lore') end
    f.runtime.on_result({status='SUCCEEDED'});f.drain()
    assert(f.reopened=='button_agents' and f.lore_clicked and f.dialogs==0)
end)
test('missing_or_hidden_lore_does_not_force_remembered_subtype',function()
    for _,hidden in ipairs({false,true}) do
        local f=fixture();f.runtime.subtypes.supported='spy'
        local clicked=false
        if hidden then
            local selection=component('general_selection_panel',f.panel);selection.visible=false
            local holder=component('main_holder',selection)
            local lores=component('lore_select_parent',holder)
            local types=component('type_list',component('wizard_type',lores))
            local lore=component('supported',types)
            function lore:SimulateLClick() clicked=true end
        end
        f.start();f.panel.visible=false;f.drain()
        f.ui.refresh_buttons=function() assert(f.ui.selected_subtype==nil) end
        f.runtime.on_result({status='SUCCEEDED'});f.drain()
        assert(not clicked and f.dialogs==0)
    end
end)
test('lord_lore_key_is_preserved_across_native_category_rebuild',function(f)
    local categories=f.panel.children.lords_and_agents_holder;categories.children.supported=nil
    local list=component('list_box',component('lord_parent',categories))
    local category=component('native_lord_category',list);category.state='selected'
    local function make_lores(selected)
        local holder=component('main_holder',component('general_selection_panel',f.panel))
        local lores=component('lore_type_list',component('lord_magic_lore_type',component('lore_select_parent',holder)))
        local fire=component('wh_main_lore_fire',lores);local death=component('wh_main_lore_death',lores)
        fire.state=selected=='fire' and 'selected' or 'active';death.state=selected=='death' and 'selected_hover' or 'active'
        function death:SimulateLClick()self.state='selected';fire.state='active';f.lore_restored=true end
    end
    make_lores('death')
    function category:SimulateLClick()
        self.state='selected';f.queue[#f.queue+1]=function()make_lores('fire')end
    end
    local opener=f.root.children.hud_campaign.children.hud_center_docker.children.button_create_army
    function opener:SimulateLClick()f.reopened=self.id;f.panel.visible=true;category.state='active' end
    f.start();assert(f.ui.reopen.lore.key=='wh_main_lore_death' and f.ui.reopen.subtype=='supported')
    f.panel.visible=false;f.drain();f.ui.refresh_buttons=function()assert(f.lore_restored)end
    f.runtime.on_result({status='SUCCEEDED'});f.drain()
    assert(f.reopened=='button_create_army' and f.lore_restored and #f.dispatched==1)
end)
test('unavailable_lord_lore_does_not_click_another_visible_lore',function(f)
    local holder=component('main_holder',component('general_selection_panel',f.panel))
    local lores=component('lore_type_list',component('lord_magic_lore_type',component('lore_select_parent',holder)))
    local death=component('wh_main_lore_death',lores);death.state='selected'
    local fire=component('wh_main_lore_fire',lores);function fire:SimulateLClick()error('Wrong lore clicked')end
    f.start();f.panel.visible=false;f.drain();lores.children.wh_main_lore_death=nil
    f.ui.refresh_buttons=function()assert(f.ui.selected_subtype==nil)end
    f.runtime.on_result({status='SUCCEEDED'});f.drain();assert(#f.dispatched==1)
end)
test('reopen_preserves_native_category_alias_instead_of_inferring_from_subtype',function()
    for _,state in ipairs({'selected','selected_hover'}) do
        local f=fixture();local categories=f.panel.children.lords_and_agents_holder
        categories.children.supported=nil
        local page=component('lord_parent',categories);local list=component('list_box',page)
        local legendary=component('legendary_lords',list);local alias=component('native_alias',list);alias.state=state
        local clicked=false
        function alias:SimulateLClick() self.state='selected_hover';legendary.state='active';clicked=true end
        local hud=f.root.children.hud_campaign.children.hud_center_docker.children.button_create_army
        function hud:SimulateLClick()
            f.reopened=self.id;f.root.children.character_panel=f.panel;f.panel.visible=true
            alias.state='active';legendary.state='selected'
        end
        f.start();f.panel.visible=false;f.drain()
        f.ui.refresh_buttons=function() assert(clicked,'Native category alias was not restored') end
        f.runtime.on_result({status='SUCCEEDED'});f.drain()
        assert(clicked and f.reopened=='button_create_army')
    end
end)
test('category_capture_uses_visible_page_and_never_changes_wire_request',function()
    local f=fixture();f.runtime.subtypes.supported='spy'
    local categories=f.panel.children.lords_and_agents_holder;categories.children.supported=nil
    local lords=component('lord_parent',categories);lords.visible=false
    local stale=component('hidden_lord',component('list_box',lords));stale.state='selected'
    local agents=component('agent_parent',categories)
    local current=component('native_agent_alias',component('list_box',agents));current.state='selected_hover'
    f.start();assert(f.ui.reopen.category=='native_agent_alias')
    f.panel.visible=false;f.drain()
    assert(f.dispatched[1][2]=='xatw3|1|refresh|8|3|supported|sp1')
end)
test('rejected_result_reopens_then_shows_dismiss_only_error',function(f)
    f.start(); f.panel.visible=false; f.drain(); f.runtime.on_result({status='REJECTED',reason='stale'}); f.drain()
    assert(f.reopened and f.dialog.visible and f.dialog.children.DY_text.text=='xatw3_error\n\nxatw3_stale')
    assert(not f.dialog.children.both_group.visible and f.dialog.children.ok_group.visible)
    f.click(component('button_tick',f.dialog)); f.drain(); assert(#f.dispatched==1 and not f.dialog.visible)
end)

test('caravan_refresh_waits_for_both_panels_and_reopens_through_caravan_purchase',function(f)
    local key='wh3_main_cth_lord_caravan_master'
    f.runtime.subtypes={[key]='general'};f.runtime.supported=function(k) return k==key end
    local category=f.panel.children.lords_and_agents_holder;category.children.supported=nil
    local alias=component('caravan_master',component('list_box',component('lord_parent',category)))
    alias.state='selected'
    local card_list=component('list_box',component('list_clip',component('listview',component('character_list',f.panel))))
    local card=component('general_candidate_0_',card_list);local select=component('button_wh3',card)
    function select:GetContextObject() return {Call=function() return key end} end
    local caravan=component('cathay_caravans',f.root)
    local purchase=component('button_purchase',component('add_caravan_button',component('reserves_listview',component('caravans_panel',caravan))))
    function purchase:SimulateLClick() f.purchase_opened=true;f.panel.visible=true end
    local hud=component('button_caravan',component('faction_buttons_docker',f.root.children.hud_campaign))
    function hud:SimulateLClick() f.caravan_opened=true;caravan.visible=true end
    f.closed_panels={}
    f.environment.CampaignUI.ClosePanel=function(name) f.closed_panels[name]=true end
    f.root.children.character_panel=f.panel;f.ui.selected_subtype=key
    f.click(component('xatw3_refresh_candidates'));assert(f.closed_panels.character_panel and f.closed_panels.cathay_caravans)
    f.panel.visible=false;f.step();assert(#f.dispatched==0,'Dispatched while special panel still held contexts')
    caravan.visible=false;f.drain();assert(#f.dispatched==1)
    f.runtime.on_result({status='SUCCEEDED'});f.drain()
    assert(f.caravan_opened and f.purchase_opened and f.ui.selected_subtype==key)
end)
test('convoy_master_list_closes_before_dispatch_and_reopens_without_ordinary_recruitment',function(f)
    local key='wh3_dlc23_chd_lord_convoy_overseer'
    f.panel.visible=false
    f.runtime.subtypes={[key]='general'};f.runtime.supported=function(k)return k==key end
    local convoy=component('military_convoys',f.root)
    local master=component('master_panel',convoy);component('reserve_master_listbox',master)
    local slot=component('master_slot',convoy)
    function slot:SimulateLClick() master.visible=true;f.master_reopened=true end
    local hud=component('button_convoys',component('faction_buttons_docker',f.root.children.hud_campaign))
    function hud:SimulateLClick()convoy.visible=true;master.visible=false;f.convoy_reopened=true end
    f.closed_panels={};f.environment.CampaignUI.ClosePanel=function(name)f.closed_panels[name]=true end
    f.ui.refresh_buttons();assert(f.ui.selected_subtype==key)
    f.click(component('xatw3_refresh_candidates'));assert(f.closed_panels.military_convoys)
    f.step();assert(#f.dispatched==0,'Convoy contexts still open')
    convoy.visible=false;f.drain();assert(#f.dispatched==1)
    f.runtime.on_result({status='SUCCEEDED'});f.drain()
    assert(f.convoy_reopened and f.master_reopened and f.ui.selected_subtype==key)
    assert(not f.reopened and not f.root.children.character_panel)
    f.emit('PanelClosedCampaign',{string='military_convoys'});assert(f.ui.selected_subtype==nil)
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
test('large_single_player_snapshot_stays_local_and_reference_consumes_once', function()
    local f=fixture()
    local r={version=1, faction='test_faction', action='refresh', sequence=8, turn=3,
        target='supported', expected=string.rep('x',4096)}
    f.ui.submit(r); r.expected='changed'; f.panel.visible=false; f.drain()
    assert(#f.dispatched==1 and #f.dispatched[1][2]<240)
    assert(f.ui.consume_request(r,'wrong')==nil)
    for _,field in ipairs({'version','action','sequence','turn','target','faction'}) do
        local value=r[field]; r[field]='different'
        assert(f.ui.consume_request(r,'sp1')==nil)
        r[field]=value
    end
    local frozen=f.ui.consume_request(r,'sp1')
    assert(frozen.expected==string.rep('x',4096))
    assert(f.ui.consume_request(r,'sp1')==nil)
end)
test('multiplayer_single_click_uses_shared_channel_without_local_model_dispatch', function()
    local f=fixture(); f.environment.cm.is_multiplayer=function() return true end
    local submitted
    f.runtime.multiplayer={submit=function(owner,r)
        assert(owner=='xatw3_campaign_utilities' and r.faction=='test_faction')
        submitted=r; return true
    end}
    f.start()
    assert(submitted.target=='supported' and f.closed==0 and #f.dispatched==0 and f.dialogs==0)
    assert(f.ui.submitting); f.runtime.on_result({status='SUCCEEDED'}); f.drain()
    assert(not f.ui.submitting and f.reopened==nil)
end)
return passed
