from common import *
import os,argparse,ctypes as C
from workshop import publish,validate_acceptance
from workshop_metadata import build_launcher_metadata
from workshop_launcher import query_launcher_metadata,owned_values
parser=argparse.ArgumentParser();parser.add_argument('--mod',required=True,choices=['recruitment_refresh']);args=parser.parse_args()
if os.environ.get('WH3_RELEASE_CONTROLLER')!='1':raise RuntimeError('Use the offline restoration controller')
acceptance=PROJECT.root/'docs/acceptance-results-0.3.4.json';validate_acceptance(PROJECT.pack_path,acceptance,PROJECT)
before=read(PROJECT.root/'workshop/publication-state.json')
if before.get('uploaded_version')!='0.3.3' or before.get('status')!='PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED':raise RuntimeError('Do not replay an uploaded or uncertain update')
time.sleep(2);idle('account-before-publisher-sdk.json');time.sleep(2);event('upload_begin',version=PROJECT.metadata['version'])
state=publish(DLL,PROJECT.pack_path,acceptance,PROJECT.root/'workshop/publication-state.json',PROJECT.build_dir/'preview.png',OWNER,project=PROJECT)
save('upload.json',state);event('upload_complete',item_id=state['item_id'],sha256=state['pack_sha256'])
event('online_upload_complete')
