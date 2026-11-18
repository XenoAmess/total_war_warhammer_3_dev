from common import *
import os,re,argparse
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args()
if set(a.mod)!={'recruitment_refresh','move_capital'}:raise RuntimeError('Explicitly select both Mods')
def inventory(name,activate=False):
 argv=[sys.executable,str(ROOT/'dlc_client.py'),'--receipt',str(ROOT/name)]
 if activate:argv.append('--activate-owned')
 result=subprocess.run(argv,cwd=REPO,env={**os.environ,'WH3_DLC_CONTROLLER':'1'},capture_output=True,text=True,timeout=75)
 with (ROOT/'sdk.log').open('ab') as log:log.write((now()+' '+name+'\n'+result.stdout+'\n'+result.stderr+'\n').encode('utf-8'))
 if result.returncode:raise RuntimeError('DLC SDK child failed: '+result.stderr[-1200:])
 event('dlc_inventory',receipt=name,summary=result.stdout[-500:])
def snapshot(name):
 result=subprocess.run([sys.executable,str(ROOT/'cef_read.py'),str(ROOT/'download_state.js')],capture_output=True,text=True,timeout=15)
 if result.returncode:raise RuntimeError('Download state query failed: '+result.stderr[-800:])
 data=json.loads(result.stdout);save(name,data);return data
def manifest():
 text=Path('C:/SteamLibrary/steamapps/appmanifest_1142710.acf').read_text(encoding='utf-8')
 keys=['StateFlags','buildid','TargetBuildID','UpdateResult','BytesToDownload','BytesDownloaded','BytesToStage','BytesStaged','AutoUpdateBehavior']
 return {key:(re.search(r'"'+key+r'"\s+"([^"]*)"',text)[1] if re.search(r'"'+key+r'"\s+"([^"]*)"',text) else None) for key in keys}
no_games();idle('account-before-restart.json');require_offline('offline-before-online-stage.json');save('manifest-before.json',manifest())
custody=False
try:
 custody=True;graceful_shutdown();hidden([str(STEAM_EXE),'-silent','-cef-enable-debugging']);event('controlled_client_starting')
 inspect_ready(75)
 if not wait_native_offline(25):raise RuntimeError('Controlled client offline readiness timed out')
 require_offline('controlled-startup-offline.json')
 idle('account-before-online.json');control('online')
 deadline=time.monotonic()+35
 while time.monotonic()<deadline:
  if inspect_ready(15)['offline'] is False:break
  time.sleep(.5)
 else:raise RuntimeError('Online readback unavailable')
 time.sleep(4);event('online_license_sync')
 inventory('dlc-online-activation.json',True)
 stable=0;deadline=time.monotonic()+900;iteration=0
 while time.monotonic()<deadline:
  state=snapshot('download-state-'+str(iteration)+'.json');m=manifest();save('manifest-progress.json',m)
  event('download_state',manifest=m,computed=state['value'].get('computed'))
  v=state['value'];o=v.get('overview',{});c=v.get('computed',{})
  pending=any(c.get(k) is True for k in ['BIsDownloading','BIsUpdating','BNeedsUpdate','BIsUpdateRequired']) or any(o.get(k) is True for k in ['update_available','is_downloading','is_updating'])
  if m['StateFlags']=='4' and m['TargetBuildID'] in ('0',None) and not pending:stable+=1
  else:stable=0
  if stable>=3:break
  iteration+=1;time.sleep(5)
 else:raise TimeoutError('Required game download not completed; state retained')
 save('manifest-after.json',manifest());event('online_operations_finished')
finally:
 if custody:restore()
