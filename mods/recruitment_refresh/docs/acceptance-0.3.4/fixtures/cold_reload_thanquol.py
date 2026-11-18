from pathlib import Path
import argparse,hashlib,json,os,psutil,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args();assert set(a.mod)=={'recruitment_refresh','move_capital'}
r=Path(__file__).parent;repo=Path.cwd()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_bytes((json.dumps(v,indent=2)+'\n').encode('utf-8'))
s=read(r/'session.json');expected=read(r/'evidence-thanq-034/thanquol-final-snapshot.json')
assert expected['status']=='PASS'
savedir=Path(os.environ['APPDATA'],'The Creative Assembly/Warhammer3/save_games')
saves=list(savedir.glob('xatw3_round2_thanquol_final034_20261118*.save'));assert len(saves)==1
save=saves[0];size=save.stat().st_size;assert size>1000000
time.sleep(1);assert save.stat().st_size==size
assert max(savedir.glob('*.save'),key=lambda p:p.stat().st_mtime_ns)==save
write(r/'checkpoint-thanquol-final.json',{'source':str(save),'bytes':size,'sha256':sha(save)})
for item in s['installed']:assert sha(Path(item['path']))==item['sha256']
for name in ['command.lua','ui-command.lua','frontend-command.lua']:assert not(r/'native'/name).exists()
for kind in ['corruptor','deceiver','warpseer','warbringer']:assert read(r/'evidence-thanq-034'/('verminlord-native-hire-'+kind+'.json'))['status']=='PASS'
def lua(v):
 if v is None:return'nil'
 if isinstance(v,bool):return'true'if v else'false'
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
 if isinstance(v,(int,float)):return str(v)
 if isinstance(v,list):return'{'+','.join(lua(x)for x in v)+'}'
 return'{'+','.join('['+lua(str(k))+']='+lua(val)for k,val in v.items())+'}'
verify="local expected="+lua(expected)+"\n"+r'''
local function equal(a,b,path)
 assert(type(a)==type(b),'Saved type changed: '..path)
 if type(a)~='table'then assert(a==b,'Saved value changed: '..path);return end
 for k,v in pairs(a)do equal(v,b[k],path..'.'..tostring(k))end
 for k in pairs(b)do assert(a[k]~=nil,'Unexpected saved key: '..path..'.'..tostring(k))end
end
local f=cm:get_local_faction();local rr=xatw3_campaign_utilities.runtime;local cap=xatw3_move_capital.runtime
equal(expected.refresh_state,rr.state,'refresh_state')
equal(expected.capital_state,cap.state,'capital_state')
equal(expected.pools,xatw3_test.others(''),'pool_fingerprints')
assert(cap.capital(f:name())==expected.capital and cm:model():turn_number()==expected.turn)
for _,v in pairs(expected.actors)do
 local actor=cm:get_family_member_by_cqi(v.id):character();assert(not actor:is_null_interface())
 assert(actor:rank()==v.rank and actor:character_subtype_key()==v.subtype and actor:region():name()==v.region)
end
xatw3_test.save('final-refreshed-save-reload',{status='PASS',package_sha256=xatw3_test.package_sha,faction=f:name(),capital=cap.capital(f:name()),turn=cm:model():turn_number(),both_full_mod_states_unchanged=true,all_pool_fingerprints_unchanged=true,hired_verminlord_actors_preserved=expected.actors,source_save_sha256=SAVE_HASH})
xatw3_test.record('FINAL_REFRESHED_SAVE_RELOAD_PASS')
'''
verify=verify.replace('SAVE_HASH',lua(sha(save)))
(r/'verify_thanquol_reload.lua').write_bytes(verify.encode('utf-8'))
proc=psutil.Process(s['pid']);assert Path(proc.exe()).resolve()==Path(s['game_exe']).resolve()and proc.create_time()==s['process_birth']
proc.terminate();proc.wait(25)
(r/'native/native.log').rename(r/'native-thanq-034.log')
(r/'evidence-thanq-reload-034').mkdir(exist_ok=False)
(r/'evidence_helpers_thanq_reload.lua').write_bytes((r/'evidence_helpers_thanq.lua').read_bytes().replace(b'/evidence-thanq-034/',b'/evidence-thanq-reload-034/'))
bootstrap=(r/'bootstrap_thanq.lua').read_text(encoding='utf-8').replace('evidence_helpers_thanq.lua','evidence_helpers_thanq_reload.lua')+'\n'+verify
(r/'native/command.lua').write_bytes(bootstrap.encode('utf-8'))
(r/'native/frontend-command.lua').write_bytes((r/'resume_034.lua').read_bytes())
receipt=r/('offline-before-refreshed-reload-'+str(time.time_ns())+'.json')
subprocess.run([sys.executable,str(repo/'mods/recruitment_refresh/docs/publication-0.3.1/steam_release_probe.py'),'--receipt',str(receipt)],check=True,capture_output=True)
proof=read(receipt);assert proof.get('status')=='offline'and proof.get('offline_mode')is True
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=4
new=subprocess.Popen([s['game_exe']],cwd=Path(s['game_exe']).parent,env={**os.environ,'SteamAppId':'1142710','SteamGameId':'1142710'},startupinfo=si)
s.setdefault('previous_pids',[]).append(s['pid']);s.update(pid=new.pid,process_birth=psutil.Process(new.pid).create_time(),phase='final-refreshed-reload-034',persistence_offline_receipt=str(receipt))
write(r/'session.json',s);print(json.dumps({'pid':new.pid,'offline':True,'save_sha256':sha(save),'cold':True}))
