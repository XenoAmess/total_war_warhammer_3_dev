from pathlib import Path
import argparse, hashlib, json, subprocess, sys

parser = argparse.ArgumentParser()
parser.add_argument('--mod', required=True, choices=['recruitment_refresh'])
parser.parse_args()
repo = Path.cwd()
root = Path(__file__).parent
old = root.parent / 'special-recruitment-release-20261116'
sys.path.insert(0, str(repo / 'tools'))
from project import load_project
from pack import read_pack
from workshop import validate_acceptance

project = load_project('recruitment_refresh')
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
save = lambda name, value: (root/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
accepted = read(project.root/'docs/acceptance-results-0.3.3.json')
expected = '51af917201f2b82aac216783b3b5291ac8198671a444182c9f3a15b0cfbe73cd'
verification = read(project.root/'docs/acceptance-0.3.3/verification.json')
if (project.metadata['version'] != '0.3.3' or sha(project.pack_path) != expected
    or accepted['release_pack_sha256'] != expected or verification['package_sha256'] != expected
    or verification['status'] != 'PASS' or not verification['cold_package_verified']):
    raise RuntimeError('Exact package acceptance mismatch')
files = read_pack(project.pack_path.read_bytes())
for path in project.source_dir.rglob('*'):
    if path.is_file():
        committed = subprocess.check_output(['git', 'show', 'HEAD:'+path.relative_to(repo).as_posix()])
        if committed != path.read_bytes() or committed != files[path.relative_to(project.source_dir).as_posix()]:
            raise RuntimeError('Source/package mismatch: '+str(path))
state = read(project.root/'workshop/publication-state.json')
if state['item_id'] != '3830548217' or state['mod_id'] != project.id or state['uploaded_version'] != '0.3.2':
    raise RuntimeError('Unexpected original publication state; do not replay upload')
save('publication-state-before.json', state)
description = (project.root/'workshop/description.bbcode').read_text(encoding='utf-8')
notes = (project.root/'workshop/change-notes.txt').read_text(encoding='utf-8')
if ('0.3.3 Alpha' not in description or description.count('[img]') != 3
    or 'Bhashiva/Clawspeakers remain unowned and untested directly' not in description
    or '0.3.3' not in notes or '197 offline tests passed' not in notes):
    raise RuntimeError('Publication text does not describe this exact accepted scope')
for name in ['common.py', 'controller.py', 'publish_child.py', 'verify_public.py', 'mount_smoke.py']:
    text = (old/name).read_text(encoding='utf-8')
    if name != 'common.py': text = text.replace('0.3.2', '0.3.3')
    if name == 'publish_child.py':
        text = text.replace("steam=Steam(DLL)", "idle('account-before-download-sdk.json');steam=Steam(DLL)")
    if name == 'verify_public.py':
        text = text.replace('Chaos Dwarf and Bhashiva caravans were NOT directly tested',
                            'Bhashiva/Clawspeakers remain unowned and untested directly')
        text = text.replace("docs/workshop-publication-0.3.1.json", "docs/workshop-publication-0.3.2.json")
    (root/name).write_text(text, encoding='utf-8')
    compile(text, str(root/name), 'exec')
save('prepared.json', {
    'status': 'PASS', 'mod_id': project.id, 'version': '0.3.3',
    'source_commit': '2625d099b56be3a2d1d93db598b673bbe8e2b43f',
    'publication_input_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
    'pack_sha256': expected, 'bytes': project.pack_path.stat().st_size,
    'acceptance': validate_acceptance(project.pack_path, project.root/'docs/acceptance-results-0.3.3.json', project),
    'description_sha256': sha(project.root/'workshop/description.bbcode'),
    'change_notes_sha256': sha(project.root/'workshop/change-notes.txt'),
    'existing_gallery_count': 3, 'production_source_changed': False,
    'local_model': {'configured_model': 'qwen38-coder', 'available': False, 'candidate_posts': 0,
                    'fallback_used': False, 'receipt': 'local-model-status.json'},
})
print((root/'prepared.json').read_text(encoding='utf-8'))
