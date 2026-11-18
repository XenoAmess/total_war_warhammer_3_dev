from common import *
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--mod',required=True,choices=['recruitment_refresh'])
parser.parse_args()
docs=PROJECT.root/'docs'
dest=docs/'publication-0.3.3'
accepted=read(docs/'acceptance-results-0.3.3.json')
prepared=read(ROOT/'prepared.json')
public=read(ROOT/'public-verification.json')
mount=read(ROOT/'mount-session.json')
download=read(ROOT/'subscription-download.json')
row=read(ROOT/'public-after.json')
expected=accepted['release_pack_sha256']
if (public['status']!='PASS' or mount['status']!='PASS' or not mount['cleaned']
    or sha(PROJECT.pack_path)!=expected or sha(Path(download['pack']))!=expected
    or prepared['pack_sha256']!=expected or public['pack_sha256']!=expected
    or mount['source_sha256']!=expected or mount['release_identity']!=accepted['release_identity']):
    raise RuntimeError('Exact release evidence mismatch')
offline=require_offline('final-after-all-checks.json')
no_games()
for p in steam_processes():
    if '-cef-enable-debugging' in p.cmdline():raise RuntimeError('Temporary Steam debugging still active')
if (row['creator_app_id']!=1142710 or row['visibility']!=0
    or row['description'].strip()!=(PROJECT.root/'workshop/description.bbcode').read_text(encoding='utf-8').strip()):
    raise RuntimeError('Public identity or description mismatch')

def write(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

dest.mkdir(exist_ok=False)
names=['prepared.json','account-initial.json','account-before-restart.json','account-before-online.json',
       'account-before-child.json','account-before-publisher-sdk.json','account-before-download-sdk.json',
       'offline-before-publication.json','final-offline.json','offline-after-subscriber-mount.json',
       'final-after-all-checks.json','subscription-download.json','remote-launcher-metadata.json',
       'public-after.json','public-pages-check.json','public-verification.json','images.json',
       'mount-session.json','local-model-status.json','account-after-publisher-busy.json',
       'account-after-publisher-exit.json','offline-after-upload.json',
       'account-before-verification-restart.json','account-before-verification-online.json',
       'account-before-verification-child.json','offline-before-verification.json',
       'public-page-retries.json','public-standard-check.json']
for name in names:write(dest/name,read(ROOT/name))
for attempt in ['attempt1-pre-online','attempt2-pre-online']:
    for name in ['failure.json','final-offline.json']:
        write(dest/(attempt+'-'+name),read(ROOT/attempt/name))
for name in ['common.py','controller.py','publish_child.py','verify_public.py','mount_smoke.py','prepare_release.py',
             'download_controller.py','download_child.py','finalize_release.py']:
    (dest/name).write_bytes((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
(dest/'subscriber-mount.log').write_bytes((ROOT/'mount/native.log').read_bytes().replace(b'\r\n',b'\n'))
(dest/'publisher.log').write_bytes((ROOT/'child.log').read_bytes().replace(b'\r\n',b'\n'))
(dest/'subscription-verifier.log').write_bytes((ROOT/'verify-child.log').read_bytes().replace(b'\r\n',b'\n'))
(dest/'steam-control.log').write_bytes((ROOT/'control.log').read_bytes().replace(b'\r\n',b'\n'))
published_at=datetime.fromtimestamp(row['time_updated'],timezone.utc).isoformat()
verified_at=now()
record={
    'schema_version':1,'mod_id':PROJECT.id,'version':'0.3.3','item_id':'3830548217',
    'url':'https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217',
    'status':'PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED','source_commit':prepared['source_commit'],
    'publication_input_commit':prepared['publication_input_commit'],
    'pack_sha256':expected,'pack_bytes':PROJECT.pack_path.stat().st_size,
    'release_identity':accepted['release_identity'],'uploaded_at_utc':published_at,'verified_at_utc':verified_at,
    'user_instruction':'发布你的修复至创意工坊。',
    'release_scope':accepted['acceptance_scope'],'acceptance_file':'acceptance-results-0.3.3.json',
    'description_sha256':sha(PROJECT.root/'workshop/description.bbcode'),
    'change_notes_sha256':sha(PROJECT.root/'workshop/change-notes.txt'),
    'account_occupancy':'Fresh public idle checks before restart, online mode, child process, publisher SDK and download SDK; no account takeover.',
    'pre_online_recoveries':[
        {'attempt':'attempt1-pre-online','reason':'CEF disconnected after startup inspection; no online/upload SDK initialization',
         'restored_offline':True},
        {'attempt':'attempt2-pre-online','reason':'Startup native tray state not yet ready; no online/upload SDK initialization',
         'restored_offline':True},
    ],
    'post_upload_recovery':{
        'upload_callback':'PASS; exactly one update submitted',
        'verification_connection_initially_blocked':'Public presence still showed WH3 immediately after publisher shutdown',
        'action':'Restored offline, waited for a fresh public idle receipt, then used a verification-only connection; no repeat upload',
    },
    'public_page_recovery':'English and language-neutral HTML returned HTTP 429; anonymous schinese main and changelog pages subsequently read successfully. Public API description comparison, image hashes and subscription bytes also passed.',
    'download':download,'public_verification':public,'public_pages':read(ROOT/'public-pages-check.json'),
    'launcher_metadata':read(ROOT/'remote-launcher-metadata.json'),'images':read(ROOT/'images.json'),
    'subscriber_mount':mount,
    'subscriber_mount_scope':'Frontend release identity loaded from a byte-identical copy of the actual Workshop subscription download; no repeat business acceptance credit.',
    'limitations':accepted['limitations'],'steam_final_mode':'offline','steam_final_receipt':offline,
    'temporary_steam_debugging_removed':True,'test_files_and_preferences_restored':True,
    'offline_probe_implementation':'publication-0.3.1/steam_release_probe.py',
    'offline_probe_sha256':sha(PROBE),'runtime_root':str(ROOT),
    'local_model':{'configured_model':'qwen38-coder','available':False,'candidate_posts':0,'fallback_used':False,
                   'reason':'Configured endpoint lists only the video model open-h3-2k; owner performed publication preparation and verification.'},
    'evidence':[{'file':p.relative_to(docs).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
                for p in sorted(dest.iterdir()) if p.is_file()],
}
write(docs/'workshop-publication-0.3.3.json',record)
accepted.update(release_status=record['status'],L4='PASS',workshop_upload_performed=True,
                source_commit=prepared['source_commit'],publication_record='workshop-publication-0.3.3.json',
                published_at_utc=published_at,verified_at_utc=verified_at,
                subscription_mount_scope=record['subscriber_mount_scope'])
write(docs/'acceptance-results-0.3.3.json',accepted)
write(docs/'acceptance-results.json',accepted)
state=read(PROJECT.root/'workshop/publication-state.json')
state.update(status=record['status'],version='0.3.3',uploaded_version='0.3.3',pack_sha256=expected,
             pack_bytes=record['pack_bytes'],uploaded_at_utc=published_at,verified_at_utc=verified_at,
             downloaded_pack_bytes=record['pack_bytes'],downloaded_pack_sha256=expected,
             steam_final_mode='offline',last_download=download,
             last_publication_record='docs/workshop-publication-0.3.3.json',
             release_acceptance={**{k:'PASS' for k in ['L0','L1','L2','L3','L4']},
                                 'scope':accepted['acceptance_scope'],'release_pack_sha256':expected},
             steam_final_offline_receipt=offline,
             final_offline_receipt={'path':str(ROOT/'final-after-all-checks.json'),
                                    'sha256':sha(ROOT/'final-after-all-checks.json')},
             public_details=row,subscriber_mount=mount)
write(PROJECT.root/'workshop/publication-state.json',state)
report=read(docs/'dlc-compatibility-20261118.json')
report['release_status_at_acceptance']=report['release_status']
report['release_status']=record['status']
report['workshop_upload_performed_during_native_acceptance']=report['workshop_upload_performed']
report['workshop_upload_performed']=True
report['publication_followup']={'status':record['status'],'publication_record':'workshop-publication-0.3.3.json',
                                'verified_at_utc':verified_at,'accepted_package_unchanged':True}
write(docs/'dlc-compatibility-20261118.json',report)
event('release_records_saved',version='0.3.3',item_id='3830548217',pack_sha256=expected)
