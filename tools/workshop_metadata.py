"""Validate and apply legacy native launcher metadata tags."""
from __future__ import annotations

import ctypes as C
import re
from project import ModProject

PACK_RE = re.compile(r'[a-z0-9_]+\.pack')
VERSION_RE = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')


def build_launcher_metadata(project: ModProject) -> dict:
    """Return {pack_name, game_version} validated from project metadata."""
    pack = project.pack_name
    if not isinstance(pack, str) or not PACK_RE.fullmatch(pack) or len(pack) > 255:
        raise ValueError('Invalid pack_name')

    workshop = project.metadata.get('workshop', {})
    if not isinstance(workshop, dict):
        raise ValueError('workshop must be an object')

    ver_str = workshop.get('game_version')
    if not isinstance(ver_str, str) or not VERSION_RE.fullmatch(ver_str):
        raise ValueError('workshop.game_version must be a dotted quad string')

    parts = [int(p) for p in ver_str.split('.')]
    if parts[0] == 0:
        raise ValueError('game_version major component must be nonzero')
    if any(p > 65535 for p in parts):
        raise ValueError('game_version components must fit uint16')

    ms = (parts[0] << 16) | parts[1]
    return {'pack_name': pack, 'game_version': str(ms)}


def validate_launcher_metadata(metadata: dict) -> None:
    """Validate the two owned keys before starting a remote update."""
    if not isinstance(metadata, dict) or set(metadata) != {'pack_name', 'game_version'}:
        raise ValueError('metadata must contain exactly pack_name and game_version')

    pack_val = metadata['pack_name']
    ver_val = metadata['game_version']

    if not isinstance(pack_val, str) or not PACK_RE.fullmatch(pack_val) or len(pack_val) > 255:
        raise ValueError('Invalid pack_name value')
    if (not isinstance(ver_val, str) or not re.fullmatch(r'[1-9][0-9]{0,9}', ver_val)
            or not 65536 <= int(ver_val) <= 0xFFFFFFFF):
        raise ValueError('Invalid game_version value')


def apply_launcher_metadata(steam, update: int, metadata: dict) -> None:
    """Remove and re-add pack_name and game_version tags."""
    validate_launcher_metadata(metadata)
    if type(update) is not int or not 0 < update < (1 << 64) - 1:
        raise ValueError('Invalid update handle')

    # Remove owned keys first
    remove = steam.bind('SteamAPI_ISteamUGC_RemoveItemKeyValueTags', C.c_bool, C.c_void_p, C.c_uint64, C.c_char_p)
    for key in ('pack_name', 'game_version'):
        if not remove(steam.ugc, update, key.encode('utf-8')):
            raise RuntimeError(f'RemoveItemKeyValueTags failed for {key}')

    # Add new values
    add = steam.bind('SteamAPI_ISteamUGC_AddItemKeyValueTag', C.c_bool, C.c_void_p, C.c_uint64, C.c_char_p, C.c_char_p)
    if not add(steam.ugc, update, b'pack_name', metadata['pack_name'].encode('utf-8')):
        raise RuntimeError('AddItemKeyValueTag failed for pack_name')
    if not add(steam.ugc, update, b'game_version', metadata['game_version'].encode('utf-8')):
        raise RuntimeError('AddItemKeyValueTag failed for game_version')
