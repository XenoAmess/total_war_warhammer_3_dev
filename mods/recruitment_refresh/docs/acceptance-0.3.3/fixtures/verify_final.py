from pathlib import Path
import argparse,json,hashlib,sys
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args();assert set(a.mod)=={'recruitment_refresh','move_capital'}
r=Path(__file__).parent;repo=Path.cwd();read=lambda name:json.loads((r/'evidence'/(name+'.json')).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((r/'expected-final.json').read_text());digest=expected['sha256'];state=json.loads((r/'session.json').read_text())
for item in state['installed']:assert sha(Path(item['path']))==item['sha256']
assert sha(repo/'mods/recruitment_refresh/build/xatw3_campaign_utilities.pack')==digest
for name in ['final-convoy-button','chd-final-original-hire','convoy-dispatch-after-capital','vanilla-convoy-capacity-fixture','chd-refreshed-hire','empty-convoy-pool','lord-lore-final','lord-native-hire']:
 data=read(name);assert data['package_sha256']==digest,name
 if 'status'in data:assert data['status']=='PASS',name
for name,prefix in [('chd-idle-protection','idle_caravans:'),('chd-active-protection','active_caravans:')]:
 data=read('case-'+name);assert data['package_sha256']==digest and data['result']['status']=='SUCCEEDED' and len(data['before'])==len(data['after'])==1
 assert data['before'][0]['id']==data['after'][0]['id'] and data['before'][0]['background']!=data['after'][0]['background']
 assert data['owned_before']==data['owned_after'] and data['owned_before'].startswith(prefix) and data['others_before']==data['others_after'] and data['requests_consumed']==1
for name in ['chd-final-original-hire','chd-refreshed-hire']:
 data=read(name);assert data['owned_after']==data['owned_before']+1 and data['gold_after']<data['gold_before']
 assert sum(data['escort_actual'].values())==sum(data['escort_expected'].values())+1
 for key,n in data['escort_expected'].items():assert data['escort_actual'][key]==n
capital=read('capital-wh3_dlc23_chd_astragoth');assert capital['refresh_package_sha256']==digest and capital['capital_package_sha256']==state['installed'][3]['sha256'] and capital['result']['status']=='SUCCEEDED'
assert capital['before']==capital['after'] and capital['previous_region_before']==capital['previous_region_after'] and capital['buildings_before']==capital['buildings_after'] and capital['previous_buildings_before']==capital['previous_buildings_after']
assert capital['caravans_before']==capital['caravans_after'] and capital['pools_before']==capital['pools_after'] and capital['convoy_pool_before']==capital['convoy_pool_after'] and capital['refresh_sequence_before']==capital['refresh_sequence_after']
lord=read('lord-lore-final');assert len(lord['before'])==2 and len(lord['after'])==3 and lord['target']==lord['ui_target'] and lord['result']['status']=='SUCCEEDED' and lord['sequence_after']==lord['sequence_before']+1 and lord['others_before']==lord['others_after'] and lord['owned_before']==lord['owned_after']
for pair in lord['result']['pairs']:assert lord['default_skills_before'][str(pair['old'])]==lord['default_skills_after'][str(pair['new'])]
hire=read('lord-native-hire');assert hire['forces_after']==hire['forces_before']+1 and hire['region']==hire['capital']==capital['capital_after'] and hire['rank']==1
empty=read('empty-convoy-pool');assert empty['offered_count']==empty['pool_count']==0 and empty['sequence_before']==empty['sequence_after']
assert 'FINAL_COLD_PACK '+digest in (r/'native/native.log').read_text()
sys.path.insert(0,str(repo/'tools'));from pack import read_pack
files=read_pack((repo/'mods/recruitment_refresh/build/xatw3_campaign_utilities.pack').read_bytes())
for path in (repo/'mods/recruitment_refresh/src').rglob('*'):
 if path.is_file():assert files[path.relative_to(repo/'mods/recruitment_refresh/src').as_posix()]==path.read_bytes()
result={'status':'PASS','mod_id':'recruitment_refresh','version':'0.3.3','package_sha256':digest,'joint_capital_pack_sha256':state['installed'][3]['sha256'],'cold_package_verified':True,'production_hot_reload_credited':False,'tracked_payload_matches_pack':True,'cases':['convoy_button','original_hire','idle_protection','capital_transaction','dispatch_after_capital','active_protection','refreshed_hire','empty_pool','lord_lore_restore','lord_native_hire']}
(r/'verification-final.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
