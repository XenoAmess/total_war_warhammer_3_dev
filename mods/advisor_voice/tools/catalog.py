"""Audit advisor event/media/text links; optionally extract native WEM files.

This reads the explicitly named vanilla packs, not the engine's live mod order.
Original resources and full text exports must stay outside tracked source files.
"""
import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct

from bank_graph import AudioNode, index_bank, resolve_event
from event_dat import parse_dat
from game_files import Pack, fnv1, read_advice, read_advice_text


def event_ids(data: bytes) -> set[int]:
    """Index event IDs from chunk boundaries without guessing playback edges."""
    result: set[int] = set()
    position = 0
    if data[:4] != b'BKHD':
        raise ValueError('Expected BKHD bank')
    while position < len(data):
        if position + 8 > len(data):
            raise ValueError('Truncated bank chunk')
        tag, size = struct.unpack_from('<4sI', data, position)
        position += 8
        end = position + size
        if end > len(data):
            raise ValueError('Chunk outside bank')
        if tag == b'HIRC':
            count = struct.unpack_from('<I', data, position)[0]
            cursor = position + 4
            for _ in range(count):
                if cursor + 9 > end:
                    raise ValueError('Truncated HIRC object')
                kind, length = struct.unpack_from('<BI', data, cursor)
                cursor += 5
                if length < 4 or cursor + length > end:
                    raise ValueError('Invalid HIRC object length')
                if kind in (4, 15):
                    result.add(struct.unpack_from('<I', data, cursor)[0])
                cursor += length
            if cursor != end:
                raise ValueError('HIRC trailing bytes')
        position = end
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, choices=['advisor_voice'])
    parser.add_argument('--game-dir', required=True, type=Path)
    languages = {'en': 'english(uk)', 'cn': 'chinese', 'fr': 'french(france)',
                 'ge': 'german', 'it': 'italian', 'pl': 'polish', 'ru': 'russian', 'sp': 'spanish(spain)'}
    parser.add_argument('--audio-language', required=True, choices=languages)
    parser.add_argument('--wwiser-root', required=True, type=Path)
    parser.add_argument('--steam-receipt', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--extract', action='store_true')
    parser.add_argument('--max-extract-bytes', type=int, default=512 * 1024 * 1024)
    args = parser.parse_args()
    language_path = languages[args.audio_language]
    bank_pack_name = f'audio_{args.audio_language}_bnk.pack'
    media_pack_name = f'audio_{args.audio_language}.pack'
    game, output = args.game_dir.resolve(), args.output.resolve()
    repo = Path(__file__).resolve().parents[3]
    build = repo / 'mods/advisor_voice/build'
    if output == game or game in output.parents or (
            (output == repo or repo in output.parents) and output != build and build not in output.parents):
        raise ValueError('Output must be outside the game and outside tracked source directories')
    receipt = json.loads(args.steam_receipt.read_text(encoding='utf-8'))
    if receipt['status'] != 'offline' or receipt['offline_mode'] is not True:
        raise ValueError('A real offline observation is required')
    output.mkdir(parents=True, exist_ok=False)
    data = game / 'data'
    names = list(dict.fromkeys(['db.pack', 'audio_base_bnk.pack', bank_pack_name,
                               media_pack_name, 'audio_en.pack', 'audio_base.pack', 'local_cn.pack', 'local_en.pack']))
    packs = {name: Pack(data / name) for name in names}
    advice = read_advice(packs['db.pack'].read('db/advice_levels_tables/data__'))
    texts: dict[str, dict[str, str]] = {}
    text_sources: dict[str, list[str]] = {}
    for language in ('cn', 'en'):
        pack = packs['local_' + language + '.pack']
        merged: dict[str, str] = {}
        text_sources[language] = []
        for member in sorted(pack.entries):
            if not member.endswith('.loc'):
                continue
            content = read_advice_text(pack.read(member))
            if content:
                text_sources[language].append(member)
            for key, value in content.items():
                if key in merged and merged[key] != value:
                    raise ValueError(f'Conflicting localization key: {language}/{key}')
                merged[key] = value
        texts[language] = merged
    dat_bytes = packs['audio_base_bnk.pack'].read('audio/wwise/event_data__core.dat')
    dat = parse_dat(dat_bytes)
    by_name = {event.name.lower(): event.name for event in dat.events}
    hash_names: dict[int, str] = {}
    for name in by_name:
        number = fnv1(name)
        if number in hash_names and hash_names[number] != name:
            raise ValueError(f'Event hash collision: {name}/{hash_names[number]}')
        hash_names[number] = name
    rows = []
    requested: set[int] = set()
    for item in advice:
        stem = item.thread.replace('.', '_').lower()
        if not stem.startswith('play_'):
            stem = 'play_' + stem
        matched = {by_name[candidate] for candidate in (stem, stem + '_' + str(item.level))
                   if candidate in by_name}
        requested.update(fnv1(name) for name in matched)
        key = 'advice_levels_onscreen_text_' + item.key
        rows.append({**asdict(item), 'loc_key': key,
                     'texts': {lang: content.get(key) for lang, content in texts.items()},
                     'event_match_basis': 'normalized thread with optional DB level suffix; runtime association unverified',
                     'events': sorted(matched)})
    bank_pack = packs[bank_pack_name]
    initial = sorted(name for name in bank_pack.entries
                     if re.search(r'/(battle|campaign)_advice[^/]*\.bnk$', name))
    selected = list(initial)
    covered: set[int] = set()
    initial_roots: set[int] = set()
    for name in initial:
        initial_roots.update(event_ids(bank_pack.read(name)))
    covered.update(initial_roots)
    # Exact ID lookup locates additional required banks; it does not infer edges.
    for name in sorted(bank_pack.entries):
        if not name.endswith('.bnk') or name in initial:
            continue
        found = event_ids(bank_pack.read(name)) & (requested - covered)
        if found:
            selected.append(name)
            covered.update(found)
    nodes: dict[int, AudioNode] = {}
    conflicts: set[int] = set()
    bank_errors: list[dict[str, str]] = []
    for name in selected:
        target = output / 'banks' / Path(name).name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(bank_pack.read(name))
        try:
            indexed = index_bank(target, args.wwiser_root)
        except (ValueError, AttributeError, ImportError) as error:
            bank_errors.append({'bank': name, 'error': str(error)})
            continue
        for key, node in indexed.items():
            if key in conflicts:
                continue
            if key in nodes:
                old, new = asdict(nodes[key]), asdict(node)
                old.pop('bank')
                new.pop('bank')
                if old != new:
                    conflicts.add(key)
                    nodes.pop(key)
                    continue
            nodes[key] = node
    resolutions = {event: resolve_event(event, nodes) for event in requested | initial_roots}
    all_media: set[int] = set()
    for row in rows:
        resolved = []
        row_media: set[int] = set()
        for name in row['events']:
            result = resolutions[fnv1(name)]
            resolved.append({'event': name, 'event_id': fnv1(name), **asdict(result)})
            row_media.update(result.media_ids)
        row['event_resolutions'] = resolved
        row['media_ids'] = sorted(row_media)
        row['graph_complete'] = bool(resolved) and bool(row_media) and all(
            item['media_ids'] and not any(item[field] for field in ('missing_node_ids', 'unsupported_kinds', 'cycle_ids'))
            for item in resolved)
        all_media.update(row_media)
    unbound = []
    name_by_id = {fnv1(name): name for name in by_name.values()}
    for event in sorted(initial_roots - requested):
        result = resolutions[event]
        unbound.append({'event_id': event, 'event': name_by_id.get(event), **asdict(result)})
        all_media.update(result.media_ids)
    # Also inventory sound leaves that have no discovered event/DB root.
    bank_leaf_media = {node.media_id for node in nodes.values()
                       if node.kind == 'CAkSound' and node.media_id is not None}
    all_media.update(bank_leaf_media)
    db_media = {i for row in rows for i in row['media_ids']}
    advice_bank_media = {i for event in initial_roots for i in resolutions[event].media_ids}
    sound_sources: dict[int, list[dict]] = defaultdict(list)
    for node in nodes.values():
        if node.kind == 'CAkSound' and node.media_id is not None:
            sound_sources[node.media_id].append({'sound_id': node.object_id, 'bank': Path(node.bank).name,
                                                'stream_type': node.stream_type, 'plugin_id': node.plugin_id})
    media: dict[str, dict] = {}
    variants: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for pack_name in dict.fromkeys([media_pack_name, 'audio_en.pack', 'audio_base.pack']):
        for name in packs[pack_name].entries:
            if name.endswith('.wem') and Path(name).stem.isdigit():
                variants[int(Path(name).stem)].append((pack_name, name))
    planned = 0
    for number in sorted(all_media):
        candidates = variants.get(number, [])
        preferred = [pair for pair in candidates if f'/{language_path}/' in pair[1].lower()]
        if not preferred:
            preferred = [pair for pair in candidates if pair[1].lower() == f'audio/wwise/{number}.wem']
        scopes = [label for label, group in [('db_advice', db_media), ('advice_bank_event', advice_bank_media),
                                             ('selected_bank_leaf', bank_leaf_media)] if number in group]
        info: dict = {'media_id': number, 'variants': candidates, 'selected': None,
                      'scopes': scopes, 'sources': sound_sources[number]}
        if len(preferred) == 1:
            pack_name, name = preferred[0]
            info['selected'] = {'pack': pack_name, 'member': name,
                                'stored_bytes': packs[pack_name].entries[name].size}
            planned += packs[pack_name].entries[name].size
        media[str(number)] = info
    if args.extract and planned > args.max_extract_bytes:
        raise ValueError(f'Extraction budget exceeded: {planned} bytes')
    if args.extract:
        for info in media.values():
            selected_media = info['selected']
            if selected_media is None:
                continue
            raw = packs[selected_media['pack']].read(selected_media['member'])
            destination = output / 'media' / selected_media['member']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            selected_media.update({'sha256': hashlib.sha256(raw).hexdigest(), 'decoded_bytes': len(raw),
                                   'extracted_path': str(destination)})
    for row in rows:
        row['media_available'] = bool(row['media_ids']) and all(media[str(i)]['selected'] for i in row['media_ids'])
    summary = {
        'schema': 'wh3.advisor-audio-catalog/v1', 'machine_id': receipt['machine_id'],
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'steam_observation': {'observed_at_utc': receipt['observed_at_utc'], 'status': receipt['status'],
                              'offline_mode': receipt['offline_mode']},
        'audio_language': language_path, 'text_languages': ['cn', 'en'],
        'advice_rows': len(rows), 'rows_with_named_events': sum(bool(r['events']) for r in rows),
        'advice_level_counts': dict(Counter(r['level'] for r in rows)),
        'rows_with_multiple_event_candidates': sum(len(r['events']) > 1 for r in rows),
        'rows_with_complete_graph': sum(r['graph_complete'] for r in rows),
        'rows_with_available_media': sum(bool(r['media_available']) for r in rows),
        'rows_with_text': {lang: sum(r['texts'][lang] is not None for r in rows) for lang in texts},
        'text_source_members': text_sources,
        'requested_event_ids': len(requested), 'initial_advice_banks': initial,
        'selected_banks': selected, 'bank_errors': bank_errors,
        'conflicting_object_ids': sorted(conflicts), 'unbound_advice_bank_events': len(unbound),
        'unique_media_ids': len(media), 'available_media_ids': sum(m['selected'] is not None for m in media.values()),
        'media_per_scope': {'db_advice': len(db_media), 'advice_bank_event': len(advice_bank_media),
                            'selected_bank_leaf': len(bank_leaf_media)},
        'planned_stored_media_bytes': planned, 'media_extracted': args.extract,
        'extracted_media_files': sum('extracted_path' in (m['selected'] or {}) for m in media.values()),
        'dat_section_counts': {name: len(getattr(dat, name)) for name in dat.__dataclass_fields__},
        'event_dat_sha256': hashlib.sha256(dat_bytes).hexdigest(),
        'source_packs': {name: pack.fingerprint() for name, pack in packs.items()},
        'limits': ['Explicit vanilla pack inputs, not verified live engine/mod load order.',
                   'DB advice and selected advice-bank scope; external sources and movies require separate auditing.',
                   'Unmatched names, unsupported graph types and object conflicts remain unresolved.',
                   'Text is paired by DB localization key, not by speech recognition or listening.']}
    for pack in packs.values():
        pack.verify_unchanged()
    for name, value in [('catalog.json', {'summary': summary, 'advice': rows, 'media': media, 'unbound_events': unbound}),
                        ('summary.json', summary)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (output / 'advice-media-text.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['advice_key', 'thread', 'level', 'advisor', 'loc_key', 'text_cn', 'text_en',
                         'event', 'event_id', 'media_id', 'media_pack', 'media_member', 'graph_complete'])
        for row in rows:
            for event in row['event_resolutions'] or [{}]:
                for number in event.get('media_ids', []) or [None]:
                    selected_media = (media[str(number)]['selected'] or {}) if number is not None else {}
                    writer.writerow([row['key'], row['thread'], row['level'], row['advisor'], row['loc_key'],
                                     row['texts']['cn'], row['texts']['en'], event.get('event'), event.get('event_id'),
                                     number, selected_media.get('pack'), selected_media.get('member'), row['graph_complete']])
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
