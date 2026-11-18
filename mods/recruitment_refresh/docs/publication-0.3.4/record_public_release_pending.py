from common import *
import argparse
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
docs=PROJECT.root/'docs';dest=docs/'publication-0.3.4'
accepted=read(docs/'acceptance-results-0.3.4.json');prepared=read(ROOT/'prepared.json');public=read(ROOT/'public-body-verification.json');row=read(ROOT/'public-after.json');upload=read(ROOT/'upload.json')
assert public['status']=='PUBLIC_METADATA_PASS'and upload['uploaded_version']=='0.3.4'
assert sha(PROJECT.pack_path)==accepted['release_pack_sha256']==prepared['pack_sha256']==upload['pack_sha256']
assert not(ROOT/'subscription-download.json').exists()
no_games();offline=require_offline('offline-after-public-verification.json')
assert all('-cef-enable-debugging'not in p.cmdline()for p in steam_processes())
game=DLL.parent
assert not any((game/'data'/name).exists()for name in [PROJECT.pack_name,'zz_xatw3_release_mount.pack','memreader_plus.pack'])
def write(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
dest.mkdir(exist_ok=True)
selected=['prepared.json','publication-state-before.json','account-before-restart.json','account-before-online.json','account-before-child.json','account-before-publisher-sdk.json','account-before-verification-restart.json','offline-before-publication.json','final-offline.json','offline-after-verification-busy.json','offline-after-public-verification.json','public-after.json','public-pages-check.json','public-body-verification.json','images.json','local-model-status.json','presence-route-verification.json','presence-http-retries.json','post-upload-occupancy-block.json','upload.json']
selected+=['account-busy-game-detail.json']+[p.name for p in ROOT.glob('account-wait-*.json')]
for name in selected:
 source=ROOT/name
 if source.exists():write(dest/name,read(source))
for source in ROOT.glob('account-wait-*.json'):write(dest/source.name,read(source))
for folder in sorted(ROOT.glob('attempt*-*')):
 if folder.is_dir()and(folder/'failure.json').exists():
  target=dest/folder.name;target.mkdir(exist_ok=True)
  for source in folder.glob('*.json'):write(target/source.name,read(source))
for source in ROOT.glob('*.py'):(dest/source.name).write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
for name in ['child.log','control.log']:
 if(ROOT/name).exists():(dest/name).write_bytes((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
published_at=datetime.fromtimestamp(row['time_updated'],timezone.utc).isoformat()
status='PUBLISHED_PUBLIC_DOWNLOAD_VERIFICATION_PENDING'
record={'schema_version':1,'mod_id':PROJECT.id,'version':'0.3.4','status':status,'item_id':'3830548217','url':'https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217','source_commit':prepared['source_commit'],'publication_input_commit':prepared['publication_input_commit'],'pack_sha256':accepted['release_pack_sha256'],'pack_bytes':PROJECT.pack_path.stat().st_size,'release_identity':accepted['release_identity'],'uploaded_at_utc':published_at,'public_verified_at_utc':public['observed_at_utc'],'user_instruction':'发布到创意工坊','upload_count':1,'upload_callback':'PASS','public_verification':public,'description_sha256':prepared['description_sha256'],'change_notes_sha256':prepared['change_notes_sha256'],'public_pages':read(ROOT/'public-pages-check.json'),'images':read(ROOT/'images.json'),'acceptance_file':'acceptance-results-0.3.4.json','acceptance_scope':accepted['acceptance_scope'],'account_occupancy':{'before_upload':'Fresh strict public full-profile idle checks; no account takeover','after_upload':'BUSY: Crusader Kings III reported on another machine; no verification SDK initialized','evidence':'publication-0.3.4/post-upload-occupancy-block.json'},'pending_verification':['Remote launcher metadata readback','Real subscribed package download/hash','Downloaded subscription frontend identity mount'],'native_acceptance_unchanged':True,'limitations':accepted['limitations'],'steam_final_mode':'offline','steam_final_receipt':offline,'temporary_steam_debugging_removed':True,'publication_test_files_installed':False,'publication_game_started':False,'runtime_root':str(ROOT),'local_model':read(ROOT/'local-model-status.json'),'evidence':[{'file':p.relative_to(docs).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(dest.rglob('*'))if p.is_file()]}
write(docs/'workshop-publication-0.3.4.json',record)
accepted.update(release_status=status,L4='PENDING',workshop_upload_performed=True,publication_record='workshop-publication-0.3.4.json',published_at_utc=published_at,public_verified_at_utc=public['observed_at_utc'],publication_pending=record['pending_verification'])
write(docs/'acceptance-results-0.3.4.json',accepted);write(docs/'acceptance-results.json',accepted)
state=read(PROJECT.root/'workshop/publication-state.json')
for old,new in [('last_download','previous_release_download'),('subscriber_mount','previous_release_subscriber_mount')]:
 if old in state:state[new]=state.pop(old)
for name in ['downloaded_pack_bytes','downloaded_pack_sha256']:state.pop(name,None)
state.update(status=status,version='0.3.4',uploaded_version='0.3.4',pack_sha256=accepted['release_pack_sha256'],pack_bytes=record['pack_bytes'],uploaded_at_utc=published_at,public_verified_at_utc=public['observed_at_utc'],last_publication_record='docs/workshop-publication-0.3.4.json',public_details=row,steam_final_mode='offline',steam_final_offline_receipt=offline,verification_pending=record['pending_verification'],release_acceptance={**{key:'PASS'for key in ['L0','L1','L2','L3']},'L4':'PENDING','release_pack_sha256':accepted['release_pack_sha256']})
write(PROJECT.root/'workshop/publication-state.json',state)
report=read(docs/'dlc-compatibility-20261118-round2.json');report.update(release_status=status,workshop_upload_performed_during_native_acceptance=False,workshop_upload_performed=True,publication_followup={'status':status,'publication_record':'workshop-publication-0.3.4.json','accepted_package_unchanged':True,'pending_verification':record['pending_verification']});write(docs/'dlc-compatibility-20261118-round2.json',report)
event('public_release_recorded',status=status,item_id='3830548217')
