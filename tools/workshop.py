"""Publish the exact accepted pack with the installed game's Steamworks API.

Requires an online Steam session and a matching PASS acceptance record. The
published item ID is saved immediately after CreateItem, before any upload.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ID = 1142710
REQUIRED_WORKSHOP_ITEMS = (3811098873,)  # memreader Plus, published by its author


class CreateResult(C.Structure):
    _fields_ = [('result', C.c_int32), ('item_id', C.c_uint64), ('needs_agreement', C.c_bool)]


class UpdateResult(C.Structure):
    _fields_ = [('result', C.c_int32), ('needs_agreement', C.c_bool)]


class Tags(C.Structure):
    _fields_ = [('values', C.POINTER(C.c_char_p)), ('count', C.c_int32)]


class DependencyResult(C.Structure):
    _fields_ = [('result', C.c_int32), ('item_id', C.c_uint64), ('child_id', C.c_uint64)]


class Steam:
    def __init__(self, dll: Path):
        os.environ['SteamAppId'] = str(APP_ID)
        os.environ['SteamGameId'] = str(APP_ID)
        self.lib = C.CDLL(str(dll.resolve()))
        raw = dll.read_bytes()
        self.init = self.bind('SteamAPI_Init', C.c_bool)
        self.shutdown = self.bind('SteamAPI_Shutdown', None)
        self.pump = self.bind('SteamAPI_RunCallbacks', None)
        if not self.init():
            raise RuntimeError('SteamAPI_Init failed')
        for name in ('User', 'Utils', 'UGC'):
            matches = set(x.decode() for x in re.findall(('SteamAPI_Steam' + name + r'_v[0-9]+').encode(), raw))
            accessor = max(matches, key=lambda x: int(x.rsplit('_v', 1)[1]))
            setattr(self, name.lower(), self.bind(accessor, C.c_void_p)())
        get_app = self.bind('SteamAPI_ISteamUtils_GetAppID', C.c_uint32, C.c_void_p)
        logged_on = self.bind('SteamAPI_ISteamUser_BLoggedOn', C.c_bool, C.c_void_p)
        get_id = self.bind('SteamAPI_ISteamUser_GetSteamID', C.c_uint64, C.c_void_p)
        self.steam_id = str(get_id(self.user))
        if get_app(self.utils) != APP_ID or not logged_on(self.user):
            self.shutdown()
            raise RuntimeError('An online Steam session for App 1142710 is required')

    def bind(self, name, result, *args):
        fn = getattr(self.lib, name)
        fn.restype, fn.argtypes = result, list(args)
        return fn

    def wait(self, handle: int, result_type, callback: int, timeout: float = 180, check_agreement: bool = True):
        completed = self.bind('SteamAPI_ISteamUtils_IsAPICallCompleted', C.c_bool, C.c_void_p, C.c_uint64, C.POINTER(C.c_bool))
        get = self.bind('SteamAPI_ISteamUtils_GetAPICallResult', C.c_bool, C.c_void_p, C.c_uint64,
                        C.c_void_p, C.c_int32, C.c_int32, C.POINTER(C.c_bool))
        if not handle:
            raise RuntimeError('Steam returned an invalid call handle')
        end = time.monotonic() + timeout
        failed = C.c_bool()
        while time.monotonic() < end:
            self.pump()
            if completed(self.utils, handle, C.byref(failed)):
                result = result_type()
                if failed.value or not get(self.utils, handle, C.byref(result), C.sizeof(result), callback, C.byref(failed)) or failed.value:
                    raise RuntimeError('Steam API call failed')
                if result.result != 1:
                    raise RuntimeError(f'Steam returned EResult={result.result}')
                if result.needs_agreement and check_agreement:
                    raise RuntimeError('Steam requires the account owner to accept the Workshop legal agreement')
                return result
            time.sleep(0.1)
        raise TimeoutError('Steam API call did not complete before timeout; preserve the saved item ID')


def publish(dll: Path, pack: Path, acceptance: Path, state_path: Path, preview: Path | None):
    sha = hashlib.sha256(pack.read_bytes()).hexdigest()
    results = json.loads(acceptance.read_text(encoding='utf-8'))
    if results.get('release_pack_sha256') != sha or any(results.get(key) != 'PASS' for key in ('L0', 'L1', 'L2', 'L3')):
        raise RuntimeError('Publication requires L0/L1/L2/L3 PASS for this exact pack SHA-256')
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    steam = Steam(dll)

    def save():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')

    try:
        if state.get('owner') and state['owner'] != steam.steam_id:
            raise RuntimeError('Stored Workshop item belongs to a different Steam account')
        if not state.get('item_id'):
            if state.get('status') == 'CREATING':
                raise RuntimeError('An earlier CreateItem has an unknown result; resolve its item ID before retrying')
            create = steam.bind('SteamAPI_ISteamUGC_CreateItem', C.c_uint64, C.c_void_p, C.c_uint32, C.c_int32)
            state.update(owner=steam.steam_id, app_id=APP_ID, status='CREATING')
            save()
            result = steam.wait(create(steam.ugc, APP_ID, 0), CreateResult, 3403, check_agreement=False)
            state.update(item_id=str(result.item_id), owner=steam.steam_id, app_id=APP_ID, status='CREATED')
            save()
            if result.needs_agreement:
                raise RuntimeError('Steam requires the account owner to accept the Workshop legal agreement; item ID has been saved')
        add_dependency = steam.bind('SteamAPI_ISteamUGC_AddDependency', C.c_uint64,
                                    C.c_void_p, C.c_uint64, C.c_uint64)
        for child in REQUIRED_WORKSHOP_ITEMS:
            result = steam.wait(add_dependency(steam.ugc, int(state['item_id']), child),
                                DependencyResult, 3412, check_agreement=False)
            if result.item_id != int(state['item_id']) or result.child_id != child:
                raise RuntimeError('Steam returned a dependency result for the wrong item')
        state['required_items'] = [str(item) for item in REQUIRED_WORKSHOP_ITEMS]
        save()
        stage = ROOT / 'build/workshop-content'
        stage.mkdir(parents=True, exist_ok=True)
        leftovers = [p.name for p in stage.iterdir() if p.name != pack.name]
        if leftovers:
            raise RuntimeError(f'Unexpected Workshop staging files: {leftovers}')
        (stage / pack.name).write_bytes(pack.read_bytes())
        begin = steam.bind('SteamAPI_ISteamUGC_StartItemUpdate', C.c_uint64, C.c_void_p, C.c_uint32, C.c_uint64)
        update = begin(steam.ugc, APP_ID, int(state['item_id']))
        if update == (1 << 64) - 1:
            raise RuntimeError('Invalid Workshop update handle')
        fields = {
            'SetItemTitle': '征募与迁都 | Recruitment Refresh & Move Capital',
            'SetItemDescription': (ROOT / 'workshop/description.bbcode').read_text(encoding='utf-8'),
            'SetItemContent': str(stage.resolve())
        }
        if preview:
            fields['SetItemPreview'] = str(preview.resolve())
        for name, value in fields.items():
            fn = steam.bind('SteamAPI_ISteamUGC_' + name, C.c_bool, C.c_void_p, C.c_uint64, C.c_char_p)
            if not fn(steam.ugc, update, value.encode('utf-8')):
                raise RuntimeError(f'{name} was rejected')
        visible = steam.bind('SteamAPI_ISteamUGC_SetItemVisibility', C.c_bool, C.c_void_p, C.c_uint64, C.c_int32)
        if not visible(steam.ugc, update, 0):
            raise RuntimeError('Public visibility was rejected')
        tag_values = (C.c_char_p * 2)(b'mod', b'campaign')
        tags = Tags(tag_values, 2)
        set_tags = steam.bind('SteamAPI_ISteamUGC_SetItemTags', C.c_bool, C.c_void_p, C.c_uint64, C.POINTER(Tags))
        if not set_tags(steam.ugc, update, C.byref(tags)):
            raise RuntimeError('Workshop tags were rejected')
        submit = steam.bind('SteamAPI_ISteamUGC_SubmitItemUpdate', C.c_uint64, C.c_void_p, C.c_uint64, C.c_char_p)
        notes = (ROOT / 'workshop/change-notes.txt').read_text(encoding='utf-8')
        state.update(status='UPLOADING', pack_sha256=sha)
        save()
        steam.wait(submit(steam.ugc, update, notes.encode('utf-8')), UpdateResult, 3404)
        state.update(status='UPLOADED_PUBLIC_VERIFICATION_PENDING', url='https://steamcommunity.com/sharedfiles/filedetails/?id=' + state['item_id'])
        save()
        return state
    finally:
        steam.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dll', type=Path, required=True)
    parser.add_argument('--pack', type=Path, default=ROOT / 'build/xatw3_campaign_utilities.pack')
    parser.add_argument('--acceptance', type=Path, default=ROOT / 'docs/acceptance-results.json')
    parser.add_argument('--state', type=Path, default=ROOT / 'workshop/publication-state.json')
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    print(json.dumps(publish(args.dll, args.pack, args.acceptance, args.state, args.preview), indent=2))
