"""Export Chinese subtitle candidates for every media file in an advisor catalog.

Associations use DB localization keys and exact event/key suffix candidates.
They do not certify that the localized text is a word-for-word transcript.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

from game_files import Pack, read_loc
from text_links import build_index, find_event_text
from text_replacements import resolve_replacements

PREFIXES = ('advice_levels_onscreen_text_', 'aide_de_camp_speeches_text_',
            'scripted_subtitles_localised_text_', 'vo_speech_texts_text_',
            'pre_battle_speeches_text_', 'vo_fmv_texts_text_')


def has_han(value: str | None) -> bool:
    return bool(value and re.search('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003134f]', value))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, choices=['advisor_voice'])
    parser.add_argument('--catalog', required=True, type=Path)
    parser.add_argument('--steam-receipt', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw_catalog = args.catalog.read_bytes()
    catalog = json.loads(raw_catalog)
    if catalog['summary']['schema'] != 'wh3.advisor-audio-catalog/v1':
        raise ValueError('Unsupported catalog')
    receipt = json.loads(args.steam_receipt.read_text(encoding='utf-8'))
    if receipt['status'] != 'offline' or receipt['offline_mode'] is not True:
        raise ValueError('A real offline observation is required')
    game = Path(catalog['summary']['source_packs']['db.pack']['path']).parent.parent.resolve()
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[3]
    build = repo / 'mods/advisor_voice/build'
    if output == game or game in output.parents or (
            (output == repo or repo in output.parents) and output != build and build not in output.parents):
        raise ValueError('Output must be outside the game and outside tracked source directories')
    packs = {lang: Pack(game / 'data' / f'local_{lang}.pack') for lang in ('cn', 'zh', 'en')}
    texts: dict[str, dict[str, str]] = {}
    members = {}
    for lang, pack in packs.items():
        merged: dict[str, str] = {}
        members[lang] = []
        for name in sorted(pack.entries):
            if not name.endswith('.loc'):
                continue
            rows = read_loc(pack.read(name))
            members[lang].append({'member': name, 'loc_records': len(rows)})
            for key, value in rows.items():
                if key in merged and merged[key] != value:
                    raise ValueError(f'Conflicting LOC key: {lang}/{key}')
                merged[key] = value
        texts[lang] = merged
    all_keys = set().union(*(content.keys() for content in texts.values()))
    relevant = {key: {lang: content.get(key) for lang, content in texts.items()}
                for key in sorted(all_keys) if key.startswith(PREFIXES)}
    resolved = {key: {lang: resolve_replacements(value, texts[lang]) if value is not None else None
                      for lang, value in values.items()} for key, values in relevant.items()}

    def resolved_fields(key: str) -> dict:
        values = resolved.get(key, {})
        return {'resolved_texts': {lang: value.text if value is not None else None for lang, value in values.items()},
                'replacement_source_keys': {lang: value.source_keys if value is not None else [] for lang, value in values.items()},
                'unresolved_replacements': {lang: value.unresolved if value is not None else [] for lang, value in values.items()}}
    # The linker uses keys only; raw texts are fetched from their exact source key.
    index = build_index({key: '' for key in relevant})
    links: dict[int, dict[str, dict]] = defaultdict(dict)
    advice_rows = []

    def attach(number: int, key: str, method: str, advice_key: str | None = None,
               event: str | None = None) -> None:
        if key not in relevant:
            return
        item = links[number].setdefault(key, {'loc_key': key, 'texts': relevant[key],
                                               **resolved_fields(key),
                                               'methods': set(), 'advice_keys': set(), 'events': set()})
        item['methods'].add(method)
        if advice_key is not None:
            item['advice_keys'].add(advice_key)
        if event is not None:
            item['events'].add(event)

    events: dict[int, dict] = {}
    for row in catalog['advice']:
        key = row['loc_key']
        advice_rows.append({'key': row['key'], 'thread': row['thread'], 'advisor': row['advisor'],
                            'hidden': row['hidden'], 'loc_key': key, 'texts': relevant.get(key),
                            **resolved_fields(key),
                            'media_ids': row['media_ids']})
        for number in row['media_ids']:
            attach(number, key, 'db_localization_key_and_event_name_candidate', advice_key=row['key'])
        for event in row['event_resolutions']:
            events[event['event_id']] = event
    for event in catalog['unbound_events'] + catalog.get('extra_bank_events', []):
        events[event['event_id']] = event
    for event in events.values():
        if not event.get('event'):
            continue
        for match in find_event_text(event['event'], index):
            for number in event['media_ids']:
                attach(number, match.ref.key, 'event_key_suffix_candidate:' + match.method,
                       event=event['event'])
    media_rows = []
    for key, media in catalog['media'].items():
        number = int(key)
        refs = []
        for ref in links[number].values():
            refs.append({**ref, **{field: sorted(ref[field]) for field in ('methods', 'advice_keys', 'events')}})
        media_rows.append({'media_id': number, 'selected': media['selected'], 'scopes': media['scopes'],
                           'text_candidates': sorted(refs, key=lambda ref: ref['loc_key']),
                           'has_cn_text': any(has_han(ref['resolved_texts']['cn']) for ref in refs),
                           'has_zh_text': any(has_han(ref['resolved_texts']['zh']) for ref in refs)})
    family_counts = {lang: {prefix: {'keys': sum(key in texts[lang] for key in relevant if key.startswith(prefix)),
                                    'with_han': sum(has_han(resolved[key][lang].text) for key in relevant
                                                    if key.startswith(prefix) and resolved[key][lang] is not None)}
                            for prefix in PREFIXES} for lang in texts}
    summary = {
        'schema': 'wh3.advisor-chinese-text-catalog/v1', 'machine_id': receipt['machine_id'],
        'steam_observation': {'observed_at_utc': receipt['observed_at_utc'], 'status': receipt['status'],
                              'offline_mode': receipt['offline_mode']},
        'audio_catalog_sha256': hashlib.sha256(raw_catalog).hexdigest(),
        'audio_catalog': str(args.catalog.resolve()), 'media_files': len(media_rows),
        'media_with_cn_candidate': sum(row['has_cn_text'] for row in media_rows),
        'media_with_traditional_only_candidate': sum(row['has_zh_text'] and not row['has_cn_text'] for row in media_rows),
        'media_without_chinese_candidate': sum(not row['has_cn_text'] and not row['has_zh_text'] for row in media_rows),
        'media_with_multiple_distinct_cn_candidates': sum(len({ref['resolved_texts']['cn'] for ref in row['text_candidates']
                                                            if has_han(ref['resolved_texts']['cn'])}) > 1 for row in media_rows),
        'advice_text_found': {lang: sum(row['loc_key'] in texts[lang] for row in advice_rows) for lang in texts},
        'advice_text_with_han': {lang: sum(has_han(row['resolved_texts'].get(lang)) for row in advice_rows) for lang in texts},
        'replacement_references': {lang: sum(bool(value[lang] and value[lang].source_keys) for value in resolved.values()) for lang in texts},
        'unresolved_replacement_references': {lang: sum(bool(value[lang] and value[lang].unresolved) for value in resolved.values()) for lang in texts},
        'unmatched_advice_text_keys': {lang: [row['loc_key'] for row in advice_rows if row['loc_key'] not in texts[lang]] for lang in texts},
        'event_roots_checked': len(events), 'family_counts': family_counts,
        'source_packs': {lang: pack.fingerprint() for lang, pack in packs.items()}, 'loc_members': members,
        'limits': ['Exact resource keys and event-name candidates, not verified spoken transcripts.',
                   'All media reachable from an event receive its candidate text; random/sequence variants may require manual segmentation.',
                   'Explicit {{tr:alias}} references resolve against UI text replacements, preserving raw text and source keys.',
                   'No fuzzy association, transcription, translation or automatic traditional-to-simplified conversion.',
                   'Missing candidate means unresolved in this explicit resource scope, not proof that no Chinese text exists anywhere.']}
    for pack in packs.values():
        pack.verify_unchanged()
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [('summary.json', summary), ('media-texts.json', media_rows),
                        ('advice-texts.json', advice_rows), ('subtitle-resources.json', {
                            key: {'texts': values, **resolved_fields(key)} for key, values in relevant.items()})]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (output / 'media-chinese-text.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['media_id', 'media_member', 'loc_key', 'text_cn', 'text_zh', 'text_en',
                         'raw_cn', 'raw_zh', 'raw_en',
                         'methods', 'advice_keys', 'events'])
        for row in media_rows:
            for ref in row['text_candidates'] or [{}]:
                writer.writerow([row['media_id'], (row['selected'] or {}).get('member'), ref.get('loc_key'),
                                 *[ref.get('resolved_texts', {}).get(lang) for lang in ('cn', 'zh', 'en')],
                                 *[ref.get('texts', {}).get(lang) for lang in ('cn', 'zh', 'en')],
                                 *[json.dumps(ref.get(field, []), ensure_ascii=False) for field in ('methods', 'advice_keys', 'events')]])
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ('unmatched_advice_text_keys', 'source_packs', 'loc_members')}, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
