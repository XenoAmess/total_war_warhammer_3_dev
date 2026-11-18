from pathlib import Path
import hashlib,json,shutil,subprocess

repo=Path.cwd()
runtime=Path(__file__).parent
docs=repo/'mods/recruitment_refresh/docs'
dest=docs/'publication-0.3.3'
for name in ['check_release_records.py','normalize_records.py']:
    shutil.copy2(runtime/name,dest/name)
changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines()
paths=[repo/name for name in changed]+list(dest.iterdir())+[docs/'workshop-publication-0.3.3.json']
for path in paths:
    if path.is_file() and path.suffix in ('.json','.py','.log','.md'):
        path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
control=dest/'steam-control.log'
control.write_bytes(('\n'.join(line.rstrip() for line in control.read_text(encoding='utf-8').splitlines()).rstrip()+'\n').encode('utf-8'))
record=json.loads((docs/'workshop-publication-0.3.3.json').read_text(encoding='utf-8'))
record['steam_control_log_canonicalization']={
    'source':str(runtime/'control.log'),
    'source_sha256':hashlib.sha256((runtime/'control.log').read_bytes()).hexdigest(),
    'transform':'Committed log uses LF, removes trailing line whitespace and trailing blank lines; original runtime log remains unchanged.',
}
record['evidence']=[{'file':p.relative_to(docs).as_posix(),
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
                    for p in sorted(dest.iterdir()) if p.is_file()]
(docs/'workshop-publication-0.3.3.json').write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print('Canonical LF release records and evidence hashes updated')
