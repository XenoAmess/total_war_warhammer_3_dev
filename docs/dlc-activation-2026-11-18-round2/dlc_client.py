from pathlib import Path
from datetime import datetime,timezone
import ctypes as C,json,os,sys,argparse,time
r=Path(__file__).parent;repo=Path.cwd();sys.path.insert(0,str(repo/'tools'));from workshop import account_activity
parser=argparse.ArgumentParser();parser.add_argument('--receipt',type=Path,required=True);parser.add_argument('--activate-owned',action='store_true');args=parser.parse_args()
owner='76561198273714027';activity=account_activity(owner)
if activity['status']!='PUBLIC_PRESENCE_IDLE':raise RuntimeError('Account busy or unknown before SDK initialization')
(r/('account-before-'+args.receipt.stem+'.json')).write_bytes((json.dumps(activity,indent=2)+'\n').encode())
if args.activate_owned and os.environ.get('WH3_DLC_CONTROLLER')!='1':raise RuntimeError('Activation requires the restoring controller')
os.environ.update(SteamAppId='1142710',SteamGameId='1142710')
lib=C.CDLL('C:/SteamLibrary/steamapps/common/Total War WARHAMMER III/steam_api64.dll')
def bind(name,restype,*types):
 fn=getattr(lib,name);fn.restype=restype;fn.argtypes=list(types);return fn
if not bind('SteamAPI_Init',C.c_bool)():raise RuntimeError('Steam API initialization failed')
try:
 apps=bind('SteamAPI_SteamApps_v008',C.c_void_p)();user=bind('SteamAPI_SteamUser_v023',C.c_void_p)();utils=bind('SteamAPI_SteamUtils_v010',C.c_void_p)()
 actual=str(bind('SteamAPI_ISteamUser_GetSteamID',C.c_uint64,C.c_void_p)(user));logged=bind('SteamAPI_ISteamUser_BLoggedOn',C.c_bool,C.c_void_p)(user)
 if actual!=owner or bind('SteamAPI_ISteamUtils_GetAppID',C.c_uint32,C.c_void_p)(utils)!=1142710:raise RuntimeError('Steam owner/application changed')
 if args.activate_owned and not logged:raise RuntimeError('Online activation session unavailable')
 owned=bind('SteamAPI_ISteamApps_BIsSubscribedApp',C.c_bool,C.c_void_p,C.c_uint32)
 installed=bind('SteamAPI_ISteamApps_BIsDlcInstalled',C.c_bool,C.c_void_p,C.c_uint32)
 purchase=bind('SteamAPI_ISteamApps_GetEarliestPurchaseUnixTime',C.c_uint32,C.c_void_p,C.c_uint32)
 count=bind('SteamAPI_ISteamApps_GetDLCCount',C.c_int32,C.c_void_p)(apps)
 if not 0<=count<=1024:raise RuntimeError('Invalid DLC count')
 data=bind('SteamAPI_ISteamApps_BGetDLCDataByIndex',C.c_bool,C.c_void_p,C.c_int32,C.POINTER(C.c_uint32),C.POINTER(C.c_bool),C.c_char_p,C.c_int32)
 catalog={}
 for i in range(count):
  app,available,name=C.c_uint32(),C.c_bool(),C.create_string_buffer(2048)
  if not data(apps,i,C.byref(app),C.byref(available),name,len(name)):raise RuntimeError('DLC enumeration failed')
  catalog[app.value]={'appid':app.value,'name':name.value.decode('utf-8'),'listed_for_wh3':True,'store_available':available.value}
 legacy=json.loads((r.parent/'clawspeaker-acceptance-20261116/pdlc_tables.json').read_text())['rows']
 for row in legacy:catalog.setdefault(row['SteamID'],{'appid':row['SteamID'],'name':row['description'],'listed_for_wh3':False,'source':'installed_game_pdlc_table'})
 store=r/'store-dlc-catalog.json'
 if store.exists():
  for row in json.loads(store.read_text(encoding='utf-8')):
   catalog.setdefault(row['appid'],{'appid':row['appid'],'name':row['name'],'listed_for_wh3':False,'source':'official_store_catalog','store_parent_app':row['store_parent_app']})
 for app in [364360,594570,1142710,1835360,1937780,2059190,2358720,2398540,2891700,4399460,617870]:catalog.setdefault(app,{'appid':app,'name':None,'listed_for_wh3':False,'source':'prior_blocker_or_base_app'})
 progress=bind('SteamAPI_ISteamApps_GetDlcDownloadProgress',C.c_bool,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64))
 requests=[]
 for app,row in catalog.items():
  row.update(owned=bool(owned(apps,app)),installed=bool(installed(apps,app)))
  if row['owned']:row['earliest_purchase_unix']=purchase(apps,app)
  done,total=C.c_uint64(),C.c_uint64();active=progress(apps,app,C.byref(done),C.byref(total));row['downloading']=bool(active)
  if active:row.update(bytes_downloaded=done.value,bytes_total=total.value)
  if args.activate_owned and row['listed_for_wh3'] and row['owned'] and not row['installed']:
   bind('SteamAPI_ISteamApps_InstallDLC',None,C.c_void_p,C.c_uint32)(apps,app);requests.append(app)
 result={'schema_version':1,'machine_id':'pc-20260924rtuf-f11af23c08','observed_at_utc':datetime.now(timezone.utc).isoformat(),'owner':owner,'logged_on':bool(logged),'current_app':1142710,
  'app_build_id':bind('SteamAPI_ISteamApps_GetAppBuildId',C.c_int32,C.c_void_p)(apps),'enumerated_count':count,'install_requests':requests,'dlc':sorted(catalog.values(),key=lambda x:x['appid'])}
 args.receipt.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 print(json.dumps({'receipt':str(args.receipt),'logged_on':bool(logged),'owned_count':sum(x['owned'] for x in catalog.values()),'missing_installed':[x['appid'] for x in catalog.values() if x['owned'] and x['listed_for_wh3'] and not x['installed']],'install_requests':requests}))
finally:bind('SteamAPI_Shutdown',None)()
