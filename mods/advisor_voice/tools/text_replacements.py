"""Resolve explicit UI translation references while preserving their source keys."""
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class ReplacementResult:
    text: str
    source_keys: tuple[str, ...]
    unresolved: tuple[str, ...]

def resolve_replacements(value: str, loc: Mapping[str, str]) -> ReplacementResult:
    import re
    pattern = re.compile(r'\{\{tr:([^{}]+)\}\}')
    source_keys = set()
    unresolved = set()

    def _resolve(s: str, depth: int, path: tuple[str, ...]) -> str:
        def repl(match):
            alias = match.group(1)
            if depth > 16:
                unresolved.add(alias)
                return match.group(0)
            key = f"ui_text_replacements_localised_text_{alias}"
            if key in loc:
                source_keys.add(key)
                if alias in path:
                    unresolved.add(alias)
                    return match.group(0)
                return _resolve(loc[key], depth + 1, path + (alias,))
            else:
                unresolved.add(alias)
                return match.group(0)

        return pattern.sub(repl, s)

    final_text = _resolve(value, 0, ())
    return ReplacementResult(
        text=final_text,
        source_keys=tuple(sorted(source_keys)),
        unresolved=tuple(sorted(unresolved))
    )
