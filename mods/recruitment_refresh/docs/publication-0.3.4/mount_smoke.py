from common import *
import argparse,os,shutil,re
from live_probe import fixture
parser=argparse.ArgumentParser();parser.add_argument('--mod',required=True,choices=['recruitment_refresh']);parser.parse_args()
require_offline('offline-before-subscriber-mount.json');no_games()
download=read(ROOT/'subscription-download.json');accepted=read(PROJECT.root/'docs/acceptance-results-0.3.4.json')
source=Path(download['pack']);expected=accepted['release_pack_sha256']
if sha(source)!=expected:raise RuntimeError('Subscription bytes changed')
game=DLL.parent;profile=Path(os.environ['APPDATA'])/'The Creative Assembly/Warhammer3';folder=ROOT/'mount';folder.mkdir(exist_ok=False)
targets=[game/'data'/PROJECT.pack_name,game/'data/zz_xatw3_release_mount.pack',game/'data/memreader_plus.pack']
if any(p.exists() for p in targets):raise RuntimeError('An installation target is already present')
dependency=game.parent.parent/'workshop/content/1142710/3811098873/memreader_plus.pack'
if sha(dependency)!='0c751ae032bb51718c267cd06b67c648035367c13338763edf9a689be4ce9ae1':raise RuntimeError('Dependency differs from native acceptance')
prefs=profile/'scripts/preferences.script.txt';user=profile/'scripts/user.script.txt'
original=prefs.read_bytes();(folder/'preferences-original.bin').write_bytes(original)
user_original=user.read_bytes() if user.exists() else None
if user_original is not None:(folder/'user-original.bin').write_bytes(user_original)
state={'status':'PREPARING','mod_id':'recruitment_refresh','source':str(source),'source_sha256':expected,'installation_method':'byte-identical copy from verified real subscription folder','frontend_mount_only':True,'business_retest':False,'installed':[]}
save('mount-session.json',state);process=None;started=None;success=False
try:
 shutil.copy2(source,targets[0]);state['installed'].append({'path':str(targets[0]),'sha256':sha(targets[0])});save('mount-session.json',state)
 fixture(targets[1],folder,source,include_production=False);state['installed'].append({'path':str(targets[1]),'sha256':sha(targets[1])});save('mount-session.json',state)
 shutil.copy2(dependency,targets[2]);state['installed'].append({'path':str(targets[2]),'sha256':sha(targets[2])});save('mount-session.json',state)
 script='mod "memreader_plus.pack";\nmod "'+PROJECT.pack_name+'";\n';user.write_text(script,encoding='utf-16')
 settings=read(ROOT.parent/'test-graphics-settings.json')['settings'];text=original.decode('utf-8-sig')
 for key,value in settings.items():
  text,n=re.subn(r'(?m)^('+re.escape(key)+r'\s+)[^;]+;',lambda m:m[1]+value+';',text)
  if n!=1:raise RuntimeError('Unknown preference '+key)
 prefs.write_bytes(text.encode('utf-8'))
 identity=accepted['release_identity'];command="assert(string.sub('abcdef',1,3)=='abc')\nassert(require('script.xatw3_release_recruitment_refresh')=='"+identity+"')\nxatw3_test.record('SUBSCRIBED_PACKAGE_MOUNT_PASS "+identity+"')\n"
 (folder/'frontend-command.lua').write_bytes(command.encode())
 require_offline('offline-immediately-before-mount-launch.json')
 env=os.environ.copy();env.update(SteamAppId='1142710',SteamGameId='1142710');si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=4
 process=subprocess.Popen([str(game/'Warhammer3.exe')],cwd=game,env=env,startupinfo=si);started=psutil.Process(process.pid).create_time();state.update(status='RUNNING',pid=process.pid);save('mount-session.json',state);event('subscriber_mount_started',pid=process.pid)
 end=time.monotonic()+180
 while time.monotonic()<end:
  if process.poll() is not None:raise RuntimeError('Game exited before mount readback')
  log=folder/'native.log';text=log.read_text(encoding='utf-8') if log.exists() else ''
  if 'SUBSCRIBED_PACKAGE_MOUNT_PASS '+identity in text and 'COMMAND_RESULT ok=true' in text:success=True;break
  if 'COMMAND_RESULT ok=false' in text or 'COMMAND_COMPILE_ERROR' in text:raise RuntimeError('Frontend identity assertion failed: '+text[-600:])
  time.sleep(.5)
 if not success:raise TimeoutError('Subscribed-package mount timed out')
 event('subscriber_mount_verified',release_identity=identity)
finally:
 if process and process.poll() is None:
  owned=psutil.Process(process.pid)
  if owned.create_time()!=started or Path(owned.exe()).resolve()!=(game/'Warhammer3.exe').resolve():raise RuntimeError('Game process identity changed')
  owned.terminate();owned.wait(20)
 for item in state['installed']:
  p=Path(item['path']).resolve()
  if p.parent!=(game/'data').resolve() or sha(p)!=item['sha256']:raise RuntimeError('Owned test file changed; preserve for review')
  p.unlink()
 if user_original is None:user.unlink(missing_ok=True)
 else:user.write_bytes(user_original)
 prefs.write_bytes(original)
 if prefs.read_bytes()!=original:raise RuntimeError('Preference restoration mismatch')
 final=require_offline('offline-after-subscriber-mount.json')
 state.update(status='PASS' if success else 'FAILED',cleaned=True,preferences_restored=True,user_script_restored=True,steam_intentionally_offline=True,release_identity=accepted['release_identity'],completed_at_utc=now())
 save('mount-session.json',state)
