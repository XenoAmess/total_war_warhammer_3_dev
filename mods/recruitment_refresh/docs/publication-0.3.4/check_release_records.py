from pathlib import Path
import argparse,hashlib,json,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
repo=Path.cwd();sys.path.insert(0,str(repo/'tools'))
from project import load_project
from pack import read_pack
from workshop import validate_acceptance
project=load_project('recruitment_refresh');docs=project.root/'docs'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=read(docs/'workshop-publication-0.3.4.json');accepted=read(docs/'acceptance-results-0.3.4.json');state=read(project.root/'workshop/publication-state.json')
assert record['version']==accepted['version']==state['uploaded_version']=='0.3.4'
assert record['status']==accepted['release_status']==state['status']
assert record['pack_sha256']==accepted['release_pack_sha256']==state['pack_sha256']==sha(project.pack_path)=='0d28ee92aa0bf1f5a9c3d7d7331fec682ece2def45c90341f084726607d3bf9d'
assert record['item_id']==state['item_id']=='3830548217'and record['upload_count']==1
assert record['description_sha256']==sha(project.root/'workshop/description.bbcode')
assert record['change_notes_sha256']==sha(project.root/'workshop/change-notes.txt')
assert record['steam_final_receipt']['status']=='offline'and record['steam_final_receipt']['offline_mode']is True
assert accepted==read(docs/'acceptance-results.json')
assert accepted['L4']=='PENDING'and record['status']=='PUBLISHED_PUBLIC_DOWNLOAD_VERIFICATION_PENDING'
assert record['public_verification']['status']=='PUBLIC_METADATA_PASS'
assert record['public_verification']['real_subscribed_download']=='NOT_RUN_ACCOUNT_BUSY'
assert record['public_verification']['launcher_metadata']=='NOT_RUN_ACCOUNT_BUSY'
assert record['pending_verification']and not record['publication_game_started']
for entry in record['evidence']:
 file=docs/entry['file'];assert file.stat().st_size==entry['bytes']and sha(file)==entry['sha256'],entry['file']
payload=read_pack(project.pack_path.read_bytes())
for file in project.source_dir.rglob('*'):
 if file.is_file():
  assert file.read_bytes()==payload[file.relative_to(project.source_dir).as_posix()]
  assert file.read_bytes()==subprocess.check_output(['git','show','HEAD:'+file.relative_to(repo).as_posix()])
assert all(v=='PASS'for v in validate_acceptance(project.pack_path,docs/'acceptance-results-0.3.4.json',project).values())
for file in(docs/'publication-0.3.4').glob('*.py'):compile(file.read_text(encoding='utf-8'),str(file),'exec')
print(json.dumps({'status':'PASS','mod_id':project.id,'publication':'PUBLICLY_PUBLISHED','full_distribution_verification':'PENDING_ACCOUNT_IDLE','pack_sha256':record['pack_sha256'],'public_artifacts_and_hashes':'PASS','source_matches_accepted_pack':True,'steam_intentional_offline':True,'upload_count':1}))
