from __future__ import annotations

import hashlib
import ctypes as C
import json
import struct
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from pack import read_pack, write_loc, write_pack
from workshop import publish, Steam, DependencyResult, account_activity, validate_acceptance
from project import ModProject, load_project
from build import build


def publication_project(root: Path) -> ModProject:
    return ModProject(root, {'id': 'test_mod', 'pack_name': 'test.pack',
                             'title': 'Test Mod', 'version': '0.1.0'})


class ProjectTests(unittest.TestCase):
    def test_two_mods_with_the_same_pack_name_build_independently(self):
        with tempfile.TemporaryDirectory() as folder:
            repository = Path(folder)
            projects = []
            for name in ('first_mod', 'second_mod'):
                root = repository / 'mods' / name
                source = root / 'src/script/campaign/mod/example.lua'
                source.parent.mkdir(parents=True)
                source.write_text(name)
                (root / 'mod.json').write_text(json.dumps({
                    'schema_version': 1, 'id': name, 'title': name, 'version': '1.0.0',
                    'pack_name': 'same.pack'}))
                project = load_project(name, repository)
                result = build(project)
                self.assertEqual(result['mod_id'], name)
                self.assertEqual(read_pack(project.pack_path.read_bytes()),
                                 {'script/campaign/mod/example.lua': name.encode()})
                projects.append(project)
            second_before = projects[1].pack_path.read_bytes()
            build(projects[0])
            self.assertEqual(projects[1].pack_path.read_bytes(), second_before)
            self.assertNotEqual(projects[0].pack_path, projects[1].pack_path)

    def test_research_directory_cannot_be_built_as_a_mod(self):
        with tempfile.TemporaryDirectory() as folder:
            repository = Path(folder)
            (repository / 'mods/research_only').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'research-only'):
                load_project('research_only', repository)

    def test_mod_selector_cannot_escape_workspace(self):
        for name in ('../other_mod', '/absolute', 'a/b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                load_project(name)


class PackTests(unittest.TestCase):
    def test_paths_cannot_escape_pack(self):
        for key in ('../secret', '/absolute', 'a/../secret', 'a\\b'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                write_pack({key: b'test'})

    def test_sorted_pack_is_independent_of_insertion_order(self):
        self.assertEqual(write_pack({'b': b'2', 'a': b'1'}), write_pack({'a': b'1', 'b': b'2'}))

    def test_truncated_pack_rejected(self):
        with self.assertRaises(ValueError):
            read_pack(write_pack({'a': b'hello'})[:-1])

    def test_localisation_binary_layout(self):
        rows = {'xatw3_label': '刷新候选', 'xatw3_other': 'Move capital'}
        raw = write_loc(rows)
        self.assertEqual(raw[:6], b'\xff\xfeLOC\0')
        version, count = struct.unpack_from('<II', raw, 6)
        self.assertEqual((version, count), (1, 2))
        position, decoded = 14, {}
        for _ in range(count):
            strings = []
            for _ in range(2):
                length = struct.unpack_from('<H', raw, position)[0]
                position += 2
                strings.append(raw[position:position + length * 2].decode('utf-16-le'))
                position += length * 2
            self.assertEqual(raw[position], 0)
            position += 1
            decoded[strings[0]] = strings[1]
        self.assertEqual(position, len(raw))
        self.assertEqual(decoded, rows)


class PublicationGateTests(unittest.TestCase):
    def test_other_mod_acceptance_or_workshop_state_never_contacts_steam(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pack = root / 'test.pack'; pack.write_bytes(b'accepted fixture')
            acceptance = root / 'acceptance.json'; state = root / 'state.json'
            record = {'L0': 'PASS', 'L1': 'PASS', 'L2': 'PASS', 'L3': 'PASS',
                      'release_pack_sha256': hashlib.sha256(pack.read_bytes()).hexdigest()}
            for acceptance_mod, state_mod in (('another_mod', 'test_mod'), ('test_mod', 'another_mod')):
                acceptance.write_text(json.dumps(dict(record, mod_id=acceptance_mod)))
                state.write_text(json.dumps({'mod_id': state_mod, 'item_id': '123'}))
                with self.subTest(acceptance_mod=acceptance_mod, state_mod=state_mod), patch('workshop.account_activity') as activity, patch('workshop.Steam') as steam:
                    with self.assertRaisesRegex(RuntimeError, 'different Mod'):
                        publish(root / 'missing.dll', pack, acceptance, state, None,
                                '76561198273714027', project=publication_project(root))
                    activity.assert_not_called()
                    steam.assert_not_called()

    def test_miniprofile_detects_active_game_before_profile_xml(self):
        response = BytesIO(json.dumps({'in_game': {'name': 'Hearts of Iron IV'}}).encode())
        response.headers = {'Age': '0', 'Date': 'test date'}
        with patch('workshop.urllib.request.urlopen', return_value=response) as request:
            result = account_activity('76561198273714027')
        self.assertEqual((result['status'], result['game']), ('BUSY', 'Hearts of Iron IV'))
        self.assertEqual(request.call_count, 1)

    def test_absent_miniprofile_game_still_requires_public_profile_evidence(self):
        mini = BytesIO(b'{"in_game": null}'); mini.headers = {'Age': '0'}
        private = BytesIO(b'<profile><steamID64>76561198273714027</steamID64>'
                          b'<privacyState>private</privacyState><onlineState>offline</onlineState></profile>')
        private.headers = {'Age': '0'}
        with patch('workshop.urllib.request.urlopen', side_effect=[mini, private]):
            self.assertEqual(account_activity('76561198273714027')['status'], 'UNAVAILABLE')

    def test_rate_limited_xml_uses_fresh_official_profile_html(self):
        for state, recent, owner, age, expected in [
                ('online', True, '76561198273714027', '0', 'PUBLIC_PRESENCE_IDLE'),
                ('offline', True, '76561198273714027', '0', 'PUBLIC_PRESENCE_IDLE'),
                ('in-game', True, '76561198273714027', '0', 'BUSY'),
                ('online', False, '76561198273714027', '0', 'UNAVAILABLE'),
                ('online', True, '76561198273714028', '0', 'ERROR'),
                ('online', True, '76561198273714027', '120', 'ERROR')]:
            mini = BytesIO(b'{}'); mini.headers = {'Age': '0'}
            html = ('g_rgProfileData = {"steamid":"' + owner + '"};'
                    '<div class="profile_in_game persona ' + state + '"></div>'
                    + ('<div class="recent_games"></div>' if recent else ''))
            page = BytesIO(html.encode()); page.headers = {'Age': age}
            limited = HTTPError('https://steamcommunity.com/', 429, 'limited', {}, None)
            with self.subTest(state=state, recent=recent, owner=owner, age=age), patch(
                    'workshop.urllib.request.urlopen', side_effect=[mini, limited, page]):
                if expected == 'ERROR':
                    with self.assertRaises(RuntimeError):
                        account_activity('76561198273714027')
                else:
                    self.assertEqual(account_activity('76561198273714027')['status'], expected)

    def test_busy_or_unknown_account_never_initializes_game_sdk(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pack = root / 'test.pack'; pack.write_bytes(b'accepted fixture')
            acceptance = root / 'acceptance.json'
            acceptance.write_text(json.dumps({'mod_id': 'test_mod', 'L0': 'PASS', 'L1': 'PASS', 'L2': 'PASS', 'L3': 'PASS',
                                              'release_pack_sha256': hashlib.sha256(pack.read_bytes()).hexdigest()}))
            for status in ('BUSY', 'UNAVAILABLE'):
                with self.subTest(status=status), patch('workshop.account_activity', return_value={'status': status}), patch('workshop.Steam') as steam:
                    with self.assertRaisesRegex(RuntimeError, 'keep Steam offline and wait'):
                        publish(root / 'missing.dll', pack, acceptance, root / 'state.json', None, '76561198273714027', project=publication_project(root))
                    steam.assert_not_called()

    def test_dependency_callback_has_no_agreement_field(self):
        steam = Steam.__new__(Steam)
        steam.utils = 1
        steam.pump = lambda: None
        def get_result(utils, handle, output, size, callback, failed):
            self.assertEqual(callback, 3412)
            result = C.cast(output, C.POINTER(DependencyResult)).contents
            result.result, result.item_id, result.child_id = 1, 12, 34
            return True
        steam.bind = lambda name, *args: (get_result if name.endswith('GetAPICallResult') else lambda *args: True)
        result = steam.wait(1, DependencyResult, 3412, check_agreement=False)
        self.assertEqual((result.item_id, result.child_id), (12, 34))

    def test_existing_dependency_is_explicitly_accepted_but_other_callbacks_stay_strict(self):
        steam = Steam.__new__(Steam); steam.utils = 1; steam.pump = lambda: None
        def get_result(utils, handle, output, size, callback, failed):
            result = C.cast(output, C.POINTER(DependencyResult)).contents
            result.result, result.item_id, result.child_id = 29, 12, 34
            return True
        steam.bind = lambda name, *args: (get_result if name.endswith('GetAPICallResult') else lambda *args: True)
        result = steam.wait(1, DependencyResult, 3412, check_agreement=False, accepted_results=(1, 29))
        self.assertEqual((result.item_id, result.child_id), (12, 34))
        with self.assertRaisesRegex(RuntimeError, 'EResult=29'):
            steam.wait(1, DependencyResult, 3412, check_agreement=False)

    def test_failed_native_acceptance_never_contacts_steam(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pack = root / 'test.pack'
            pack.write_bytes(b'fixture')
            acceptance = root / 'acceptance.json'
            acceptance.write_text(json.dumps({'mod_id': 'test_mod', 'L0': 'PASS', 'L1': 'PASS', 'L2': 'BLOCKED', 'L3': 'NOT_RUN',
                                              'release_pack_sha256': hashlib.sha256(pack.read_bytes()).hexdigest()}))
            with patch('workshop.Steam') as steam, self.assertRaisesRegex(RuntimeError, 'requires L0/L1/L2/L3 PASS'):
                publish(root / 'missing.dll', pack, acceptance, root / 'state.json', None, project=publication_project(root))
            steam.assert_not_called()

    def test_explicit_matching_waiver_preserves_pending_native_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); pack = root / 'test.pack'; pack.write_bytes(b'fixture')
            sha = hashlib.sha256(pack.read_bytes()).hexdigest()
            acceptance = root / 'acceptance.json'
            acceptance.write_text(json.dumps(dict(mod_id='test_mod', release_pack_sha256=sha,
                                                  L0='PASS', L1='PASS', L2='IN_PROGRESS', L3='NOT_RUN')))
            waiver = root / 'waiver.json'
            waiver.write_text(json.dumps(dict(schema_version=1, mod_id='test_mod', release_pack_sha256=sha,
                                              authorized_by='user', deferred_checks=['L2', 'L3'],
                                              instruction='Publish now; complete native testing later.')))
            result = validate_acceptance(pack, acceptance, publication_project(root), waiver)
            self.assertEqual((result['L2'], result['L3']), ('IN_PROGRESS', 'NOT_RUN'))
            self.assertEqual(result['native_test_waiver']['sha256'], hashlib.sha256(waiver.read_bytes()).hexdigest())
            for field, value in [('mod_id', 'other_mod'), ('release_pack_sha256', '0' * 64),
                                 ('deferred_checks', ['L2']), ('deferred_checks', ['L0', 'L2', 'L3']),
                                 ('authorized_by', 'tool'), ('instruction', '')]:
                with self.subTest(field=field, value=value):
                    original = waiver.read_text()
                    changed = json.loads(original); changed[field] = value; waiver.write_text(json.dumps(changed))
                    with self.assertRaises(RuntimeError):
                        validate_acceptance(pack, acceptance, publication_project(root), waiver)
                    waiver.write_text(original)
            failed = json.loads(acceptance.read_text()); failed['L1'] = 'FAIL'; acceptance.write_text(json.dumps(failed))
            with self.assertRaisesRegex(RuntimeError, 'L0/L1 PASS'):
                validate_acceptance(pack, acceptance, publication_project(root), waiver)

    def test_unaccepted_pack_hash_never_contacts_steam(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pack = root / 'test.pack'; pack.write_bytes(b'changed')
            acceptance = root / 'acceptance.json'
            acceptance.write_text(json.dumps({'L0': 'PASS', 'L1': 'PASS', 'L2': 'PASS', 'L3': 'PASS',
                                              'release_pack_sha256': 'different'}))
            with patch('workshop.Steam') as steam, self.assertRaises(RuntimeError):
                publish(root / 'missing.dll', pack, acceptance, root / 'state.json', None, project=publication_project(root))
            steam.assert_not_called()


if __name__ == '__main__':
    unittest.main()
