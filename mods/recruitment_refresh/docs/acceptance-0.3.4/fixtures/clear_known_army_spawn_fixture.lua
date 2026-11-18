local faction=cm:get_local_faction()
local records={}
local ids={16870}
for _,id in ipairs(ids)do
 local actor=cm:get_family_member_by_cqi(id):character()
 assert(not actor:is_null_interface()and actor:faction():name()==faction:name())
 do
  local oldx,oldy=actor:logical_position_x(),actor:logical_position_y()
  local x,y=cm:find_valid_spawn_location_for_character_from_settlement(faction:name(),faction:home_region():name(),false,true,10)
  assert(type(x)=='number'and type(y)=='number'and x>=0 and y>=0)
  local id=actor:family_member():command_queue_index()
  records[#records+1]={id=id,subtype=actor:character_subtype_key(),before_x=oldx,before_y=oldy,target_x=x,target_y=y}
  cm:teleport_to(cm:char_lookup_str(actor),x,y)
 end
end
assert(#records>0)
cm:callback(function()
 for _,v in ipairs(records)do
  local actor=cm:get_family_member_by_cqi(v.id):character()
  assert(not actor:is_null_interface());v.after_x=actor:logical_position_x();v.after_y=actor:logical_position_y()
  assert(v.after_x==v.target_x and v.after_y==v.target_y)
 end
 xatw3_test.save('owned-army-position-fixture-'..#records,{fixture=true,status='PASS',reason='Clear the occupied native recruitment spawn point between independent native hires',full_native_movement_credited=false,records=records})
 xatw3_test.record('VERMINLORD_SPAWN_POSITION_FIXTURE_READY '..#records)
end,.6)
