local live=xatw3_move_capital;local rt=live.runtime;local rr=xatw3_campaign_utilities.runtime
local faction=cm:get_local_faction();local key=faction:name();local previous=assert(rt.capital(key));local home=cm:get_region(previous)
local target;local candidates=home:adjacent_region_list()
for i=0,faction:region_list():num_items()-1 do local r=faction:region_list():item_at(i);if r:name()~=previous then target=r;break end end
local fixture=xatw3_test.capital_fixture
if not target then
 for i=0,candidates:num_items()-1 do local r=candidates:item_at(i);if not r:settlement():is_null_interface() and not r:is_abandoned() and not r:owning_faction():is_human() then target=r;break end end
 assert(target,'No valid nearby settlement fixture');fixture={region=target:name(),original_owner=target:owning_faction():name(),operation='cm:transfer_region_to_faction; disposable acceptance campaign'}
 xatw3_test.capital_fixture=fixture;xatw3_test.save('capital-settlement-fixture-before-transfer',fixture)
 cm:transfer_region_to_faction(target:name(),key)
end
local target_key=target:name()
local function later(fn)cm:callback(function()local ok,e=pcall(fn);if not ok then xatw3_test.record('DLC_CAPITAL_FAIL '..tostring(e))end end,.7)end
local function buildings(region)
 local values={};local slots=region:settlement():slot_list()
 for i=0,slots:num_items()-1 do local slot=slots:item_at(i);if slot:has_building() then values[#values+1]=slot:building():name() end end
 table.sort(values);return table.concat(values,',')
end
later(function()
 assert(target:owning_faction():name()==key)
 local seq=rt.state.next_sequence;local refresh_seq=rr.state.next_sequence;local old_owned=xatw3_test.owned();local old_pools=xatw3_test.others('none')
 local before=assert(rt.region(target_key));local before_buildings=buildings(target);local old_region=assert(rt.region(previous));local old_buildings=buildings(home)
 local convoy_pool=assert(rr.read_pool(key,'wh3_cp1_cth_sawai_caravan'));local convoy_fingerprint=xatw3_campaign_utilities.logic.fingerprint(convoy_pool)
 assert(live.logic.capital_eligible(before,key,previous))
 local evidence={fixture=fixture,previous=previous,target=target_key,before=before,buildings_before=before_buildings,previous_region_before=old_region,previous_buildings_before=old_buildings,caravans_before=old_owned,refresh_sequence_before=refresh_seq,pools_before=old_pools,convoy_pool_before=convoy_pool,capital_package_sha256='e3702133d65dc7d08c1248a96e5b48a297505f238fe2d6e79a950d79f9d3767f',refresh_package_sha256=xatw3_test.package_sha}
 CampaignUI.ClosePanel('cp1_cth_bhashiva_caravans');CampaignUI.CloseCurrentHUDPanel();common.get_context_value('CcoCampaignSettlement',home:cqi(),'Select');common.get_context_value('CcoCampaignSettlement',target:cqi(),'Select')
 later(function()
  assert(live.ui.selected_region==target_key,'Wrong settlement UI target')
  local b=assert(find_uicomponent(core:get_ui_root(),'settlement_panel','xatw3mc_move_capital'));assert(b:Visible() and b:CurrentState()=='active');b:SimulateLClick()
  assert(live.ui.pending and live.ui.pending.target==target_key)
  assert(find_uicomponent(core:get_ui_root(),'xatw3mc_confirm_action','both_group','button_tick')):SimulateLClick()
  later(function()
   evidence.after=assert(rt.region(target_key));evidence.result=rt.state.last;evidence.buildings_after=buildings(target);evidence.caravans_after=xatw3_test.owned();evidence.capital_after=rt.capital(key);evidence.refresh_sequence_after=rr.state.next_sequence
   evidence.previous_region_after=assert(rt.region(previous));evidence.previous_buildings_after=buildings(home);evidence.pools_after=xatw3_test.others('none');evidence.convoy_pool_after=assert(rr.read_pool(key,'wh3_cp1_cth_sawai_caravan'))
   xatw3_test.save('capital-attempt-'..key,evidence)
   assert(evidence.result.status=='SUCCEEDED' and rt.state.next_sequence==seq+1 and rt.capital(key)==target_key)
   assert(evidence.before.owner==evidence.after.owner and evidence.before.level==evidence.after.level and evidence.before.province_capital==evidence.after.province_capital)
   assert(before_buildings==evidence.buildings_after and old_owned==evidence.caravans_after and refresh_seq==rr.state.next_sequence)
   assert(old_buildings==evidence.previous_buildings_after and old_region.owner==evidence.previous_region_after.owner and old_region.level==evidence.previous_region_after.level and old_region.province_capital==evidence.previous_region_after.province_capital,'Previous capital settlement changed')
   assert(convoy_fingerprint==xatw3_campaign_utilities.logic.fingerprint(evidence.convoy_pool_after),'Offered convoy pool changed during capital move')
   local new_pools=xatw3_test.others('none');for k,v in pairs(old_pools)do assert(new_pools[k]==v,'Recruitment pool changed during capital move')end
   assert(not rt.state.locked and not live.ui.submitting)
   xatw3_test.save('capital-'..key,evidence);xatw3_test.record('DLC_CAPITAL_PASS '..previous..'->'..target_key)
  end)
 end)
end)
