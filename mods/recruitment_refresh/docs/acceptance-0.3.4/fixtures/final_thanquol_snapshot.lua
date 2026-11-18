local rt=xatw3_campaign_utilities.runtime;local cap=xatw3_move_capital.runtime
local f=cm:get_local_faction()
assert(f:name()=='wh3_dlc29_skv_clan_scruten')
local actors={}
local list=f:character_list()
for i=0,list:num_items()-1 do
 local a=list:item_at(i)
 if verminlords_config.verminlord_on_spawn_setup[a:character_subtype_key()]then
  local id=a:family_member():command_queue_index()
  assert(rt.state.history[tostring(id)].recruited)
  actors[tostring(id)]={id=id,subtype=a:character_subtype_key(),rank=a:rank(),region=a:region():name(),x=a:logical_position_x(),y=a:logical_position_y(),force=a:military_force():command_queue_index(),background=a:background_skill(),default_skills=xatw3_test.defaults(id)}
 end
end
local n=0;for _ in pairs(actors)do n=n+1 end;assert(n==4)
for _,key in ipairs(verminlords_config.subtype_to_choice_mapping)do
 assert(#assert(rt.read_pool(f:name(),key))==0 and not rt.supported(key))
end
assert(rt.state.next_sequence==5 and not rt.state.locked)
assert(cap.capital(f:name())=='wh3_main_combi_region_swartzhafen')
assert(cap.state.last.status=='SUCCEEDED'and not cap.state.locked)
xatw3_test.save('thanquol-final-snapshot',{status='PASS',faction=f:name(),turn=cm:turn_number(),capital=cap.capital(f:name()),package_sha256=xatw3_test.package_sha,refresh_state=rt.state,capital_state=cap.state,pools=xatw3_test.others('none'),actors=actors,gold=f:treasury()})
xatw3_test.record('THANQUOL_FINAL_NATIVE_SNAPSHOT_PASS')
