cm:dismiss_advice()
local done=find_uicomponent(core:get_ui_root(),'xatw3mc_confirm_action','ok_group','button_tick');if done and done:Visible(true)then done:SimulateLClick()end
local tour=find_uicomponent(core:get_ui_root(),'under_advisor_docker','scripted_tour_controls','button_close');if tour and tour:Visible(true)then tour:SimulateLClick()end
CampaignUI.ClosePanel('technology_panel');CampaignUI.ClosePanel('settlement_panel')
local opened=find_uicomponent(core:get_ui_root(),'military_convoys')
if not opened or not opened:Visible(true)then
 local b=assert(find_uicomponent(core:get_ui_root(),'hud_campaign','faction_buttons_docker','button_convoys'));assert(b:Visible(true) and (b:CurrentState()=='active' or b:CurrentState()=='hover'));b:SimulateLClick()
end
cm:callback(function()
 local p=assert(find_uicomponent(core:get_ui_root(),'military_convoys'));local master=assert(find_uicomponent(p,'master_panel'))
 if not master:Visible(true)then assert(find_uicomponent(p,'master_slot')):SimulateLClick()end
 xatw3_test.record('OPEN_CONVOYS_COMPLETE turn='..cm:model():turn_number())
end,1)
