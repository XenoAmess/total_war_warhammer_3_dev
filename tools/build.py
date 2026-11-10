"""Build and reopen the distributable without modifying the game installation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pack import read_pack, read_translations, write_loc, write_pack
from project import ModProject, add_mod_argument, selected_project

def build(project: ModProject, language: str | None = None, output: Path | None = None) -> dict:
    output = output if output is not None else project.build_dir
    files = {p.relative_to(project.source_dir).as_posix(): p.read_bytes()
             for p in project.source_dir.rglob('*') if p.is_file()}
    if not files:
        raise ValueError(f'Mod {project.id!r} has no release files in src/')
    if project.metadata.get('multiplayer_transport') == 1:
        files['script/xatw3_multiplayer.lua'] = (Path(__file__).parent / 'lua/multiplayer.lua').read_bytes()
        files['script/xatw3_transport_identity.lua'] = (
            "return '" + hashlib.sha256(files['script/xatw3_multiplayer.lua']).hexdigest() + "'\n").encode('ascii')
    languages = project.metadata.get('languages', [])
    language = language or project.metadata.get('default_language')
    if languages:
        if language not in languages:
            raise ValueError(f'Unsupported language: {language}')
        translations = read_translations(project.root / 'localisation' / (language + '.tsv'))
        for other_language in languages:
            other = read_translations(project.root / 'localisation' / (other_language + '.tsv'))
            if translations.keys() != other.keys():
                raise ValueError('Translation keys differ')
        files[project.metadata['localisation_pack_path']] = write_loc(translations)
    elif language is not None:
        raise ValueError('This Mod has no selectable localisation')
    if project.metadata.get('multiplayer_transport') == 1:
        digest = hashlib.sha256()
        for name, content in sorted(files.items()):
            digest.update(name.encode('utf-8') + b'\0' + str(len(content)).encode() + b'\0' + content)
        files[f'script/xatw3_release_{project.id}.lua'] = (
            "return '" + digest.hexdigest() + "'\n").encode('ascii')
    raw = write_pack(files)
    if read_pack(raw) != files:
        raise ValueError('Pack round trip failed')
    output.mkdir(parents=True, exist_ok=True)
    target = output / project.pack_name
    target.write_bytes(raw)
    manifest = {'mod_id': project.id, 'version': project.metadata['version'], 'language': language, 'pack': target.name,
                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                'files': [{'path': k, 'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()}
                          for k, v in sorted(files.items())]}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    add_mod_argument(parser)
    parser.add_argument('--language')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    project = selected_project(parser, args.mod)
    print(json.dumps(build(project, args.language, args.output), indent=2))
