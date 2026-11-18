local function later(fn)
 cm:callback(function()local ok,e=pcall(fn);if not ok then xatw3_test.record('VERMINLORD_HIRE_FAIL '..tostring(e))end end,.7)
end
function xatw3_test.hire_verminlord(kind)
 local rt=xatw3_campaign_utilities.runtime
 local target='wh3_dlc29_skv_verminlord_'..kind
 local b=find_uicomponent(core:get_ui_root(),'character_panel','lord_magic_lore_type','lore_type_list','wh3_dlc29_lore_verminlord_'..kind)
 if b and b:Visible(true)then b:SimulateLClick()else xatw3_campaign_utilities.ui.refresh_buttons();assert(xatw3_campaign_utilities.ui.selected_subtype==target,'Single remaining native category has a different subtype')end
 later(function()
  local f=cm:get_local_faction();local pool=assert(rt.read_pool(f:name(),target));assert(#pool==1)
  local candidate=pool[1];local id=candidate.id;local before=f:treasury();local count=f:military_force_list():num_items()
  local original_default_skills=xatw3_test.defaults(id);local others=xatw3_test.others(target);local seq=rt.state.next_sequence
  local card=xatw3_test.card(id);assert(card:CurrentState()=='active'or card:CurrentState()=='selected'or card:CurrentState()=='selected_hover');card:SimulateLClick()
  later(function()
   local hire=assert(find_uicomponent(core:get_ui_root(),'character_panel','footer','button_raise'))
   assert(hire:Visible(true)and(hire:CurrentState()=='active'or hire:CurrentState()=='hover'));hire:SimulateLClick()
   later(function()
    local actor=cm:get_family_member_by_cqi(id):character()
    assert(not actor:is_null_interface()and actor:character_subtype_key()==target and actor:rank()==1)
    assert(actor:region():name()==(xatw3_test.expected_hire_region or f:home_region():name()))
    assert(f:treasury()<before and f:military_force_list():num_items()==count+1)
    assert(rt.state.history[tostring(id)].recruited)
    local after=assert(rt.read_pool(f:name(),target));assert(#after==0 and not rt.supported(target))
    local after_others=xatw3_test.others(target);for key,value in pairs(others)do assert(after_others[key]==value,'Native hire changed another recruitment pool')end
    assert(seq==rt.state.next_sequence)
    assert(original_default_skills==xatw3_test.defaults(id),'Native hire changed default skills')
    xatw3_test.save('verminlord-native-hire-'..kind,{status='PASS',package_sha256=xatw3_test.package_sha,id=id,subtype=target,rank=actor:rank(),region=actor:region():name(),gold_before=before,gold_after=f:treasury(),cost=before-f:treasury(),forces_before=count,forces_after=f:military_force_list():num_items(),pool_before=pool,pool_after=after,other_pools_unchanged=true,default_skills=original_default_skills,recruited_protected=true,refresh_sequence_unchanged=true})
    xatw3_test.record('VERMINLORD_NATIVE_HIRE_PASS '..kind)
   end)
  end)
 end)
end
xatw3_test.record('VERMINLORD_HIRE_TOOLS_READY')
