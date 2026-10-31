"""Build a single streamed-media override using two extracted native WEMs.

This produces a static packaging probe, not an installed or playback-tested mod.
Use originals only for local verification; do not distribute the probe assets.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

from game_files import Pack
from wem import inspect_wem

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from pack import read_pack, write_pack


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_media(catalog: dict, media_id: int) -> tuple[dict, bytes]:
    info = catalog['media'][str(media_id)]
    selected = info['selected']
    if selected is None or 'extracted_path' not in selected:
        raise ValueError('Both media files must have been extracted by catalog.py')
    if not info['sources'] or any(node['stream_type'] != 2 or node['plugin_id'] != 262145
                                  for node in info['sources']):
        raise ValueError('Probe requires fully streamed Vorbis sources')
    raw = Path(selected['extracted_path']).read_bytes()
    if sha256(raw) != selected['sha256']:
        raise ValueError('Extracted media hash mismatch')
    return info, raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, choices=['advisor_voice'])
    parser.add_argument('--catalog', required=True, type=Path)
    parser.add_argument('--target-media-id', required=True, type=int)
    parser.add_argument('--donor-media-id', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    if catalog['summary']['schema'] != 'wh3.advisor-audio-catalog/v1':
        raise ValueError('Unsupported catalog')
    target, original = load_media(catalog, args.target_media_id)
    donor, replacement = load_media(catalog, args.donor_media_id)
    if sha256(original) == sha256(replacement):
        raise ValueError('Probe must change the target bytes')
    original_format, replacement_format = inspect_wem(original), inspect_wem(replacement)
    if (original_format.codec, original_format.channels, original_format.sample_rate) != (
            replacement_format.codec, replacement_format.channels, replacement_format.sample_rate):
        raise ValueError('Incompatible codec/channel/rate headers')
    if original_format.codec != 65535:
        raise ValueError('Expected native Wwise Vorbis')
    output = args.output.resolve()
    game = Path(catalog['summary']['source_packs']['db.pack']['path']).parent.parent.resolve()
    build = REPO / 'mods/advisor_voice/build'
    if output == game or game in output.parents or (
            (output == REPO or REPO in output.parents) and output != build and build not in output.parents):
        raise ValueError('Output must be outside the game and outside tracked source directories')
    member = target['selected']['member']
    raw_pack = write_pack({member: replacement})
    if read_pack(raw_pack) != {member: replacement}:
        raise ValueError('Shared pack reader roundtrip failed')
    output.mkdir(parents=True, exist_ok=False)
    pack_path = output / 'advisor_voice_native_swap_probe.pack'
    pack_path.write_bytes(raw_pack)
    parsed = Pack(pack_path)
    if list(parsed.entries) != [member] or parsed.read(member) != replacement:
        raise ValueError('Independent archive reader roundtrip failed')
    affected = [{'key': row['key'], 'thread': row['thread'], 'advisor': row['advisor']}
                for row in catalog['advice'] if args.target_media_id in row['media_ids']]
    receipt = {
        'schema': 'wh3.advisor-native-swap-probe/v1', 'pack': str(pack_path),
        'pack_sha256': sha256(raw_pack), 'pack_bytes': len(raw_pack), 'pack_type': 3,
        'member': member, 'target_media_id': args.target_media_id, 'donor_media_id': args.donor_media_id,
        'original_sha256': sha256(original), 'replacement_sha256': sha256(replacement),
        'original_format': asdict(original_format), 'replacement_format': asdict(replacement_format),
        'affected_db_advice': affected, 'catalog_sha256': sha256(args.catalog.read_bytes()),
        'verification': {'shared_pack_roundtrip': True, 'independent_pack_roundtrip': True,
                         'game_installed': False, 'game_playback_verified': False},
        'limits': ['Native donor bytes only: no custom encoding was tested.',
                   'Matching headers and archive roundtrips do not prove engine playback or load priority.',
                   'Only the selected streamed media path is overridden; other languages and embedded/preloaded media need separate work.']}
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
