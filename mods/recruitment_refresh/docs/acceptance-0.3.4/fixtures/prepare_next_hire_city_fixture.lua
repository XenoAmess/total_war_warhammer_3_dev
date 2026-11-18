local f=cm:get_local_faction();local target
xatw3_test.hire_used_provinces=xatw3_test.hire_used_provinces or{wh3_main_combi_province_black_water=true,wh3_main_combi_province_southern_sylvania=true}
local regions=f:region_list()
for i=0,regions:num_items()-1 do
 local adjacent=regions:item_at(i):adjacent_region_list()
 for j=0,adjacent:num_items()-1 do
  local candidate=adjacent:item_at(j)
  if not xatw3_test.hire_used_provinces[candidate:province_name()]and not candidate:is_abandoned()and not candidate:settlement():is_null_interface()and candidate:owning_faction():name()~=f:name()and not candidate:owning_faction():is_human()then target=candidate;break end
 end
 if target then break end
end
assert(target,'No NPC settlement available for independent native hire fixture')
local evidence={fixture=true,region=target:name(),original_owner=target:owning_faction():name(),operation='cm:transfer_region_to_faction',purpose='Independent native recruitment location; previous native hire control is unavailable at its settlement',full_siege_credited=false}
xatw3_test.hire_used_provinces[target:province_name()]=true;
xatw3_test.native_hire_region=target:name();xatw3_test.expected_hire_region=target:name()
cm:transfer_region_to_faction(target:name(),f:name())
cm:callback(function()
 assert(target:owning_faction():name()==f:name())
 xatw3_test.save('native-hire-city-fixture-'..target:name(),evidence)
 xatw3_test.record('INDEPENDENT_NATIVE_HIRE_CITY_READY '..target:name())
end,.8)
