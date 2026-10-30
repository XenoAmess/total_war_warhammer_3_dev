"""Build and reopen the distributable without modifying the game installation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pack import read_pack, read_translations, write_loc, write_pack

ROOT = Path(__file__).resolve().parents[1]


def build(language: str = 'zh-CN', output: Path | None = None) -> dict:
    output = output or ROOT / 'build'
    translations = read_translations(ROOT / 'localisation' / (language + '.tsv'))
    other = read_translations(ROOT / 'localisation' / ('en.tsv' if language == 'zh-CN' else 'zh-CN.tsv'))
    if translations.keys() != other.keys():
        raise ValueError('Translation keys differ')
    files = {p.relative_to(ROOT / 'mod').as_posix(): p.read_bytes()
             for p in (ROOT / 'mod').rglob('*') if p.is_file()}
    files['text/db/xatw3_campaign_utilities.loc'] = write_loc(translations)
    raw = write_pack(files)
    if read_pack(raw) != files:
        raise ValueError('Pack round trip failed')
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'xatw3_campaign_utilities.pack'
    target.write_bytes(raw)
    manifest = {'version': '0.1.0', 'language': language, 'pack': target.name,
                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                'files': [{'path': k, 'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()}
                          for k, v in sorted(files.items())]}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=('zh-CN', 'en'), default='zh-CN')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.language, args.output), indent=2))
