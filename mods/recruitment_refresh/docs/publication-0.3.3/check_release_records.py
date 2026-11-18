from pathlib import Path
import argparse, hashlib, html, json, os, re, subprocess, sys

parser=argparse.ArgumentParser()
parser.add_argument('--mod',required=True,choices=['recruitment_refresh'])
parser.parse_args()
repo=Path.cwd()
runtime=Path(__file__).parent
sys.path.insert(0,str(repo/'tools'))
from pack import read_pack
from project import load_project
from workshop import validate_acceptance

project=load_project('recruitment_refresh')
docs=project.root/'docs'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=read(docs/'workshop-publication-0.3.3.json')
expected='51af917201f2b82aac216783b3b5291ac8198671a444182c9f3a15b0cfbe73cd'
if (record['pack_sha256']!=expected or record['status']!='PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED'
    or sha(project.pack_path)!=expected or sha(Path(record['download']['pack']))!=expected):
    raise RuntimeError('Published package mismatch')
checked=validate_acceptance(project.pack_path,docs/'acceptance-results-0.3.3.json',project)
for p in [docs/'acceptance-results.json',docs/'acceptance-results-0.3.3.json']:
    a=read(p)
    if a['L4']!='PASS' or a['release_pack_sha256']!=expected or not a['workshop_upload_performed']:
        raise RuntimeError('Current publication gate mismatch')
for evidence in record['evidence']:
    p=docs/evidence['file']
    if sha(p)!=evidence['sha256'] or p.stat().st_size!=evidence['bytes']:
        raise RuntimeError('Evidence changed: '+str(p))
for p in (docs/'publication-0.3.3').glob('*.json'):read(p)
files=read_pack(project.pack_path.read_bytes())
for p in project.source_dir.rglob('*'):
    if p.is_file():
        committed=subprocess.check_output(['git','show','HEAD:'+p.relative_to(repo).as_posix()])
        if p.read_bytes()!=committed or files[p.relative_to(project.source_dir).as_posix()]!=committed:
            raise RuntimeError('Accepted source payload changed: '+str(p))
if sha(repo/'mods/move_capital/build/xatw3_move_capital.pack')!='e3702133d65dc7d08c1248a96e5b48a297505f238fe2d6e79a950d79f9d3767f':
    raise RuntimeError('Unchanged Capital package drifted')
mount=record['subscriber_mount']
if mount['status']!='PASS' or not all(mount[k] for k in ['cleaned','preferences_restored','user_script_restored','steam_intentionally_offline']):
    raise RuntimeError('Mount cleanup incomplete')
for item in mount['installed']:
    if Path(item['path']).exists():raise RuntimeError('Temporary test pack remains')
profile=Path(os.environ['APPDATA'])/'The Creative Assembly/Warhammer3/scripts'
if (profile/'preferences.script.txt').read_bytes()!=(runtime/'mount/preferences-original.bin').read_bytes():
    raise RuntimeError('Preferences were not restored byte for byte')
saved_user=runtime/'mount/user-original.bin'
user=profile/'user.script.txt'
if saved_user.exists():
    if user.read_bytes()!=saved_user.read_bytes():raise RuntimeError('User script restoration mismatch')
elif user.exists():raise RuntimeError('Unexpected user script after cleanup')
changelog=next(x for x in record['public_pages'] if x['kind']=='changelog')
text=' '.join(html.unescape(re.sub('<[^>]+>',' ',Path(changelog['path']).read_text(encoding='utf-8'))).split())
notes=(project.root/'workshop/change-notes.txt').read_text(encoding='utf-8')
missing=[line for line in notes.splitlines() if line.strip() and ' '.join(line.split()) not in text]
if missing:raise RuntimeError('Submitted changelog lines missing from public page: '+repr(missing))
for name in ['README.md','docs/README.md','docs/dlc-activation-2026-11-18.md','docs/dlc-acceptance-ledger.md',
             'mods/recruitment_refresh/README.md','mods/recruitment_refresh/docs/README.md',
             'mods/recruitment_refresh/docs/dlc-compatibility-20261118.md',
             'mods/recruitment_refresh/docs/workshop-publication.md']:
    p=repo/name
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' not in link and not (p.parent/link.split('#')[0]).exists():
            raise RuntimeError('Missing document link: '+name+' '+link)
print(json.dumps({'status':'PASS','mod_id':project.id,'version':'0.3.3','pack_sha256':expected,
                  'checks':['publication evidence hashes','exact subscribed package','source payload unchanged',
                            'L0-L4 records','all submitted changelog lines public','document links',
                            'Capital package unchanged','temporary pack and preferences cleanup']}))
