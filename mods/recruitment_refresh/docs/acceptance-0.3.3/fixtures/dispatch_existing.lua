local fc=cm:model():world():caravans_system():faction_caravans(cm:get_local_faction());assert(fc:idle_caravans():num_items()>0 and fc:active_caravans():num_items()==0)
local id=fc:idle_caravans():item_at(0):caravan_master():command_queue_index();local before=xatw3_test.owned();local offered_before=fc:available_caravan_recruitment_items():num_items();local sequence=xatw3_campaign_utilities.runtime.state.next_sequence
local function later(fn)cm:callback(function()local ok,e=pcall(fn);if not ok then xatw3_test.record('CONVOY_DISPATCH_FAIL '..tostring(e))end end,.7)end
local p=assert(find_uicomponent(core:get_ui_root(),'military_convoys','master_panel'));local list=assert(find_uicomponent(p,'owned_master_listbox','list_clip','list_box'));local card
for i=0,list:ChildCount()-1 do local c=UIComponent(list:Find(i));local ok,value=pcall(function()return c:GetContextObject('CcoCampaignCharacter'):Call('FamilyMemberCQI')end);if ok and value==id then card=c;break end end
assert(card and card:Visible(true));card:SimulateLClick()
later(function()
 local add=assert(find_uicomponent(p,'add_master_button'));assert(add:Visible(true) and (add:CurrentState()=='active' or add:CurrentState()=='hover'));assert(add:GetContextObject('CcoCampaignCharacter'):Call('FamilyMemberCQI')==id);add:SimulateLClick()
 later(function()
  local dispatch=assert(find_uicomponent(core:get_ui_root(),'military_convoys','new_convoy_section','button_dispatch'));local context=assert(dispatch:GetContextObject('CcoCampaignCaravan'))
  local info={id=id,button_state=dispatch:CurrentState(),selected=context:Call('CharacterContext.FamilyMemberCQI'),destination=context:Call('DestinationNodeContext.SettlementContext.Name'),capital=xatw3_move_capital.runtime.capital(cm:get_local_faction_name()),package_sha256=xatw3_test.package_sha}
  xatw3_test.save('convoy-dispatch-before',info)
  assert(info.selected==id and dispatch:Visible(true) and (dispatch:CurrentState()=='active' or dispatch:CurrentState()=='hover'),'Native dispatch unavailable after capital move')
  dispatch:SimulateLClick()
  later(function()
   assert(fc:active_caravans():num_items()==1 and fc:idle_caravans():num_items()==0)
   local caravan=fc:active_caravans():item_at(0);assert(caravan:caravan_master():command_queue_index()==id and caravan:cargo()>0)
   assert(fc:available_caravan_recruitment_items():num_items()==offered_before and xatw3_campaign_utilities.runtime.state.next_sequence==sequence)
   info.status='PASS';info.cargo=caravan:cargo();info.before=before;info.after=xatw3_test.owned()
   xatw3_test.save('convoy-dispatch-after-capital',info);xatw3_test.record('DLC_CONVOY_DISPATCH_PASS id='..id..' cargo='..caravan:cargo())
  end)
 end)
end)
