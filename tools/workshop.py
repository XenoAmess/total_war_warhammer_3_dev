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
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from project import ModProject, add_mod_argument, selected_project
from workshop_media import apply_gallery, prepare_gallery
from workshop_metadata import apply_launcher_metadata, build_launcher_metadata
from account_confirmation import confirmed_idle

APP_ID = 1142710


def _html_account_activity(owner: str, observed: str) -> dict:
    request = urllib.request.Request(
        f'https://steamcommunity.com/profiles/{owner}/?l=english&presence_check={time.time_ns()}',
        headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read(512001)
        age = response.headers.get('Age', '0')
        server_date = response.headers.get('Date')
    if len(raw) > 512000 or not age.isdecimal() or int(age) > 5:
        raise RuntimeError('Steam account activity response is stale or invalid')
    html = raw.decode('utf-8')
    identity = re.search(r'g_rgProfileData\s*=\s*(\{.*?\});', html)
    if not identity or json.loads(identity[1]).get('steamid') != owner:
        raise RuntimeError('Steam returned another account profile')
    presence = re.findall(r'class="profile_in_game persona ([a-z_ -]+)"', html)
    status = 'UNAVAILABLE'
    if len(presence) == 1:
        classes = set(presence[0].split())
        if 'in-game' in classes or 'ingame' in classes:
            status = 'BUSY'
        elif (classes in ({'online'}, {'offline'}) and 'class="recent_games"' in html
              and 'profile_private_info' not in html):
            status = 'PUBLIC_PRESENCE_IDLE'
    return dict(owner=owner, status=status, online_state=presence[0] if presence else None,
                observed_at_utc=observed, server_date=server_date,
                source='steam_community_public_profile_html',
                response_sha256=hashlib.sha256(raw).hexdigest())


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
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(512001)
            age = response.headers.get('Age', '0')
            server_date = response.headers.get('Date')
    except urllib.error.HTTPError as error:
        if error.code != 429:
            raise
        return _html_account_activity(owner, observed)
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

    def wait(self, handle: int, result_type, callback: int, timeout: float = 180,
             check_agreement: bool = True, accepted_results: tuple[int, ...] = (1,)):
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
                if result.result not in accepted_results:
                    raise RuntimeError(f'Steam returned EResult={result.result}')
                if check_agreement and result.needs_agreement:
                    raise RuntimeError('Steam requires the account owner to accept the Workshop legal agreement')
                return result
            time.sleep(0.1)
        raise TimeoutError('Steam API call did not complete before timeout; preserve the saved item ID')


def validate_acceptance(pack: Path, acceptance: Path, project: ModProject,
                        native_waiver: Path | None = None) -> dict:
    sha = hashlib.sha256(pack.read_bytes()).hexdigest()
    results = json.loads(acceptance.read_text(encoding='utf-8'))
    if results.get('mod_id') != project.id or pack.name != project.pack_name:
        raise RuntimeError('Pack or acceptance record belongs to a different Mod')
    if results.get('release_pack_sha256') != sha or any(results.get(key) != 'PASS' for key in ('L0', 'L1')):
        raise RuntimeError('Publication requires L0/L1 PASS for this exact pack SHA-256')
    pending = [key for key in ('L2', 'L3') if results.get(key) != 'PASS']
    record = {key: results.get(key) for key in ('L0', 'L1', 'L2', 'L3')}
    if pending:
        if native_waiver is None:
            raise RuntimeError('Publication requires L0/L1/L2/L3 PASS or an explicit native-test waiver')
        waiver = json.loads(native_waiver.read_text(encoding='utf-8'))
        checks = waiver.get('deferred_checks')
        if (waiver.get('schema_version') != 1 or waiver.get('mod_id') != project.id
                or waiver.get('release_pack_sha256') != sha or waiver.get('authorized_by') != 'user'
                or not isinstance(checks, list) or not checks
                or any(key not in ('L2', 'L3') for key in checks)
                or not set(pending).issubset(checks)
                or not isinstance(waiver.get('instruction'), str) or not waiver['instruction'].strip()):
            raise RuntimeError('Native-test waiver must match this Mod, pack and deferred checks')
        record['native_test_waiver'] = {'file': str(native_waiver.resolve()),
                                      'sha256': hashlib.sha256(native_waiver.read_bytes()).hexdigest(),
                                      'deferred_checks': checks, 'instruction': waiver['instruction']}
    return record


def publish(dll: Path, pack: Path, acceptance: Path, state_path: Path, preview: Path | None,
            expected_owner: str | None = None, *, project: ModProject,
            native_waiver: Path | None = None, account_confirmation: dict | None = None):
    acceptance_record = validate_acceptance(pack, acceptance, project, native_waiver)
    sha = hashlib.sha256(pack.read_bytes()).hexdigest()
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    if state and state.get('mod_id') != project.id:
        raise RuntimeError('Stored Workshop state belongs to a different Mod')
    gallery = prepare_gallery(project, state)
    launcher_metadata = build_launcher_metadata(project)
    owner = expected_owner or state.get('owner')
    if not owner:
        raise RuntimeError('Specify --owner before creating a Workshop item')
    activity = (confirmed_idle(owner, account_confirmation) if account_confirmation is not None
                else account_activity(owner))
    if activity['status'] not in ('PUBLIC_PRESENCE_IDLE', 'USER_CONFIRMED_IDLE'):
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
        state['release_acceptance'] = acceptance_record
        if state.get('owner') and state['owner'] != steam.steam_id:
            raise RuntimeError('Stored Workshop item belongs to a different Steam account')
        if not state.get('item_id'):
            if state.get('status') == 'CREATING':
                raise RuntimeError('An earlier CreateItem has an unknown result; resolve its item ID before retrying')
            create = steam.bind('SteamAPI_ISteamUGC_CreateItem', C.c_uint64, C.c_void_p, C.c_uint32, C.c_int32)
            state.update(mod_id=project.id, owner=steam.steam_id, app_id=APP_ID, status='CREATING')
            save()
            result = steam.wait(create(steam.ugc, APP_ID, 0), CreateResult, 3403, check_agreement=False)
            state.update(item_id=str(result.item_id), owner=steam.steam_id, app_id=APP_ID, status='CREATED')
            save()
            if result.needs_agreement:
                raise RuntimeError('Steam requires the account owner to accept the Workshop legal agreement; item ID has been saved')
        add_dependency = steam.bind('SteamAPI_ISteamUGC_AddDependency', C.c_uint64,
                                    C.c_void_p, C.c_uint64, C.c_uint64)
        for child in project.required_items:
            result = steam.wait(add_dependency(steam.ugc, int(state['item_id']), child),
                                DependencyResult, 3412, check_agreement=False, accepted_results=(1, 29))
            if result.item_id != int(state['item_id']) or result.child_id != child:
                raise RuntimeError('Steam returned a dependency result for the wrong item')
        state['required_items'] = [str(item) for item in project.required_items]
        save()
        stage = project.build_dir / 'workshop-content'
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
            'SetItemTitle': project.metadata['title'],
            'SetItemDescription': (project.root / 'workshop/description.bbcode').read_text(encoding='utf-8'),
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
        tag_names = project.metadata.get('workshop', {}).get('tags', ['mod'])
        tag_values = (C.c_char_p * len(tag_names))(*(tag.encode('utf-8') for tag in tag_names))
        tags = Tags(tag_values, len(tag_names))
        set_tags = steam.bind('SteamAPI_ISteamUGC_SetItemTags', C.c_bool, C.c_void_p, C.c_uint64, C.POINTER(Tags))
        if not set_tags(steam.ugc, update, C.byref(tags)):
            raise RuntimeError('Workshop tags were rejected')
        apply_launcher_metadata(steam, update, launcher_metadata)
        apply_gallery(steam, update, gallery)
        submit = steam.bind('SteamAPI_ISteamUGC_SubmitItemUpdate', C.c_uint64, C.c_void_p, C.c_uint64, C.c_char_p)
        notes = (project.root / 'workshop/change-notes.txt').read_text(encoding='utf-8')
        state.update(status='UPLOADING', pack_sha256=sha)
        confirmed_gallery = [{key: value for key, value in record.items()
                              if key not in ('absolute_path', 'operation')} for record in gallery]
        if any(record['operation'] != 'skip' for record in gallery):
            state['gallery_pending'] = confirmed_gallery
        save()
        steam.wait(submit(steam.ugc, update, notes.encode('utf-8')), UpdateResult, 3404)
        if gallery:
            state['gallery'] = confirmed_gallery
        state.pop('gallery_pending', None)
        state.update(uploaded_version=project.metadata['version'], uploaded_title=project.metadata['title'],
                     launcher_metadata=launcher_metadata,
                     description_sha256=hashlib.sha256(fields['SetItemDescription'].encode('utf-8')).hexdigest())
        if preview:
            state['preview_sha256'] = hashlib.sha256(preview.read_bytes()).hexdigest()
        state.update(status='UPLOADED_PUBLIC_VERIFICATION_PENDING', url='https://steamcommunity.com/sharedfiles/filedetails/?id=' + state['item_id'])
        save()
        return state
    finally:
        steam.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    add_mod_argument(parser)
    parser.add_argument('--dll', type=Path, required=True)
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--acceptance', type=Path)
    parser.add_argument('--state', type=Path)
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--owner', help='Expected Steam account ID; required for the first publication')
    parser.add_argument('--native-waiver', type=Path, help='Explicit user authorization to defer L2/L3 for this exact Mod and pack')
    parser.add_argument('--account-confirmation', type=Path, help='Fresh explicit user statement that no other machine is running a Steam game')
    args = parser.parse_args()
    project = selected_project(parser, args.mod)
    preview = args.preview or project.build_dir / 'preview.png'
    print(json.dumps(publish(args.dll, args.pack or project.pack_path,
                             args.acceptance or project.root / 'docs/acceptance-results.json',
                             args.state or project.root / 'workshop/publication-state.json',
                             preview, args.owner, project=project, native_waiver=args.native_waiver,
                             account_confirmation=json.loads(args.account_confirmation.read_text(encoding='utf-8'))
                             if args.account_confirmation else None), indent=2))
