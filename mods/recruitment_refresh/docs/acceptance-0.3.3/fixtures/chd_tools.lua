local live=xatw3_campaign_utilities;local rt,logic=live.runtime,live.logic
local subtype='wh3_dlc23_chd_lord_convoy_overseer'
local function later(fn)cm:callback(function()local ok,e=pcall(fn);if not ok then xatw3_test.record('DLC_CASE_FAIL '..tostring(e))end end,.5)end
local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-acceptance-20261118/escort_templates.lua','r'));local s=f:read('*a');f:close();local templates=assert(loadstring(s))()
local function master_panel()return assert(find_uicomponent(core:get_ui_root(),'military_convoys','master_panel'))end
function xatw3_test.chd_refresh(name)
 local faction=cm:get_local_faction_name();local before=assert(rt.read_pool(faction,subtype));local seq=rt.state.next_sequence
 live.ui.refresh_buttons();assert(live.ui.selected_subtype==subtype)
 local plan=logic.plan(before,faction,subtype);assert(#plan.replace>0)
 local eligible={};for _,c in ipairs(plan.replace)do eligible[c.id]=true end
 local defaults={};for _,c in ipairs(before)do defaults[tostring(c.id)]=xatw3_test.defaults(c.id)end
 local evidence={name=name,package_sha256=xatw3_test.package_sha,before=before,owned_before=xatw3_test.owned(),others_before=xatw3_test.others(subtype),default_skills_before=defaults,capital=xatw3_move_capital.runtime.capital(faction)}
 xatw3_test.save('before-'..name,evidence)
 local button=assert(find_uicomponent(master_panel(),'xatw3_refresh_candidates'));assert(button:Visible(true) and (button:CurrentState()=='active' or button:CurrentState()=='hover'))
 button:SimulateLClick();local tries=0
 local function verify()
  tries=tries+1
  local panel=find_uicomponent(core:get_ui_root(),'military_convoys','master_panel')
  if not rt.state.last or rt.state.last.sequence~=seq or live.ui.submitting or not panel or not panel:Visible(true) or live.ui.selected_subtype~=subtype then assert(tries<80,'Convoy refresh or UI reopening timed out');later(verify);return end
  evidence.result=rt.state.last;evidence.after=assert(rt.read_pool(faction,subtype));evidence.owned_after=xatw3_test.owned();evidence.others_after=xatw3_test.others(subtype);evidence.requests_consumed=rt.state.next_sequence-seq;evidence.returned_ui_target=live.ui.selected_subtype
  assert(evidence.result.status=='SUCCEEDED' and evidence.requests_consumed==1 and evidence.result.added==0 and #before==#evidence.after)
  assert(evidence.owned_before==evidence.owned_after,'Owned convoy changed')
  for k,v in pairs(evidence.others_before)do assert(evidence.others_after[k]==v,'Other pool changed')end
  local expected={};local old={};for _,c in ipairs(before)do local copy={};for k,v in pairs(c)do copy[k]=v end;expected[#expected+1]=copy;old[c.id]=c end
  evidence.default_skills_after={}
  for _,c in ipairs(evidence.after)do
   assert(old[c.id],'Convoy identity changed')
   if eligible[c.id] then
    assert(old[c.id].background~=c.background,'Offered background unchanged')
    for _,copy in ipairs(expected)do if copy.id==c.id then copy.background=c.background end end
   else assert(old[c.id].background==c.background,'Protected convoy background changed')end
   local skills=xatw3_test.defaults(c.id);evidence.default_skills_after[tostring(c.id)]=skills;assert(defaults[tostring(c.id)]==skills,'Default skills changed')
  end
  assert(logic.fingerprint(expected)==logic.fingerprint(evidence.after),'Other convoy details changed')
  assert(find_uicomponent(master_panel(),'xatw3_refresh_candidates'):Visible(true))
  xatw3_test.save('case-'..name,evidence);xatw3_test.record('DLC_CHD_REFRESH_PASS '..name..' '..#before..'->'..#evidence.after)
 end
 later(verify)
end
function xatw3_test.chd_hire(name,expected_id)
 local faction=cm:get_local_faction();local fc=cm:model():world():caravans_system():faction_caravans(faction);local offered=fc:available_caravan_recruitment_items();assert(offered:num_items()>0)
 local id=expected_id or offered:item_at(0):caravan_master():command_queue_index();local in_offers=false;for i=0,offered:num_items()-1 do if offered:item_at(i):caravan_master():command_queue_index()==id then in_offers=true end end;assert(in_offers,'Expected caravan not currently offered')
 local d=cm:get_family_member_by_cqi(id):character_details();local background=d:background_skill();local escort=assert(templates[background]);local expected={}
 for _,unit in ipairs(escort)do local k=type(unit)=='table' and unit[1] or unit;expected[k]=(expected[k] or 0)+1 end
 local list=assert(find_uicomponent(master_panel(),'reserve_master_listbox','list_clip','list_box'));local card
 for i=0,list:ChildCount()-1 do local c=UIComponent(list:Find(i));local ok,value=pcall(function()return c:GetContextObject('CcoCampaignCharacter'):Call('FamilyMemberCQI')end);if ok and value==id then card=c;break end end
 assert(card and card:Visible(true),'Offered convoy card not visible');card:SimulateLClick()
 local before=faction:treasury();local _,count=xatw3_test.owned()
 later(function()
  local hire=assert(find_uicomponent(master_panel(),'hire_add_master_button'));assert(hire:Visible(true) and (hire:CurrentState()=='active' or hire:CurrentState()=='hover'),'Native convoy hire button unavailable')
  local selected=assert(hire:GetContextObject('CcoCampaignCharacter')):Call('FamilyMemberCQI');assert(selected==id,'Native convoy selection differs from expected candidate')
  assert(fc:available_caravan_recruitment_items():num_items()==offered:num_items());hire:SimulateLClick()
  later(function()
   local snapshot,after=xatw3_test.owned();local actor=cm:get_family_member_by_cqi(id):character();assert(not actor:is_null_interface() and after==count+1 and faction:treasury()<before)
   local actual={};local units=actor:military_force():unit_list();for i=0,units:num_items()-1 do local k=units:item_at(i):unit_key();actual[k]=(actual[k] or 0)+1 end
   assert(units:num_items()==#escort+1);for k,n in pairs(expected)do assert(actual[k]==n,'Incorrect escort '..k)end
   assert(actor:background_skill()==background and rt.state.history[tostring(id)].recruited)
   xatw3_test.save(name,{status='PASS',id=id,background=background,escort_expected=expected,escort_actual=actual,gold_before=before,gold_after=faction:treasury(),owned_before=count,owned_after=after,owned_snapshot=snapshot,package_sha256=xatw3_test.package_sha})
   xatw3_test.record('DLC_CHD_HIRE_PASS '..name..' id='..id)
  end)
 end)
end
xatw3_test.record('CHD_ACCEPTANCE_TOOLS_READY')
