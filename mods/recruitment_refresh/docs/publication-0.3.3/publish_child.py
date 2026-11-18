from common import *
import os,argparse,ctypes as C
from workshop import publish,validate_acceptance
from workshop_metadata import build_launcher_metadata
from workshop_launcher import query_launcher_metadata,owned_values
parser=argparse.ArgumentParser();parser.add_argument('--mod',required=True,choices=['recruitment_refresh']);args=parser.parse_args()
if os.environ.get('WH3_RELEASE_CONTROLLER')!='1':raise RuntimeError('Use the offline restoration controller')
acceptance=PROJECT.root/'docs/acceptance-results-0.3.3.json';validate_acceptance(PROJECT.pack_path,acceptance,PROJECT)
idle('account-before-publisher-sdk.json');event('upload_begin',version=PROJECT.metadata['version'])
state=publish(DLL,PROJECT.pack_path,acceptance,PROJECT.root/'workshop/publication-state.json',PROJECT.build_dir/'preview.png',OWNER,project=PROJECT)
save('upload.json',state);event('upload_complete',item_id=state['item_id'],sha256=state['pack_sha256'])
idle('account-before-download-sdk.json');steam=Steam(DLL)
try:
 if steam.steam_id!=OWNER:raise RuntimeError('Steam account changed')
 item=int(state['item_id']);metadata=query_launcher_metadata(steam,item);expected=build_launcher_metadata(PROJECT)
 if not all(owned_values(metadata,k)==[v] for k,v in expected.items()):raise RuntimeError('Remote launcher metadata mismatch')
 save('remote-launcher-metadata.json',metadata)
 flags=steam.bind('SteamAPI_ISteamUGC_GetItemState',C.c_uint32,C.c_void_p,C.c_uint64)
 if not flags(steam.ugc,item)&1:raise RuntimeError('Real subscription missing')
 download=steam.bind('SteamAPI_ISteamUGC_DownloadItem',C.c_bool,C.c_void_p,C.c_uint64,C.c_bool)
 info=steam.bind('SteamAPI_ISteamUGC_GetItemInstallInfo',C.c_bool,C.c_void_p,C.c_uint64,C.POINTER(C.c_uint64),C.c_char_p,C.c_uint32,C.POINTER(C.c_uint32))
 if not download(steam.ugc,item,True):raise RuntimeError('Download request rejected')
 end=time.monotonic()+150
 while time.monotonic()<end:
  steam.pump();current=flags(steam.ugc,item)
  if current&1 and current&4 and not current&(8|16|32):
   size,stamp,folder=C.c_uint64(),C.c_uint32(),C.create_string_buffer(4096)
   if info(steam.ugc,item,C.byref(size),folder,len(folder),C.byref(stamp)):
    path=Path(folder.value.decode())/PROJECT.pack_name
    if path.is_file() and sha(path)==state['pack_sha256']:
     save('subscription-download.json',{'status':'PASS','mod_id':PROJECT.id,'item_id':state['item_id'],'flags':current,'subscribed':True,'installed':True,'sha256':sha(path),'bytes':path.stat().st_size,'pack':str(path),'observed_at_utc':now()})
     event('subscription_download_verified',sha256=sha(path));break
  time.sleep(.2)
 else:raise TimeoutError('Subscription did not settle to exact accepted bytes')
finally:steam.shutdown()
event('online_operations_complete')
