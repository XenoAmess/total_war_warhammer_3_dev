from __future__ import annotations

import ctypes as C
import json
from workshop import APP_ID, UpdateResult, Steam
from workshop_metadata import apply_launcher_metadata, validate_launcher_metadata


class QueryCompleted(C.Structure):
    _fields_ = [('handle', C.c_uint64), ('result', C.c_int32), ('returned', C.c_uint32),
                ('total', C.c_uint32), ('cached', C.c_bool), ('cursor', C.c_char * 256)]


def owned_values(tags: dict, key: str) -> list:
    # Steam may return its canonical spelling (observed PACK_NAME). Preserve
    # raw keys in receipts and combine variants when checking for duplicates.
    return [value for name, values in tags.items() if name.casefold() == key
            for value in values]


def query_launcher_metadata(steam: Steam, item_id: int) -> dict:
    if type(item_id) is not int or item_id <= 0 or item_id >= (1 << 64) - 1:
        raise ValueError('Invalid item_id')

    create_query = steam.bind('SteamAPI_ISteamUGC_CreateQueryUGCDetailsRequest', C.c_uint64, C.c_void_p, C.POINTER(C.c_uint64), C.c_uint32)
    set_return_kv = steam.bind('SteamAPI_ISteamUGC_SetReturnKeyValueTags', C.c_bool, C.c_void_p, C.c_uint64, C.c_bool)
    set_allow_cached = steam.bind('SteamAPI_ISteamUGC_SetAllowCachedResponse', C.c_bool, C.c_void_p, C.c_uint64, C.c_uint32)
    send_query = steam.bind('SteamAPI_ISteamUGC_SendQueryUGCRequest', C.c_uint64, C.c_void_p, C.c_uint64)
    get_num_kv = steam.bind('SteamAPI_ISteamUGC_GetQueryUGCNumKeyValueTags', C.c_uint32, C.c_void_p, C.c_uint64, C.c_uint32)
    get_kv = steam.bind('SteamAPI_ISteamUGC_GetQueryUGCKeyValueTag', C.c_bool, C.c_void_p, C.c_uint64, C.c_uint32, C.c_uint32, C.c_char_p, C.c_uint32, C.c_char_p, C.c_uint32)
    release_query = steam.bind('SteamAPI_ISteamUGC_ReleaseQueryUGCRequest', C.c_bool, C.c_void_p, C.c_uint64)

    ids = (C.c_uint64 * 1)(item_id)
    query = create_query(steam.ugc, ids, 1)
    if query in (0, (1 << 64) - 1):
        raise RuntimeError('Invalid query handle')

    try:
        if not set_return_kv(steam.ugc, query, True):
            raise RuntimeError('SetReturnKeyValueTags failed')
        if not set_allow_cached(steam.ugc, query, 0):
            raise RuntimeError('SetAllowCachedResponse failed')
        handle = send_query(steam.ugc, query)
        if handle in (0, (1 << 64) - 1):
            raise RuntimeError('Invalid send handle')

        result = steam.wait(handle, QueryCompleted, 3401, timeout=45, check_agreement=False)
        if result.handle != query or result.returned != 1 or result.cached:
            raise RuntimeError('Query result mismatch or cached')

        num_tags = get_num_kv(steam.ugc, query, 0)
        if num_tags > 10000:
            raise RuntimeError('Too many key-value tags')

        tags = {}
        for i in range(num_tags):
            key_buf = C.create_string_buffer(256)
            val_buf = C.create_string_buffer(256)
            if not get_kv(steam.ugc, query, 0, i, key_buf, 256, val_buf, 256):
                raise RuntimeError('GetQueryUGCKeyValueTag failed')
            try:
                k = key_buf.value.decode('utf-8')
                v = val_buf.value.decode('utf-8')
            except UnicodeDecodeError:
                raise RuntimeError('Invalid UTF-8 in tag')
            if k in tags:
                tags[k].append(v)
            else:
                tags[k] = [v]
        return tags
    finally:
        if not release_query(steam.ugc, query):
            raise RuntimeError('ReleaseQueryUGCRequest failed')


def repair_launcher_metadata(steam: Steam, item_id: int, expected: dict) -> dict:
    validate_launcher_metadata(expected)

    before = query_launcher_metadata(steam, item_id)
    owned = {k: owned_values(before,k) for k in ('pack_name', 'game_version')}
    if all(len(vals) == 1 and vals[0] == expected[k] for k, vals in owned.items()):
        return {'item_id': str(item_id), 'status': 'SKIPPED', 'before': before, 'after': before}

    start_update = steam.bind('SteamAPI_ISteamUGC_StartItemUpdate', C.c_uint64, C.c_void_p, C.c_uint32, C.c_uint64)
    submit_update = steam.bind('SteamAPI_ISteamUGC_SubmitItemUpdate', C.c_uint64, C.c_void_p, C.c_uint64, C.c_char_p)

    update = start_update(steam.ugc, APP_ID, item_id)
    if update in (0, (1 << 64) - 1):
        raise RuntimeError('Invalid update handle')

    apply_launcher_metadata(steam, update, expected)

    notes = b'Legacy launcher metadata repair'
    handle = submit_update(steam.ugc, update, notes)
    if handle in (0, (1 << 64) - 1):
        raise RuntimeError('Invalid submit handle')

    steam.wait(handle, UpdateResult, 3404)

    after = query_launcher_metadata(steam, item_id)
    if not all(owned_values(after,k) == [expected[k]] for k in ('pack_name', 'game_version')):
        raise RuntimeError('Post-repair verification failed: ' + json.dumps(
            {'item_id':str(item_id),'before':before,'after':after,'submit_handle':str(handle)}))

    return {'item_id': str(item_id), 'status': 'REPAIRED', 'before': before, 'after': after, 'submit_handle': str(handle)}
