from common import *
import argparse
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
docs=PROJECT.root/'docs';dest=docs/'publication-0.3.4'
accepted=read(docs/'acceptance-results-0.3.4.json');prepared=read(ROOT/'prepared.json')
public=read(ROOT/'public-verification.json');download=read(ROOT/'subscription-download.json');mount=read(ROOT/'mount-session.json');row=read(ROOT/'public-after.json')
state=read(PROJECT.root/'workshop/publication-state.json');expected=accepted['release_pack_sha256']
assert public['status']=='PASS'and mount['status']=='PASS'and mount['cleaned']
assert prepared['pack_sha256']==public['pack_sha256']==mount['source_sha256']==expected==sha(PROJECT.pack_path)==sha(Path(download['pack']))
assert mount['release_identity']==accepted['release_identity']and state['uploaded_version']=='0.3.4'
assert row['creator_app_id']==1142710 and row['visibility']==0 and row['description'].strip()==(PROJECT.root/'workshop/description.bbcode').read_text(encoding='utf-8').strip()
assert sha(PROJECT.root/'workshop/change-notes.txt')==prepared['change_notes_sha256']
offline=require_offline('final-after-all-checks.json');no_games()
assert all('-cef-enable-debugging'not in p.cmdline()for p in steam_processes())
def write(path,data):path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
dest.mkdir(exist_ok=True)
names=['prepared.json','publication-state-before.json','account-initial.json','account-before-restart.json','account-before-online.json','account-before-child.json','account-before-publisher-sdk.json','account-before-verification-restart.json','account-before-verification-online.json','account-before-verification-child.json','account-before-download-sdk.json','offline-initial.json','offline-before-publication.json','offline-before-verification.json','final-offline.json','offline-after-subscriber-mount.json','final-after-all-checks.json','subscription-download.json','remote-launcher-metadata.json','public-before.json','public-after.json','public-pages-check.json','public-verification.json','images.json','mount-session.json','local-model-status.json','presence-route-verification.json','presence-http-retries.json','public-page-retries.json','upload.json']
for name in names:
 source=ROOT/name
 if source.exists():write(dest/name,read(source))
attempts=[]
for folder in sorted(ROOT.glob('attempt*-*')):
 if not folder.is_dir()or not(folder/'failure.json').exists():continue
 target=dest/folder.name;target.mkdir(exist_ok=True)
 for source in folder.glob('*.json'):write(target/source.name,read(source))
 attempts.append({'folder':folder.name,**read(folder/'failure.json')})
for source in ROOT.glob('*.py'):(dest/source.name).write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
for source,name in [(ROOT/'mount/native.log','subscriber-mount.log'),(ROOT/'child.log','publisher.log'),(ROOT/'verify-child.log','subscription-verifier.log'),(ROOT/'control.log','steam-control.log')]:
 if source.exists():(dest/name).write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
published_at=datetime.fromtimestamp(row['time_updated'],timezone.utc).isoformat();verified_at=now()
record={'schema_version':1,'mod_id':PROJECT.id,'version':'0.3.4','machine_id':offline['machine_id'],'item_id':'3830548217','url':'https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217','status':'PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED','source_commit':prepared['source_commit'],'publication_input_commit':prepared['publication_input_commit'],'pack_sha256':expected,'pack_bytes':PROJECT.pack_path.stat().st_size,'release_identity':accepted['release_identity'],'uploaded_at_utc':published_at,'verified_at_utc':verified_at,'user_instruction':'发布到创意工坊','release_scope':accepted['acceptance_scope'],'acceptance_file':'acceptance-results-0.3.4.json','description_sha256':sha(PROJECT.root/'workshop/description.bbcode'),'change_notes_sha256':sha(PROJECT.root/'workshop/change-notes.txt'),'account_occupancy':'Fresh strict public full-profile identity/privacy/presence checks before restart, online mode and each SDK session; unknown or busy never admitted. Direct schinese route and read-only HTTP backoff avoid redundant mini/XML requests. No user-confirmation substitution or account takeover.','pre_upload_failures':attempts,'upload_count':1,'download':download,'public_verification':public,'public_pages':read(ROOT/'public-pages-check.json'),'launcher_metadata':read(ROOT/'remote-launcher-metadata.json'),'images':read(ROOT/'images.json'),'subscriber_mount':mount,'subscriber_mount_scope':'Frontend release identity loaded from a byte-identical copy of the verified real Workshop subscription download; no repeat business acceptance credit.','limitations':accepted['limitations'],'steam_final_mode':'offline','steam_final_receipt':offline,'temporary_steam_debugging_removed':True,'test_files_and_preferences_restored':True,'offline_probe_implementation':'publication-0.3.1/steam_release_probe.py','offline_probe_sha256':sha(PROBE),'runtime_root':str(ROOT),'local_model':read(ROOT/'local-model-status.json'),'evidence':[{'file':p.relative_to(docs).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(dest.rglob('*'))if p.is_file()]}
write(docs/'workshop-publication-0.3.4.json',record)
accepted.update(release_status=record['status'],L4='PASS',workshop_upload_performed=True,publication_record='workshop-publication-0.3.4.json',published_at_utc=published_at,verified_at_utc=verified_at,subscription_mount_scope=record['subscriber_mount_scope'])
write(docs/'acceptance-results-0.3.4.json',accepted);write(docs/'acceptance-results.json',accepted)
state.update(status=record['status'],version='0.3.4',uploaded_version='0.3.4',pack_sha256=expected,pack_bytes=record['pack_bytes'],uploaded_at_utc=published_at,verified_at_utc=verified_at,downloaded_pack_bytes=record['pack_bytes'],downloaded_pack_sha256=expected,steam_final_mode='offline',last_download=download,last_publication_record='docs/workshop-publication-0.3.4.json',release_acceptance={**{k:'PASS'for k in ['L0','L1','L2','L3','L4']},'scope':accepted['acceptance_scope'],'release_pack_sha256':expected},steam_final_offline_receipt=offline,final_offline_receipt={'path':str(ROOT/'final-after-all-checks.json'),'sha256':sha(ROOT/'final-after-all-checks.json')},public_details=row,subscriber_mount=mount)
write(PROJECT.root/'workshop/publication-state.json',state)
report=read(docs/'dlc-compatibility-20261118-round2.json');report.update(release_status=record['status'],workshop_upload_performed_during_native_acceptance=False,workshop_upload_performed=True,publication_followup={'status':record['status'],'publication_record':'workshop-publication-0.3.4.json','verified_at_utc':verified_at,'accepted_package_unchanged':True});write(docs/'dlc-compatibility-20261118-round2.json',report)
event('release_records_saved',version='0.3.4',item_id='3830548217',pack_sha256=expected)
