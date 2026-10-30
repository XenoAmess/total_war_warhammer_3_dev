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
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ID = 1142710
REQUIRED_WORKSHOP_ITEMS = (3811098873,)  # memreader Plus, published by its author


def account_activity(owner: str) -> dict:
    """Read fresh public presence before initializing any game SDK session."""
    if not re.fullmatch(r'[0-9]{17}', owner):
        raise ValueError('Expected an explicit Steam account ID')
    observed = datetime.now(timezone.utc).isoformat()
    account_id = int(owner) - 76561197960265728
    if not 0 <= account_id < 2**32:
        raise ValueError('Expected an individual Steam account ID')
    # This separate official endpoint remains useful when profile XML is rate
    # limited. A reported game proves occupancy; an absent game does not prove
    # idle, so the full public-profile checks below are still required.
    mini_request = urllib.request.Request(
        f'https://steamcommunity.com/miniprofile/{account_id}/json?l=english&presence_check={time.time_ns()}',
        headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    try:
        with urllib.request.urlopen(mini_request, timeout=15) as response:
            mini_raw = response.read(512001)
            mini_age = response.headers.get('Age', '0')
            mini_date = response.headers.get('Date')
        if len(mini_raw) <= 512000 and mini_age.isdecimal() and int(mini_age) <= 5:
            mini = json.loads(mini_raw)
            game = (mini.get('in_game') or {}).get('name')
            if isinstance(game, str) and game:
                return {'owner': owner, 'status': 'BUSY', 'game': game,
                        'observed_at_utc': observed, 'server_date': mini_date,
                        'source': 'steam_community_miniprofile',
                        'response_sha256': hashlib.sha256(mini_raw).hexdigest()}
    except (OSError, ValueError, AttributeError):
        pass
    request = urllib.request.Request(
        f'https://steamcommunity.com/profiles/{owner}/?xml=1&l=english&presence_check={time.time_ns()}',
        headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read(512001)
        age = response.headers.get('Age', '0')
        server_date = response.headers.get('Date')
    if len(raw) > 512000 or not age.isdecimal() or int(age) > 5:
        raise RuntimeError('Steam account activity response is stale or invalid')
    profile = ET.fromstring(raw)
    if profile.findtext('steamID64') != owner:
        raise RuntimeError('Steam returned another account profile')
    state, game = profile.findtext('onlineState'), profile.findtext('inGameInfo/gameName')
    if game or state == 'in-game':
        status = 'BUSY'
    elif (profile.findtext('privacyState') == 'public'
          and profile.find('mostPlayedGames') is not None and state in ('online', 'offline')):
        status = 'PUBLIC_PRESENCE_IDLE'
    else:
        status = 'UNAVAILABLE'
    return {'owner': owner, 'status': status, 'game': game, 'online_state': state,
            'observed_at_utc': observed, 'server_date': server_date,
            'source': 'steam_community_public_presence',
            'response_sha256': hashlib.sha256(raw).hexdigest()}


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
                if check_agreement and result.needs_agreement:
                    raise RuntimeError('Steam requires the account owner to accept the Workshop legal agreement')
                return result
            time.sleep(0.1)
        raise TimeoutError('Steam API call did not complete before timeout; preserve the saved item ID')


def publish(dll: Path, pack: Path, acceptance: Path, state_path: Path, preview: Path | None,
            expected_owner: str | None = None):
    sha = hashlib.sha256(pack.read_bytes()).hexdigest()
    results = json.loads(acceptance.read_text(encoding='utf-8'))
    if results.get('release_pack_sha256') != sha or any(results.get(key) != 'PASS' for key in ('L0', 'L1', 'L2', 'L3')):
        raise RuntimeError('Publication requires L0/L1/L2/L3 PASS for this exact pack SHA-256')
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    owner = expected_owner or state.get('owner')
    if not owner:
        raise RuntimeError('Specify --owner before creating a Workshop item')
    activity = account_activity(owner)
    if activity['status'] != 'PUBLIC_PRESENCE_IDLE':
        raise RuntimeError('Account is busy or its activity is unavailable; keep Steam offline and wait: '
                           + json.dumps(activity))
    steam = Steam(dll)

    def save():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')

    try:
        if steam.steam_id != owner:
            raise RuntimeError('The active Steam account differs from the checked account')
        state['account_activity_before_sdk_init'] = activity
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
    parser.add_argument('--owner', help='Expected Steam account ID; required for the first publication')
    args = parser.parse_args()
    print(json.dumps(publish(args.dll, args.pack, args.acceptance, args.state, args.preview, args.owner), indent=2))
