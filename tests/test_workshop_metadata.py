from __future__ import annotations

import ctypes as C
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from workshop_metadata import build_launcher_metadata, apply_launcher_metadata
from project import ModProject
from workshop import publish


class BuildLauncherMetadataTests(unittest.TestCase):
    def test_invalid_inputs_and_explicit_tested_version(self):
        valid = {'pack_name': 'test.pack', 'workshop': {'game_version': '9.0.4.0'}}
        for value in (None, True, 9040, '', '9.0.4', '9.0.4.0\n', '9.0.-1.0',
                      '9.0.65536.0', '65536.0.0.0', '0.9.0.0', '09.0.4.0'):
            with self.subTest(version=value), self.assertRaises(ValueError):
                build_launcher_metadata(ModProject(Path('.'), dict(valid, workshop={'game_version': value})))
        for value in ('../test.pack', 'a/b.pack', 'a\\b.pack', 'TEST.pack', 'a\0.pack', 'a'*251+'.pack', True):
            with self.subTest(pack=value), self.assertRaises(ValueError):
                build_launcher_metadata(ModProject(Path('.'), dict(valid, pack_name=value)))
        self.assertEqual(build_launcher_metadata(ModProject(Path('.'), dict(valid,
            workshop={'game_version': '9.1.65535.65535'})))['game_version'], '589825')

    def test_invalid_metadata_fails_before_account_or_sdk(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); pack = root/'test.pack'; pack.write_bytes(b'accepted')
            acceptance = root/'acceptance.json'
            acceptance.write_text(json.dumps(dict(mod_id='test', release_pack_sha256=hashlib.sha256(b'accepted').hexdigest(),
                L0='PASS', L1='PASS', L2='PASS', L3='PASS')))
            project = ModProject(root, {'id': 'test', 'pack_name': 'test.pack'})
            with patch('workshop.account_activity') as account, patch('workshop.Steam') as sdk:
                with self.assertRaisesRegex(ValueError, 'game_version'):
                    publish(root/'missing.dll', pack, acceptance, root/'state.json', None, project=project)
                account.assert_not_called(); sdk.assert_not_called()

    def test_valid(self):
        proj = ModProject(Path('.'), {
            'id': 'test', 'pack_name': 'test.pack', 'title': 'T', 'version': '1.0',
            'workshop': {'game_version': '9.0.4.0'}
        })
        res = build_launcher_metadata(proj)
        self.assertEqual(res, {'pack_name': 'test.pack', 'game_version': '589824'})

    def test_invalid_pack(self):
        proj = ModProject(Path('.'), {
            'id': 'test', 'pack_name': 'Test.Pack', 'title': 'T', 'version': '1.0',
            'workshop': {'game_version': '9.0.4.0'}
        })
        with self.assertRaises(ValueError):
            build_launcher_metadata(proj)

    def test_missing_version(self):
        proj = ModProject(Path('.'), {
            'id': 'test', 'pack_name': 'test.pack', 'title': 'T', 'version': '1.0',
            'workshop': {}
        })
        with self.assertRaises(ValueError):
            build_launcher_metadata(proj)

    def test_zero_major(self):
        proj = ModProject(Path('.'), {
            'id': 'test', 'pack_name': 'test.pack', 'title': 'T', 'version': '1.0',
            'workshop': {'game_version': '0.0.0.0'}
        })
        with self.assertRaises(ValueError):
            build_launcher_metadata(proj)

    def test_bool_version(self):
        proj = ModProject(Path('.'), {
            'id': 'test', 'pack_name': 'test.pack', 'title': 'T', 'version': '1.0',
            'workshop': {'game_version': True}
        })
        with self.assertRaises(ValueError):
            build_launcher_metadata(proj)


class ApplyLauncherMetadataTests(unittest.TestCase):
    def test_replacement_preserves_unowned_tags_and_exact_signatures(self):
        tags = {'other': ['keep'], 'pack_name': ['old.pack','duplicate.pack'], 'game_version': ['1']}
        bindings, calls = [], []
        class FakeSteam:
            ugc = 17
            def bind(self, name, result, *args):
                bindings.append((name, result, args))
                def invoke(ugc, update, key, *value):
                    calls.append((ugc, update, key, value))
                    if value: tags.setdefault(key.decode(), []).append(value[0].decode())
                    else: tags.pop(key.decode(), None)
                    return True
                return invoke
        for _ in range(2):
            apply_launcher_metadata(FakeSteam(), 99, {'pack_name': 'test.pack', 'game_version': '589824'})
            self.assertEqual(tags, {'other': ['keep'], 'pack_name': ['test.pack'], 'game_version': ['589824']})
        self.assertEqual(bindings[:2], [
            ('SteamAPI_ISteamUGC_RemoveItemKeyValueTags', C.c_bool, (C.c_void_p,C.c_uint64,C.c_char_p)),
            ('SteamAPI_ISteamUGC_AddItemKeyValueTag', C.c_bool, (C.c_void_p,C.c_uint64,C.c_char_p,C.c_char_p))])
        self.assertEqual(calls[:4], [(17,99,b'pack_name',()),(17,99,b'game_version',()),
            (17,99,b'pack_name',(b'test.pack',)),(17,99,b'game_version',(b'589824',))])

    def test_each_rejected_call_stops_immediately(self):
        for fail_at in range(4):
            calls = []
            class FakeSteam:
                ugc = 1
                def bind(self, name, *signature):
                    def invoke(*args):
                        calls.append(name)
                        return len(calls)-1 != fail_at
                    return invoke
            with self.subTest(fail_at=fail_at), self.assertRaises(RuntimeError):
                apply_launcher_metadata(FakeSteam(), 99, {'pack_name': 'test.pack', 'game_version': '589824'})
            self.assertEqual(len(calls), fail_at+1)

    def test_invalid_handles_and_values_never_bind(self):
        for handle in (None, True, -1, 0, 1.5, '99', 2**64-1, 2**64):
            with self.subTest(handle=handle), self.assertRaises(ValueError):
                apply_launcher_metadata(None, handle, {'pack_name':'test.pack','game_version':'589824'})
        for value in ('0', '1', '0589824', '５８９８２４', '4294967296', '1\0', True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                apply_launcher_metadata(None, 99, {'pack_name':'test.pack','game_version':value})

    def test_success(self):
        calls = []
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                def fn(*a):
                    calls.append((name, a))
                    return True
                return fn

        steam = FakeSteam()
        apply_launcher_metadata(steam, 99, {'pack_name': 'test.pack', 'game_version': '589824'})

        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0][0], 'SteamAPI_ISteamUGC_RemoveItemKeyValueTags')
        self.assertEqual(calls[1][0], 'SteamAPI_ISteamUGC_RemoveItemKeyValueTags')
        self.assertEqual(calls[2][0], 'SteamAPI_ISteamUGC_AddItemKeyValueTag')
        self.assertEqual(calls[3][0], 'SteamAPI_ISteamUGC_AddItemKeyValueTag')

    def test_remove_fail(self):
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if 'Remove' in name:
                    return lambda *a: False
                return lambda *a: True

        with self.assertRaises(RuntimeError):
            apply_launcher_metadata(FakeSteam(), 99, {'pack_name': 'test.pack', 'game_version': '589824'})

    def test_add_fail(self):
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if 'Add' in name:
                    return lambda *a: False
                return lambda *a: True

        with self.assertRaises(RuntimeError):
            apply_launcher_metadata(FakeSteam(), 99, {'pack_name': 'test.pack', 'game_version': '589824'})

    def test_invalid_handle(self):
        with self.assertRaises(ValueError):
            apply_launcher_metadata(None, 0, {'pack_name': 'test.pack', 'game_version': '589824'})

    def test_invalid_metadata_keys(self):
        with self.assertRaises(ValueError):
            apply_launcher_metadata(None, 99, {'pack_name': 'test.pack'})

    def test_invalid_metadata_values(self):
        with self.assertRaises(ValueError):
            apply_launcher_metadata(None, 99, {'pack_name': 'test.pack', 'game_version': 'not-a-number'})

if __name__ == '__main__':
    unittest.main()
