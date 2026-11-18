from common import *
import shutil

after=read(ROOT/'dlc-after-offline-full.json')
before=read(REPO/'docs/dlc-activation-2026-11-18/dlc-after-offline-full.json')
old={x['appid']:x for x in before['dlc']}
new=[x for x in after['dlc'] if x['owned'] and not old.get(x['appid'],{}).get('owned')]
listed=[x for x in after['dlc'] if x['listed_for_wh3']]
if len(listed)!=after['enumerated_count'] or any(not x['installed'] or x['downloading'] for x in listed if x['owned']):
    raise RuntimeError('Owned enumerated content not installed')
catalog=read(ROOT/'store-dlc-catalog.json')
store_ids={x['appid'] for x in catalog if int(x['store_parent_app'])==1142710}
unowned=[x for x in listed if not x['owned']]
store_unowned=[x for x in after['dlc'] if x['appid'] in store_ids and not x['owned']]
save('license-diff.json',{'enumerated_before':before['enumerated_count'],'enumerated_after':after['enumerated_count'],
                        'newly_owned':new,'missing_installed':[], 'enumerated_unowned':unowned,
                        'store_wh3_unowned':store_unowned})
if {x['appid'] for x in new}!={3589650,3589660,3589670,3589680,4399460}:
    raise RuntimeError('Unexpected inventory difference; review before recording')
offline=require_offline('offline-after-inventory.json')
no_games()
if any('-cef-enable-debugging' in p.cmdline() for p in steam_processes()):
    raise RuntimeError('Temporary Steam debugging remains')
game=DLL.parent/'Warhammer3.exe'
game_sha=sha(game)
if game_sha!='d2a8a58288bf8bd86768f21ff6be036cebb1916f9c312999c60afc1abe13789f' or after['app_build_id']!=26403568:
    raise RuntimeError('Game changed; requalify native bindings before acceptance')
out=REPO/'docs/dlc-activation-2026-11-18-round2'
out.mkdir(exist_ok=True)
names=['dlc-online-activation.json','dlc-after-offline-full.json','license-diff.json',
       'account-initial.json','account-before-online.json','account-before-restart.json',
       'account-before-dlc-online-activation.json','account-before-dlc-after-offline-full.json',
       'offline-initial.json','offline-before-online-stage.json','controlled-startup-offline.json',
       'final-offline.json','offline-after-inventory.json','manifest-before.json','manifest-after.json',
       'download-state-2.json','local-model-status.json','common.py','dlc_client.py','sync_controller.py',
       'cef_read.py','download_state.js','prepare_sync.py','finalize_sync.py','store-dlc-catalog.json']
for name in names:(out/name).write_bytes((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
report={
 'schema_version':1,'batch':'2026-11-18-round2','machine_id':'pc-20260924rtuf-f11af23c08',
 'recorded_at_utc':now(),'observed_at_utc':after['observed_at_utc'],
 'status':'LICENSES_SYNCED_INSTALLED_OFFLINE_VERIFIED','steam_owner':OWNER,
 'scope':['recruitment_refresh','move_capital'],'previous_inventory':'dlc-activation-2026-11-18/dlc-after-offline-full.json',
 'raw_inventory':'dlc-activation-2026-11-18-round2/dlc-after-offline-full.json',
 'steam_enumeration_before':before['enumerated_count'],'steam_enumeration_after':after['enumerated_count'],
 'ownership_rows_are_not_unique_paid_packs':True,'new_paid_dlc':new,
 'enumerated_owned_count':sum(x['owned'] for x in listed),
 'enumerated_all_owned_installed':False,'owned_enumerated_all_installed':True,'missing_installed':[],
 'enumerated_unowned':unowned,'remaining_unowned_in_supplied_official_wh3_catalog':store_unowned,
 'unowned_interpretation':'Seven raw unowned entries remain. Blood for the Blood God III 1374300 and the three individual Shadows of Change character packs are owned. Do not equate legacy/free/combined entries to seven missing paid gameplay packs; in-game free-content availability is not yet verified.',
 'catalog_scope':'Current client WH3 enumeration plus the official Store catalog captured earlier on 2026-11-18; not a claim about future releases.',
 'required_dlc_install_requests':read(ROOT/'dlc-online-activation.json')['install_requests'],
 'download_claim':'No required DLC/base transfer observed; final StateFlags=4 and TargetBuildID=0. Historical byte counters retained in raw manifests are not new-transfer evidence.',
 'game_version':'9.0.5.0','game_build_id':after['app_build_id'],'game_exe_sha256':game_sha,
 'transitional_online_sdk_result':'Initial online SDK retained the previous 70-entry catalog. Ordinary client restart followed by a fresh offline SDK session enumerated 82 entries and the five new paid licenses.',
 'license_blockers_resolved':['Bhashiva/Clawspeaker/Sawai caravan','Thanquol/four Verminlord subtypes'],
 'native_acceptance':'IN_PROGRESS; separate Mod reports will record actual outcomes. Ownership does not grant test credit.',
 'multiplayer':'NOT_RUN; still requires a second participant/environment.',
 'steam_final_mode':'intentional_offline','offline_receipt':'dlc-activation-2026-11-18-round2/offline-after-inventory.json',
 'local_model':read(ROOT/'local-model-status.json'),'runtime_root':str(ROOT),
 'evidence':[{'file':p.relative_to(REPO/'docs').as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
             for p in sorted(out.iterdir()) if p.is_file()],
}
(REPO/'docs/dlc-activation-2026-11-18-round2.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'status':report['status'],'new_paid_dlc':len(new),'enumerated':len(listed),'offline':offline['status'],'game_unchanged':True}))
