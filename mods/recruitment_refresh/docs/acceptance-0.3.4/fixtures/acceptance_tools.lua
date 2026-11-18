local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/escort_templates.lua','r'));local source=f:read('*a');f:close();local escort_templates=assert(loadstring(source))()
local live=xatw3_campaign_utilities;local rt,logic=live.runtime,live.logic
local function later(fn)
 cm:callback(function() local ok,e=pcall(fn);if not ok then xatw3_test.record('FINAL_CASE_FAIL '..tostring(e)) end end,.6)
end
local function card(id)
 local p=assert(find_uicomponent(core:get_ui_root(),'character_panel'))
 local list=assert(find_uicomponent(p,'character_list','listview','list_clip','list_box'))
 for i=0,list:ChildCount()-1 do
  local c=UIComponent(list:Find(i));local b=find_uicomponent(c,'button_wh3')
  if c:Visible() and b and b:Visible() then
   local ctx=b:GetContextObject('CcoCampaignCharacter')
   if ctx and ctx:Call('FamilyMemberCQI')==id then return b end
  end
 end
 error('Visible card missing '..id)
end
local function owned()
 local owner=cm:get_local_faction();local fc=cm:model():world():caravans_system():faction_caravans(owner)
 local values={}
 for _,name in ipairs({'active_caravans','idle_caravans'}) do
  local list=fc[name](fc)
  for i=0,list:num_items()-1 do
   local c=list:item_at(i);local mf=c:caravan_force();local units={}
   for j=0,mf:unit_list():num_items()-1 do units[#units+1]=mf:unit_list():item_at(j):unit_key() end
   values[#values+1]=table.concat({name,tostring(c:caravan_master():command_queue_index()),
    tostring(mf:command_queue_index()),tostring(c:cargo()),tostring(c:is_returning()),
    tostring(c:rounds_until_return()),table.concat(units,',')},':')
  end
 end
 table.sort(values);return table.concat(values,'|'),#values
end
local function others(target)
 local result={}
 for _,key in ipairs(xatw3_test.pool_keys) do
  if key~=target then result[key]=logic.fingerprint(assert(rt.read_pool(cm:get_local_faction_name(),key))) end
 end
 return result
end
local function defaults(id)
 local mr=memreader_plus;local d=cm:get_family_member_by_cqi(id):character_details()
 local dp=mr.read_pointer(mr.ud_topointer(d),8);local rows=mr.read_pointer(dp,0x208);local values={}
 for i=0,mr.read_uint32(dp,0x204)-1 do
  local row=mr.add(rows,i*16);local nodes=mr.read_pointer(row,8)
  for j=0,mr.read_uint32(row,4)-1 do
   local node=mr.add(nodes,j*48);local n=mr.read_uint8(node,0x10)
   if n>0 then
    local record=mr.read_pointer(node,0);local skill=mr.read_pointer(record,8)
    if mr.read_uint8(skill,0x4c)==0 then values[#values+1]=mr.tostring(record)..':'..n end
   end
  end
 end
 table.sort(values);return table.concat(values,',')
end
function xatw3_test.hire_caravan(name)
 xatw3_test.record('HIRE_BEGIN '..name)
 local fc=cm:model():world():caravans_system():faction_caravans(cm:get_local_faction());local candidates=fc:available_caravan_recruitment_items()
 assert(candidates:num_items()>0);local id=xatw3_test.hire_id or candidates:item_at(0):caravan_master():command_queue_index()
 local background=cm:get_family_member_by_cqi(id):character_details():background_skill()
 local expected_escort=assert(escort_templates[background]);local expected_counts={}
 for _,unit in ipairs(expected_escort) do local key=type(unit)=='table' and unit[1] or unit;expected_counts[key]=(expected_counts[key] or 0)+1 end
 local before=cm:get_local_faction():treasury();local _,count=owned();xatw3_test.record('HIRE_SELECT '..id);card(id):SimulateLClick()
 later(function()
  local b=assert(find_uicomponent(core:get_ui_root(),'character_panel','footer','button_raise'))
  assert(b:CurrentState()=='active' or b:CurrentState()=='hover','Native hire button unavailable '..b:CurrentState());xatw3_test.record('HIRE_CLICK '..id);b:SimulateLClick();xatw3_test.record('HIRE_CLICK_RETURN '..id)
  later(function()
   xatw3_test.record('HIRE_VERIFY_BEGIN '..id);local snapshot,after=owned();xatw3_test.record('HIRE_OWNED_READ '..after);local actor=cm:get_family_member_by_cqi(id):character();xatw3_test.record('HIRE_ACTOR_READ '..id)
   assert(after==count+1 and not actor:is_null_interface())
   local units=actor:military_force():unit_list();assert(units:num_items()==#expected_escort+1,'Initial escort count differs from vanilla background')
   local actual_escort={}
   for i=0,units:num_items()-1 do local key=units:item_at(i):unit_key();actual_escort[key]=(actual_escort[key] or 0)+1 end
   for key,n in pairs(expected_counts) do assert(actual_escort[key]==n,'Wrong escort units for '..background..': '..key) end
   assert(cm:get_local_faction():treasury()<before)
   assert(actor:background_skill()==background and rt.state.history[tostring(id)].recruited)
   xatw3_test.save(name,{status='PASS',package_sha256=xatw3_test.package_sha,id=id,background=background,
    escort_expected=expected_counts,escort_actual=actual_escort,gold_before=before,gold_after=cm:get_local_faction():treasury(),owned_before=count,owned_after=after,owned_snapshot=snapshot})
   xatw3_test.record('FINAL_HIRE_PASS '..name..' id='..id..' owned='..count..'->'..after)
  end)
 end)
end
function xatw3_test.case(target,name,caravan)
 live.ui.refresh_buttons();assert(live.ui.selected_subtype==target,'Wrong UI target '..tostring(live.ui.selected_subtype))
 local faction=cm:get_local_faction_name();local before=assert(rt.read_pool(faction,target));local seq=rt.state.next_sequence
 local owned_before=caravan and owned() or 'not_applicable'
 local evidence={package_sha256=xatw3_test.package_sha,mode='native_ui',target=target,request_target=live.ui.selected_subtype,
  faction=faction,before=before,others_before=others(target),owned_before=owned_before}
 evidence.default_skills_before={};evidence.ranks_before={}
 for _,c in ipairs(before) do evidence.default_skills_before[tostring(c.id)]=defaults(c.id);evidence.ranks_before[tostring(c.id)]=common.get_context_value('CcoCampaignCharacter',c.id,'Rank') end
 assert(#logic.plan(before,faction,target).replace>0,'No eligible candidates')
 xatw3_test.save('before-'..name,evidence)
 xatw3_test.continue=function()
  xatw3_test.continue=nil
  local b=assert(find_uicomponent(core:get_ui_root(),'character_panel','xatw3_refresh_candidates'))
  assert(b:Visible() and (b:CurrentState()=='active' or b:CurrentState()=='hover'));b:SimulateLClick()
  local tries=0
  local function verify()
   tries=tries+1
   if not rt.state.last or rt.state.last.sequence~=seq or live.ui.submitting or live.ui.selected_subtype~=target then
    assert(tries<50,'Native refresh/reopen timeout');later(verify);return
   end
   evidence.after=assert(rt.read_pool(faction,target));evidence.result=rt.state.last
   evidence.default_skills_after={};evidence.ranks_after={}
   for _,c in ipairs(evidence.after) do evidence.default_skills_after[tostring(c.id)]=defaults(c.id);evidence.ranks_after[tostring(c.id)]=common.get_context_value('CcoCampaignCharacter',c.id,'Rank') end
   evidence.returned_ui_target=live.ui.selected_subtype;evidence.requests_consumed=rt.state.next_sequence-seq
   evidence.others_after=others(target);evidence.owned_after=caravan and owned() or 'not_applicable'
   assert(evidence.result.status=='SUCCEEDED' and evidence.requests_consumed==1)
   assert(#evidence.after==math.max(#before,logic.minimum_candidates) or caravan or evidence.result.added==0)
   if caravan then assert(#evidence.after==#before and evidence.result.added==0) end
   for key,value in pairs(evidence.others_before) do assert(evidence.others_after[key]==value,'Other pool changed') end
   assert(evidence.owned_after==evidence.owned_before,'Owned caravan changed')
   for _,pair in ipairs(evidence.result.pairs) do
    assert(evidence.default_skills_before[tostring(pair.old)]==evidence.default_skills_after[tostring(pair.new)],'Default skills changed')
    -- Unhired CCO Rank is nil; default skill levels are the actual comparison above.
   end
   for _,v in ipairs(evidence.after) do assert(card(v.id)) end
   xatw3_test.save('case-'..name,evidence);xatw3_test.record('FINAL_REFRESH_PASS '..name..' before='..#before..' after='..#evidence.after..' replaced='..evidence.result.completed)
  end
  later(verify)
 end
 xatw3_test.record('FINAL_READY_BEFORE '..name)
end
xatw3_test.card=card

xatw3_test.owned=owned
xatw3_test.defaults=defaults
xatw3_test.others=others
