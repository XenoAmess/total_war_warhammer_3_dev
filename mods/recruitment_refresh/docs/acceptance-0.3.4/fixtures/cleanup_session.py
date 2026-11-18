from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,psutil,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args();assert set(a.mod)=={'recruitment_refresh','move_capital'}
r=Path(__file__).parent;repo=Path.cwd();s=json.loads((r/'session.json').read_text());game=Path('C:/SteamLibrary/steamapps/common/Total War WARHAMMER III').resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if psutil.pid_exists(s['pid']):
 proc=psutil.Process(s['pid']);assert Path(proc.exe()).resolve()==game/'Warhammer3.exe' and proc.create_time()==s['process_birth'];proc.terminate();proc.wait(20)
assert not any(p.info['name'].lower()=='warhammer3.exe'for p in psutil.process_iter(['name']))
removed=[]
for item in s['installed']:
 target=Path(item['path']).resolve();assert target.parent==game/'data' and target.name in ['xatw3_campaign_utilities.pack','xatw3_move_capital.pack','zz_xatw3_acceptance.pack','memreader_plus.pack']
 assert sha(target)==item['sha256'];target.unlink();removed.append(str(target))
user=Path(s['user']);expected='mod "memreader_plus.pack";\nmod "xatw3_campaign_utilities.pack";\nmod "xatw3_move_capital.pack";'
assert user.read_text(encoding='utf-16').strip()==expected
if s['user_existed']:user.write_bytes((r/'user-script-original.bin').read_bytes())
else:user.unlink()
prefs=Path(s['prefs']);original=(r/'preferences-original.bin').read_bytes();prefs.write_bytes(original);assert prefs.read_bytes()==original
receipt=r/('offline-final-'+str(time.time_ns())+'.json');subprocess.run([sys.executable,str(repo/'mods/recruitment_refresh/docs/publication-0.3.1/steam_release_probe.py'),'--receipt',str(receipt)],check=True,capture_output=True);offline=json.loads(receipt.read_text());assert offline['status']=='offline' and offline['offline_mode'] is True
assert '-cef-enable-debugging' not in psutil.Process(offline['steam']['pid']).cmdline()
result={'status':'PASS','observed_at_utc':datetime.now(timezone.utc).isoformat(),'mods':['recruitment_refresh','move_capital'],'removed_owned_packs':removed,'preferences_restored':True,'user_script_restored':True,'game_stopped':True,'save_files_deleted':0,'steam_offline':True,'offline_receipt':str(receipt),'preferences_original_sha256':hashlib.sha256(original).hexdigest()}
(r/'cleanup.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
