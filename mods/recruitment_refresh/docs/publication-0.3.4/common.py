from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,time,hashlib,psutil,urllib.request,urllib.parse
ROOT=Path(__file__).parent;REPO=Path.cwd();OWNER='76561198273714027';STEAM_EXE=Path('D:/steam/steam.exe');DLL=Path('C:/SteamLibrary/steamapps/common/Total War WARHAMMER III/steam_api64.dll')
CONTROL=ROOT.parent/'launcher-both-followup-20261031T141338Z/steam_control_force.py'
PROBE=REPO/'mods/recruitment_refresh/docs/publication-0.3.1/steam_release_probe.py'
sys.path.insert(0,str(REPO/'tools'))
from project import load_project
from workshop import Steam, _html_account_activity
import workshop as workshop_module
import urllib.error
def account_activity(owner):
 # Every admission still performs a new strict full-profile read. Space HTTP reads
 # across the controller/children; a rate-limit failure never becomes idle evidence.
 for attempt in range(3):
  stamp=ROOT/'presence-request-time.json'
  if stamp.exists():
   previous=json.loads(stamp.read_text(encoding='utf-8'))['started_epoch']
   delay=max(0,15-(time.time()-previous))
   if delay:time.sleep(min(delay,30))
  stamp.write_bytes((json.dumps({'started_epoch':time.time()})+'\n').encode())
  try:return _html_account_activity(owner,datetime.now(timezone.utc).isoformat(),language='schinese')
  except urllib.error.HTTPError as error:
   if error.code!=429:raise
   path=ROOT/'presence-http-retries.json'
   records=json.loads(path.read_text(encoding='utf-8'))if path.exists()else[]
   records.append({'attempt':attempt+1,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':429,'action':'wait for fresh public presence; no SDK initialization'})
   path.write_bytes((json.dumps(records,indent=2)+'\n').encode())
   if attempt==2:raise
   time.sleep(20+10*attempt)
workshop_module.account_activity=account_activity
PROJECT=load_project('recruitment_refresh')
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,value):
 (ROOT/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def event(stage,**fields):print(json.dumps({'stage':stage,'utc':now(),**fields},ensure_ascii=False),flush=True)
def steam_processes():return [p for p in psutil.process_iter(['name']) if p.info['name'].lower()=='steam.exe']
def no_games():
 if any(p.info['name'].lower() in ['warhammer3.exe','ck3.exe'] for p in psutil.process_iter(['name'])):raise RuntimeError('Game running; do not restart Steam')
def hidden(argv):
 si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 return subprocess.Popen(argv,startupinfo=si)
def control(action):
 result=subprocess.run([sys.executable,str(CONTROL),action],capture_output=True,text=True,timeout=13)
 with (ROOT/'control.log').open('ab') as f:f.write((now()+' '+action+' '+result.stdout+'\n'+result.stderr+'\n').encode('utf-8'))
 if result.returncode:raise RuntimeError('Control failed: '+result.stderr[-400:])
 rows=[json.loads(s) for s in result.stdout.splitlines() if s.startswith('{')]
 if not rows or not rows[0].get('state'):raise RuntimeError('No live CEF state')
 return rows[0]['state']
def inspect_ready(timeout=60):
 end=time.monotonic()+timeout;last=None
 while time.monotonic()<end:
  try:
   current=control('inspect')
   if current.get('steamid')==OWNER:return current
   if current.get('steamid') not in (None,'0'):raise RuntimeError('Steam account changed')
  except (subprocess.TimeoutExpired,RuntimeError) as error:
   if 'account changed' in str(error):raise
   last=repr(error)
  time.sleep(1)
 raise TimeoutError('Owned Steam context unavailable: '+str(last))
def idle(name):
 activity=account_activity(OWNER);save(name,activity)
 if activity['status']!='PUBLIC_PRESENCE_IDLE':raise RuntimeError('Account busy/unknown; stay offline: '+json.dumps(activity))
 return activity
def probe(name):
 p=ROOT/(Path(name).stem+'-'+str(time.time_ns())+'.json');started=datetime.now(timezone.utc)
 result=subprocess.run([sys.executable,str(PROBE),'--receipt',str(p)],capture_output=True,text=True,timeout=12)
 if result.returncode:raise RuntimeError('Offline query failed: '+result.stderr[-300:])
 state=read(p)
 if datetime.fromisoformat(state['observed_at_utc'].replace('Z','+00:00'))<started:raise RuntimeError('Stale offline evidence')
 save(name,state);return state
def require_offline(name):
 state=probe(name)
 if state.get('status')!='offline' or state.get('offline_mode') is not True:raise RuntimeError('Intentional offline not confirmed')
 return state
def graceful_shutdown():
 no_games()
 for p in steam_processes():
  if Path(p.exe()).resolve()!=STEAM_EXE.resolve():raise RuntimeError('Unexpected Steam executable')
 hidden([str(STEAM_EXE),'-shutdown']);end=time.monotonic()+40
 while steam_processes():
  if time.monotonic()>end:raise TimeoutError('Graceful Steam shutdown incomplete; no force termination')
  time.sleep(.5)
def wait_native_offline(seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  state=probe('restore-progress.json')
  if state.get('status')=='offline' and state.get('offline_mode') is True:return state
  time.sleep(1)
 return None
def restore():
 event('restoring_intentional_offline');confirmed=None
 try:
  inspect_ready(18);control('offline');confirmed=wait_native_offline(12)
 except (RuntimeError,subprocess.TimeoutExpired,TimeoutError) as error:event('offline_control_recovery',error=str(error)[-350:])
 if not confirmed:
  graceful_shutdown();hidden([str(STEAM_EXE),'-silent','-cef-enable-debugging','-offline']);inspect_ready(75)
  control('offline');confirmed=wait_native_offline(25)
 if not confirmed:raise RuntimeError('Controlled Steam intentional offline readback failed')
 graceful_shutdown();hidden([str(STEAM_EXE),'-silent']);time.sleep(30)
 confirmed=wait_native_offline(35)
 if not confirmed:
  # Re-enter the same verified background control route; no screen input.
  graceful_shutdown();hidden([str(STEAM_EXE),'-silent','-cef-enable-debugging','-offline']);inspect_ready(75);control('offline')
  if not wait_native_offline(25):raise RuntimeError('Recovery offline readback failed')
  graceful_shutdown();hidden([str(STEAM_EXE),'-silent']);time.sleep(30);confirmed=wait_native_offline(35)
 if not confirmed:raise RuntimeError('Ordinary Steam offline readback failed')
 time.sleep(3);confirmed=require_offline('final-offline.json')
 processes=steam_processes()
 if len(processes)!=1 or '-cef-enable-debugging' in processes[0].cmdline():raise RuntimeError('Temporary debug mode still active')
 event('intentional_offline_restored',steam_pid=confirmed['steam']['pid'])
def public_details():
 request=urllib.request.Request('https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/',data=urllib.parse.urlencode({'itemcount':'1','publishedfileids[0]':'3830548217'}).encode(),headers={'Cache-Control':'no-cache','User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(request,timeout=20) as response:data=json.load(response)
 rows=data['response']['publishedfiledetails']
 if len(rows)!=1:raise RuntimeError('Unexpected public item count')
 row=rows[0]
 if row['result']!=1 or row['creator']!=OWNER or row['consumer_app_id']!=1142710 or row['publishedfileid']!='3830548217':raise RuntimeError('Public item identity mismatch')
 return row
