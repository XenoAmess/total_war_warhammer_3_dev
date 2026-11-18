from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
r=Path(__file__).parent;repo=Path.cwd();sys.path.insert(0,str(repo/'tools'))
from project import load_project
from workshop import validate_acceptance
from pack import read_pack
project=load_project('recruitment_refresh')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
accepted=read(project.root/'docs/acceptance-results-0.3.4.json')
expected='0d28ee92aa0bf1f5a9c3d7d7331fec682ece2def45c90341f084726607d3bf9d'
assert project.metadata['version']=='0.3.4'and sha(project.pack_path)==expected and accepted['release_pack_sha256']==expected
assert accepted['release_status']=='NATIVE_ACCEPTED_NOT_PUBLISHED'and accepted['L4']=='NOT_RUN'
assert read(project.root/'docs/acceptance-0.3.4/cleanup.json')['status']=='PASS'
assert read(project.root/'docs/acceptance-0.3.4/final-refreshed-save-reload.json')['status']=='PASS'
payload=read_pack(project.pack_path.read_bytes())
for path in project.source_dir.rglob('*'):
 if path.is_file():
  committed=subprocess.check_output(['git','show','HEAD:'+path.relative_to(repo).as_posix()])
  assert committed==path.read_bytes()==payload[path.relative_to(project.source_dir).as_posix()]
for entry in read(project.root/'docs/acceptance-0.3.4/evidence-index.json'):
 assert sha(project.root/'docs/acceptance-0.3.4'/entry['file'])==entry['sha256']
state=read(project.root/'workshop/publication-state.json')
assert state['item_id']=='3830548217'and state['mod_id']==project.id and state['uploaded_version']=='0.3.3'
assert state['status']=='PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED'and not(r/'upload.json').exists()
write(r/'publication-state-before.json',state)
description=(project.root/'workshop/description.bbcode').read_text(encoding='utf-8')
notes=(project.root/'workshop/change-notes.txt').read_text(encoding='utf-8')
for name,text in [('description.bbcode',description),('change-notes.txt',notes)]:
 assert '0.3.4'in text and '199 offline tests passed'in text and 'Bhashiva and four Verminlord types now directly tested'in text
 assert 'remain unowned'not in text and 'native multiplayer'in text
 path=project.root/'workshop'/name
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(repo).as_posix()])==path.read_bytes(),'Commit publication inputs before preparing the release'
assert description.count('[img]')==3 and len(state['gallery'])==3
assert sha(project.build_dir/'preview.png')==state['preview_sha256']
for path in r.glob('*.py'):compile(path.read_text(encoding='utf-8'),str(path),'exec')
write(r/'prepared.json',{'status':'PASS','mod_id':project.id,'version':'0.3.4','machine_id':'pc-20260924rtuf-f11af23c08','observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_commit':accepted['source_commit'],'publication_input_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'pack_sha256':expected,'bytes':project.pack_path.stat().st_size,'acceptance':validate_acceptance(project.pack_path,project.root/'docs/acceptance-results-0.3.4.json',project),'description_sha256':sha(project.root/'workshop/description.bbcode'),'change_notes_sha256':sha(project.root/'workshop/change-notes.txt'),'preview_sha256':sha(project.build_dir/'preview.png'),'existing_gallery_count':3,'production_source_changed':False,'local_model':{'configured_model':'qwen38-coder','available':False,'candidate_posts':0,'fallback_used':False,'receipt':'local-model-status.json'}})
print((r/'prepared.json').read_text(encoding='utf-8'))
