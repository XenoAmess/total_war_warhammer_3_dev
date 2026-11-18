local target='wh3_dlc23_chd_sorcerer_prophet_death';local rt=xatw3_campaign_utilities.runtime;local faction=cm:get_local_faction();local pool=assert(rt.read_pool(faction:name(),target));local eligible={};for _,c in ipairs(pool)do eligible[c.id]=c end
local panel=assert(find_uicomponent(core:get_ui_root(),'character_panel'));local list=assert(find_uicomponent(panel,'character_list','listview','list_clip','list_box'));local chosen,button
for i=0,list:ChildCount()-1 do local c=UIComponent(list:Find(i));local b=find_uicomponent(c,'button_wh3');if b and b:Visible(true)then local id=b:GetContextObject('CcoCampaignCharacter'):Call('FamilyMemberCQI');if eligible[id]then chosen=eligible[id];button=b;break end end end
assert(chosen and button);local before=faction:treasury();local forces=faction:military_force_list():num_items();button:SimulateLClick()
cm:callback(function()
 local hire=assert(find_uicomponent(panel,'footer','button_raise'));assert(hire:Visible(true) and (hire:CurrentState()=='active' or hire:CurrentState()=='hover'));hire:SimulateLClick()
 cm:callback(function()
  local actor=cm:get_family_member_by_cqi(chosen.id):character();assert(not actor:is_null_interface() and actor:character_subtype_key()==target and actor:background_skill()==chosen.background and faction:military_force_list():num_items()==forces+1 and rt.state.history[tostring(chosen.id)].recruited)
  xatw3_test.save('lord-native-hire',{status='PASS',id=chosen.id,target=target,background=chosen.background,gold_before=before,gold_after=faction:treasury(),forces_before=forces,forces_after=faction:military_force_list():num_items(),rank=actor:rank(),region=actor:region():name(),capital=xatw3_move_capital.runtime.capital(faction:name()),package_sha256=xatw3_test.package_sha});xatw3_test.record('FINAL_LORD_HIRE_PASS '..target..' id='..chosen.id)
 end,.8)
end,.6)
