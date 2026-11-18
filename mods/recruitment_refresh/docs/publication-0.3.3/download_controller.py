from common import *
import os,argparse
from workshop import validate_acceptance
parser=argparse.ArgumentParser();parser.add_argument('--mod',required=True,choices=['recruitment_refresh']);args=parser.parse_args()
validate_acceptance(PROJECT.pack_path,PROJECT.root/'docs/acceptance-results-0.3.3.json',PROJECT)
no_games();save('public-before-verification.json',public_details());idle('account-before-verification-restart.json');require_offline('offline-before-verification.json')
custody=False;code=1
try:
 custody=True;graceful_shutdown();hidden([str(STEAM_EXE),'-silent','-cef-enable-debugging']);event('controlled_client_starting')
 inspect_ready(75)
 if not wait_native_offline(25):raise RuntimeError('Controlled startup native offline readiness timed out')
 require_offline('controlled-startup-offline.json')
 idle('account-before-verification-online.json');control('online')
 end=time.monotonic()+35
 while time.monotonic()<end:
  state=inspect_ready(15)
  if state['offline'] is False:break
  time.sleep(.5)
 else:raise RuntimeError('Online mode did not read back')
 time.sleep(4);idle('account-before-verification-child.json');event('upload_child_starting')
 with (ROOT/'verify-child.log').open('wb') as log:
  child=subprocess.run([sys.executable,str(ROOT/'download_child.py'),'--mod',args.mod],cwd=REPO,env={**os.environ,'WH3_RELEASE_CONTROLLER':'1'},stdout=log,stderr=subprocess.STDOUT)
 code=child.returncode;event('upload_child_exited',exit_code=code)
finally:
 if custody:restore()
 event('controller_complete',exit_code=code)
sys.exit(code)
