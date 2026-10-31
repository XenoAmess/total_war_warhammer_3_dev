"""Exact subtitle-key candidate joins; local-model candidate with owner corrections."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class TextRef:
    key: str
    text: str

@dataclass(frozen=True)
class EventTextMatch:
    ref: TextRef
    method: str

_ALLOWED_PREFIXES = (
    "aide_de_camp_speeches_text_",
    "scripted_subtitles_localised_text_",
    "vo_speech_texts_text_",
    "pre_battle_speeches_text_",
    "vo_fmv_texts_text_",
)

def build_index(loc: Mapping[str, str]) -> dict[str, tuple[TextRef, ...]]:
    index: dict[str, list[TextRef]] = {}
    for key, text in loc.items():
        cf = key.casefold()
        index.setdefault(cf, []).append(TextRef(key=key, text=text))
    return {cf: tuple(refs) for cf, refs in index.items()}

def _candidate_stems(event: str) -> list[tuple[str, str]]:
    stems: list[tuple[str, str]] = []
    if not event:
        return stems
    stems.append((event, "exact_event"))
    if event.lower().startswith("play_"):
        stems.append((event[5:], "without_play"))
    for stem, method in list(stems):
        if stem.endswith("_1"):
            stems.append((stem[:-2], "level_1_wrapper"))
    return stems

def find_event_text(event: str, index: Mapping[str, tuple[TextRef, ...]]) -> tuple[EventTextMatch, ...]:
    if not event:
        return ()
    seen_keys: set[str] = set()
    matches: list[EventTextMatch] = []
    for stem, method in _candidate_stems(event):
        for prefix in _ALLOWED_PREFIXES:
            full_key = prefix + stem
            cf_full_key = full_key.casefold()
            refs = index.get(cf_full_key, ())
            for ref in refs:
                if ref.key not in seen_keys:
                    seen_keys.add(ref.key)
                    matches.append(EventTextMatch(ref=ref, method=method))
    matches.sort(key=lambda m: m.ref.key)
    return tuple(matches)
