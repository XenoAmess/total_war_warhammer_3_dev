assert(cm:get_local_faction_name()=='wh3_dlc29_skv_clan_scruten')
assert(type(verminlord_spawn)=='function'and type(verminlords_config)=='table')
local f=cm:get_local_faction()
local rt=xatw3_campaign_utilities.runtime
local before={}
for _,key in ipairs(verminlords_config.subtype_to_choice_mapping)do
 local pool=assert(rt.read_pool(f:name(),key));assert(#pool==0,'Do not add to an existing finite pool')
 before[key]=pool
end
local technology_before=f:has_technology(verminlords_config.tech_key)
cm:instantly_research_technology(f:name(),verminlords_config.tech_key,false)
for _,key in ipairs(verminlords_config.subtype_to_choice_mapping)do verminlord_spawn(f:name(),key)end
cm:callback(function()
 local ok,e=pcall(function()
  local pools={}
  assert(f:has_technology(verminlords_config.tech_key))
  for _,key in ipairs(verminlords_config.subtype_to_choice_mapping)do
   local pool=assert(rt.read_pool(f:name(),key));assert(#pool==1)
   pools[key]={pool=pool,supported=rt.supported(key),plan=xatw3_campaign_utilities.logic.plan(pool,f:name(),key)}
  end
  xatw3_test.save('verminlord-vanilla-generation-fixture',{status='PASS',fixture=true,package_sha256=xatw3_test.package_sha,technology=verminlords_config.tech_key,technology_before=technology_before,technology_after=f:has_technology(verminlords_config.tech_key),full_ritual_credited=false,spawn_function='vanilla verminlord_spawn',before=before,after=pools})
  xatw3_test.record('VERMINLORD_VANILLA_GENERATION_READY')
 end)
 if not ok then xatw3_test.record('VERMINLORD_FIXTURE_FAIL '..tostring(e))end
end,.8)
