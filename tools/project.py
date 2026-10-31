"""Resolve one explicitly selected Mod and its isolated workspace paths."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModProject:
    root: Path
    metadata: dict

    @property
    def id(self) -> str:
        return self.metadata['id']

    @property
    def pack_name(self) -> str:
        return self.metadata['pack_name']

    @property
    def source_dir(self) -> Path:
        return self.root / 'src'

    @property
    def build_dir(self) -> Path:
        return self.root / 'build'

    @property
    def pack_path(self) -> Path:
        return self.build_dir / self.pack_name

    @property
    def required_items(self) -> tuple[int, ...]:
        return tuple(int(item) for item in self.metadata.get('workshop', {}).get('required_items', []))


def load_project(mod_id: str, repository: Path = ROOT) -> ModProject:
    if not re.fullmatch(r'[a-z][a-z0-9_]*', mod_id):
        raise ValueError('Mod ID must contain lowercase letters, digits and underscores')
    mods = (repository / 'mods').resolve()
    folder = (mods / mod_id).resolve()
    if not folder.is_relative_to(mods):
        raise ValueError('Mod directory escapes the repository')
    manifest = folder / 'mod.json'
    if not manifest.is_file():
        raise ValueError(f'Mod {mod_id!r} has no mod.json; research-only directories cannot be built')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or data.get('id') != mod_id:
        raise ValueError('Mod manifest schema or ID does not match its directory')
    for key in ('title', 'version'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'Missing Mod metadata: {key}')
    if not re.fullmatch(r'[a-z0-9_]+\.pack', data.get('pack_name', '')):
        raise ValueError('pack_name must be a lowercase .pack filename')
    languages = data.get('languages', [])
    if not isinstance(languages, list) or any(not isinstance(x, str) or not re.fullmatch(r'[A-Za-z0-9-]+', x) for x in languages):
        raise ValueError('Invalid language list')
    if len(set(languages)) != len(languages):
        raise ValueError('Duplicate language')
    if languages:
        path = data.get('localisation_pack_path', '')
        if not path.endswith('.loc') or path.startswith('/') or '..' in path.split('/') or '\\' in path:
            raise ValueError('Invalid localisation pack path')
        if data.get('default_language') not in languages:
            raise ValueError('default_language must occur in languages')
    workshop = data.get('workshop', {})
    if not isinstance(workshop, dict):
        raise ValueError('workshop must be an object')
    required = workshop.get('required_items', [])
    if not isinstance(required, list) or any(not isinstance(x, str) or not x.isdecimal() or int(x) == 0 for x in required):
        raise ValueError('Invalid required Workshop item ID')
    tags = workshop.get('tags', ['mod'])
    if not isinstance(tags, list) or not tags or any(not isinstance(x, str) or not x for x in tags):
        raise ValueError('Invalid Workshop tags')
    return ModProject(folder, data)


def add_mod_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--mod', required=True, help='Mod directory name under mods/')


def selected_project(parser: argparse.ArgumentParser, mod_id: str) -> ModProject:
    try:
        return load_project(mod_id)
    except (ValueError, OSError) as error:
        parser.error(str(error))
