local live=xatw3_campaign_utilities;local rt=live.runtime;local target='wh3_dlc23_chd_sorcerer_prophet_death';local root=core:get_ui_root()
local lore=assert(find_uicomponent(root,'character_panel','general_selection_panel','main_holder','lore_select_parent','lord_magic_lore_type','lore_type_list','wh_main_lore_death'));assert(lore:Visible(true));lore:SimulateLClick()
cm:callback(function()
 live.ui.refresh_buttons();assert(live.ui.selected_subtype==target)
 local faction=cm:get_local_faction_name();local before=assert(rt.read_pool(faction,target));local seq=rt.state.next_sequence;local defaults={};for _,c in ipairs(before)do defaults[tostring(c.id)]=xatw3_test.defaults(c.id)end
 local data={target=target,before=before,others_before=xatw3_test.others(target),owned_before=xatw3_test.owned(),default_skills_before=defaults,package_sha256=xatw3_test.package_sha,capital=xatw3_move_capital.runtime.capital(faction)}
 xatw3_test.save('before-lord-lore-final',data)
 assert(find_uicomponent(root,'character_panel','xatw3_refresh_candidates')):SimulateLClick();local tries=0
 local function verify()
  tries=tries+1;local panel=find_uicomponent(root,'character_panel')
  if not rt.state.last or rt.state.last.sequence~=seq or live.ui.submitting or not panel or not panel:Visible(true) or live.ui.selected_subtype~=target then
   if tries<80 then cm:callback(verify,.4);return end
   xatw3_test.record('FINAL_LORD_LORE_TIMEOUT result='..tostring(rt.state.last and rt.state.last.status)..' target='..tostring(live.ui.selected_subtype));return
  end
  data.after=assert(rt.read_pool(faction,target));data.result=rt.state.last;data.ui_target=live.ui.selected_subtype;data.sequence_before=seq;data.sequence_after=rt.state.next_sequence;data.others_after=xatw3_test.others(target);data.owned_after=xatw3_test.owned();data.default_skills_after={}
  assert(data.result.status=='SUCCEEDED' and #before==2 and #data.after==3 and data.result.completed==2 and data.result.added==1 and data.sequence_after==seq+1)
  for k,v in pairs(data.others_before)do assert(data.others_after[k]==v,'Other lore or hero pool changed')end
  assert(data.owned_before==data.owned_after,'Owned convoys changed during ordinary lord refresh')
  for _,pair in ipairs(data.result.pairs)do local skills=xatw3_test.defaults(pair.new);data.default_skills_after[tostring(pair.new)]=skills;assert(defaults[tostring(pair.old)]==skills,'Default caster skills changed')end
  data.status='PASS';xatw3_test.save('lord-lore-final',data);xatw3_test.record('FINAL_LORD_LORE_PASS death=2->3 returned='..data.ui_target)
 end
 cm:callback(verify,.4)
end,.6)
