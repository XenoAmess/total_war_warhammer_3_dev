from __future__ import annotations

import ctypes as C
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from workshop_media import prepare_gallery, apply_gallery
from project import ModProject
from workshop import publish


def make_project(root: Path) -> ModProject:
    (root / 'workshop').mkdir(exist_ok=True)
    return ModProject(root, {'id': 'test_mod', 'pack_name': 'test.pack',
                             'title': 'Test Mod', 'version': '0.1.0',
                             'workshop': {'game_version': '9.0.4.0'}})


def write_screenshot(root: Path, name: str, content: bytes = b'PNG') -> Path:
    path = root / 'workshop' / 'screenshots' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PrepareGalleryTests(unittest.TestCase):
    def test_missing_manifest_returns_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            result = prepare_gallery(project, {})
            self.assertEqual(result, [])

    def test_valid_single_add(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            shot = write_screenshot(root, 'shot.png', b'PNGDATA')
            sha = sha256_hex(b'PNGDATA')
            url = 'https://raw.githubusercontent.com/test/shot.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'shot.png', 'sha256': sha, 'caption': 'A shot', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            result = prepare_gallery(project, {})
            self.assertEqual(len(result), 1)
            rec = result[0]
            self.assertEqual(rec['file'], 'shot.png')
            self.assertEqual(rec['operation'], 'add')
            self.assertEqual(rec['index'], 0)
            self.assertEqual(rec['sha256'], sha)
            self.assertEqual(rec['url'], url)
            self.assertEqual(rec['caption'], 'A shot')
            self.assertTrue(rec['absolute_path'].endswith('shot.png'))

    def test_skip_identical_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            shot = write_screenshot(root, 'shot.png', b'PNGDATA')
            sha = sha256_hex(b'PNGDATA')
            url = 'https://raw.githubusercontent.com/test/shot.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'shot.png', 'sha256': sha, 'caption': 'A shot', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            state = {'gallery': [{'file': 'shot.png', 'sha256': sha, 'index': 0}]}
            result = prepare_gallery(project, state)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['operation'], 'skip')

    def test_update_changed_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            shot = write_screenshot(root, 'shot.png', b'NEWDATA')
            sha = sha256_hex(b'NEWDATA')
            old_sha = sha256_hex(b'OLDDATA')
            url = 'https://raw.githubusercontent.com/test/shot.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'shot.png', 'sha256': sha, 'caption': 'Updated', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            state = {'gallery': [{'file': 'shot.png', 'sha256': old_sha, 'index': 0}]}
            result = prepare_gallery(project, state)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['operation'], 'update')
            self.assertEqual(result[0]['index'], 0)

    def test_append_new_after_confirmed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            s1 = write_screenshot(root, 'a.png', b'A')
            s2 = write_screenshot(root, 'b.png', b'B')
            sha1 = sha256_hex(b'A')
            sha2 = sha256_hex(b'B')
            url1 = 'https://raw.githubusercontent.com/test/a.png'
            url2 = 'https://raw.githubusercontent.com/test/b.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [
                    {'file': 'a.png', 'sha256': sha1, 'caption': 'A', 'url': url1},
                    {'file': 'b.png', 'sha256': sha2, 'caption': 'B', 'url': url2},
                ]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url1}[/img]\n[img]{url2}[/img]', encoding='utf-8')
            state = {'gallery': [{'file': 'a.png', 'sha256': sha1, 'index': 0}]}
            result = prepare_gallery(project, state)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['operation'], 'skip')
            self.assertEqual(result[1]['operation'], 'add')
            self.assertEqual(result[1]['index'], 1)

    def test_reject_reorder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            s1 = write_screenshot(root, 'a.png', b'A')
            s2 = write_screenshot(root, 'b.png', b'B')
            sha1 = sha256_hex(b'A')
            sha2 = sha256_hex(b'B')
            url1 = 'https://raw.githubusercontent.com/test/a.png'
            url2 = 'https://raw.githubusercontent.com/test/b.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [
                    {'file': 'b.png', 'sha256': sha2, 'caption': 'B', 'url': url2},
                    {'file': 'a.png', 'sha256': sha1, 'caption': 'A', 'url': url1},
                ]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url2}[/img]\n[img]{url1}[/img]', encoding='utf-8')
            state = {'gallery': [{'file': 'a.png', 'sha256': sha1, 'index': 0}, {'file': 'b.png', 'sha256': sha2, 'index': 1}]}
            with self.assertRaisesRegex(RuntimeError, 'reordered'):
                prepare_gallery(project, state)

    def test_reject_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            s1 = write_screenshot(root, 'a.png', b'A')
            sha1 = sha256_hex(b'A')
            url1 = 'https://raw.githubusercontent.com/test/a.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': sha1, 'caption': 'A', 'url': url1}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url1}[/img]', encoding='utf-8')
            state = {'gallery': [{'file': 'a.png', 'sha256': sha1, 'index': 0}, {'file': 'b.png', 'sha256': 'x', 'index': 1}]}
            with self.assertRaisesRegex(RuntimeError, 'cannot remove'):
                prepare_gallery(project, state)

    def test_reject_gallery_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            with self.assertRaisesRegex(RuntimeError, 'gallery_pending'):
                prepare_gallery(project, {'gallery_pending': True})

    def test_reject_duplicate_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            s1 = write_screenshot(root, 'a.png', b'A')
            sha1 = sha256_hex(b'A')
            url1 = 'https://raw.githubusercontent.com/test/a.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [
                    {'file': 'a.png', 'sha256': sha1, 'caption': 'A', 'url': url1},
                    {'file': 'a.png', 'sha256': sha1, 'caption': 'A', 'url': url1},
                ]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url1}[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'duplicate'):
                prepare_gallery(project, {})

    def test_reject_unsafe_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': '../escape.png', 'sha256': '0' * 64, 'caption': 'X', 'url': 'https://x.com/y'}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text('[img]https://x.com/y[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'unsafe'):
                prepare_gallery(project, {})

    def test_reject_bad_sha(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'a.png', b'A')
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': 'not-hex', 'caption': 'A', 'url': 'https://x.com/y'}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text('[img]https://x.com/y[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'malformed sha256'):
                prepare_gallery(project, {})

    def test_reject_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'a.png', b'A')
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/y'}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text('[img]https://x.com/y[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'sha256 mismatch'):
                prepare_gallery(project, {})

    def test_reject_too_large(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            big = b'X' * 1048576
            write_screenshot(root, 'big.png', big)
            sha = sha256_hex(big)
            url = 'https://raw.githubusercontent.com/test/big.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'big.png', 'sha256': sha, 'caption': 'Big', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'too large'):
                prepare_gallery(project, {})

    def test_reject_empty_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'empty.png', b'')
            sha = sha256_hex(b'')
            url = 'https://raw.githubusercontent.com/test/empty.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'empty.png', 'sha256': sha, 'caption': 'Empty', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'empty'):
                prepare_gallery(project, {})

    def test_reject_missing_embed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'a.png', b'A')
            sha = sha256_hex(b'A')
            url = 'https://raw.githubusercontent.com/test/a.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': sha, 'caption': 'A', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text('no embed here', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'inline embed mismatch'):
                prepare_gallery(project, {})

    def test_reject_duplicate_embed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'a.png', b'A')
            sha = sha256_hex(b'A')
            url = 'https://raw.githubusercontent.com/test/a.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': sha, 'caption': 'A', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img] [img]{url}[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'inline embed mismatch'):
                prepare_gallery(project, {})

    def test_reject_http_url(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            write_screenshot(root, 'a.png', b'A')
            sha = sha256_hex(b'A')
            url = 'http://raw.githubusercontent.com/test/a.png'
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'a.png', 'sha256': sha, 'caption': 'A', 'url': url}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'HTTPS'):
                prepare_gallery(project, {})

    def test_reject_disallowed_suffix(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = make_project(root)
            (root / 'workshop' / 'screenshots').mkdir(parents=True, exist_ok=True)
            (root / 'workshop' / 'screenshots' / 'bad.txt').write_text('x')
            (root / 'workshop' / 'screenshots.json').write_text(json.dumps({
                'screenshots': [{'file': 'bad.txt', 'sha256': '0' * 64, 'caption': 'X', 'url': 'https://x.com/y'}]
            }), encoding='utf-8')
            (root / 'workshop' / 'description.bbcode').write_text('[img]https://x.com/y[/img]', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'disallowed'):
                prepare_gallery(project, {})


class ApplyGalleryTests(unittest.TestCase):
    def test_add_calls_add_item_preview(self):
        calls = []
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if name == 'SteamAPI_ISteamUGC_AddItemPreviewFile':
                    def fn(ugc, update, path, ptype):
                        calls.append(('add', ugc, update, path, ptype))
                        return True
                    return fn
                if name == 'SteamAPI_ISteamUGC_UpdateItemPreviewFile':
                    def fn(ugc, update, index, path):
                        calls.append(('update', ugc, update, index, path))
                        return True
                    return fn
                raise AssertionError(f'unexpected bind: {name}')
        steam = FakeSteam()
        records = [{'file': 'a.png', 'absolute_path': '/tmp/a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/a', 'index': 0, 'operation': 'add'}]
        apply_gallery(steam, 99, records)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 'add')
        self.assertEqual(calls[0][1], 1)
        self.assertEqual(calls[0][2], 99)
        self.assertEqual(calls[0][3], b'/tmp/a.png')
        self.assertEqual(calls[0][4], 0)

    def test_update_calls_update_item_preview(self):
        calls = []
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if name == 'SteamAPI_ISteamUGC_AddItemPreviewFile':
                    def fn(ugc, update, path, ptype):
                        calls.append(('add', ugc, update, path, ptype))
                        return True
                    return fn
                if name == 'SteamAPI_ISteamUGC_UpdateItemPreviewFile':
                    def fn(ugc, update, index, path):
                        calls.append(('update', ugc, update, index, path))
                        return True
                    return fn
                raise AssertionError(f'unexpected bind: {name}')
        steam = FakeSteam()
        records = [{'file': 'a.png', 'absolute_path': '/tmp/a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/a', 'index': 0, 'operation': 'update'}]
        apply_gallery(steam, 99, records)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 'update')
        self.assertEqual(calls[0][3], 0)

    def test_skip_makes_no_calls(self):
        calls = []
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                calls.append(name)
                raise AssertionError('should not bind for skip')
        steam = FakeSteam()
        records = [{'file': 'a.png', 'absolute_path': '/tmp/a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/a', 'index': 0, 'operation': 'skip'}]
        apply_gallery(steam, 99, records)
        self.assertEqual(calls, [])

    def test_add_rejection_raises(self):
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if name == 'SteamAPI_ISteamUGC_AddItemPreviewFile':
                    return lambda *a: False
                if name == 'SteamAPI_ISteamUGC_UpdateItemPreviewFile':
                    return lambda *a: True
                raise AssertionError(f'unexpected bind: {name}')
        steam = FakeSteam()
        records = [{'file': 'a.png', 'absolute_path': '/tmp/a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/a', 'index': 0, 'operation': 'add'}]
        with self.assertRaisesRegex(RuntimeError, 'AddItemPreviewFile rejected'):
            apply_gallery(steam, 99, records)

    def test_update_rejection_raises(self):
        class FakeSteam:
            ugc = 1
            def bind(self, name, *args):
                if name == 'SteamAPI_ISteamUGC_AddItemPreviewFile':
                    return lambda *a: True
                if name == 'SteamAPI_ISteamUGC_UpdateItemPreviewFile':
                    return lambda *a: False
                raise AssertionError(f'unexpected bind: {name}')
        steam = FakeSteam()
        records = [{'file': 'a.png', 'absolute_path': '/tmp/a.png', 'sha256': '0' * 64, 'caption': 'A', 'url': 'https://x.com/a', 'index': 0, 'operation': 'update'}]
        with self.assertRaisesRegex(RuntimeError, 'UpdateItemPreviewFile rejected'):
            apply_gallery(steam, 99, records)


class PublicationGalleryTests(unittest.TestCase):
    def test_submission_confirmation_and_unknown_result(self):
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                project = make_project(root)
                shot = write_screenshot(root, 'shot.png', b'actual-capture-fixture')
                url = 'https://example.org/shot.png'
                manifest = {'screenshots': [{'file': shot.name, 'sha256': sha256_hex(shot.read_bytes()),
                                             'caption': 'Feature screenshot', 'url': url}]}
                (root / 'workshop/screenshots.json').write_text(json.dumps(manifest), encoding='utf-8')
                (root / 'workshop/description.bbcode').write_text(f'[img]{url}[/img]', encoding='utf-8')
                (root / 'workshop/change-notes.txt').write_text('0.1.0', encoding='utf-8')
                project.build_dir.mkdir()
                project.pack_path.write_bytes(b'accepted-pack')
                acceptance = root / 'acceptance.json'
                acceptance.write_text(json.dumps(dict(mod_id=project.id, release_pack_sha256=sha256_hex(b'accepted-pack'),
                                                      L0='PASS', L1='PASS', L2='PASS', L3='PASS')))
                state_path = root / 'workshop/publication-state.json'
                owner = '76561198273714027'
                state_path.write_text(json.dumps(dict(mod_id=project.id, owner=owner, item_id='123')))
                calls = []

                class FakeSteam:
                    ugc = 1
                    steam_id = owner

                    def __init__(self, dll):
                        calls.append('initialized')

                    def bind(self, name, *signature):
                        def invoke(*args):
                            calls.append(name)
                            if name.endswith('SubmitItemUpdate'):
                                self_test.assertEqual(calls.count('SteamAPI_ISteamUGC_RemoveItemKeyValueTags'), 2)
                                self_test.assertEqual(calls.count('SteamAPI_ISteamUGC_AddItemKeyValueTag'), 2)
                                pending = json.loads(state_path.read_text())['gallery_pending']
                                self_test.assertEqual(pending[0]['sha256'], manifest['screenshots'][0]['sha256'])
                            return 99
                        return invoke

                    def wait(self, handle, *args, **kwargs):
                        if interrupted:
                            raise TimeoutError('Unknown submit result')
                        return SimpleNamespace(result=1, needs_agreement=False)

                    def shutdown(self):
                        calls.append('shutdown')

                self_test = self
                with patch('workshop.Steam', FakeSteam), patch('workshop.account_activity', return_value={'status': 'PUBLIC_PRESENCE_IDLE'}):
                    if interrupted:
                        with self.assertRaises(TimeoutError):
                            publish(root / 'dummy.dll', project.pack_path, acceptance, state_path, None, owner, project=project)
                    else:
                        publish(root / 'dummy.dll', project.pack_path, acceptance, state_path, None, owner, project=project)
                state = json.loads(state_path.read_text())
                self.assertIn('SteamAPI_ISteamUGC_AddItemPreviewFile', calls)
                self.assertEqual(calls[-1], 'shutdown')
                if interrupted:
                    self.assertIn('gallery_pending', state)
                    self.assertNotIn('gallery', state)
                    with patch('workshop.Steam') as sdk:
                        with self.assertRaisesRegex(RuntimeError, 'gallery_pending'):
                            publish(root / 'dummy.dll', project.pack_path, acceptance, state_path, None, owner, project=project)
                        sdk.assert_not_called()
                else:
                    self.assertNotIn('gallery_pending', state)
                    self.assertEqual(state['gallery'][0]['sha256'], manifest['screenshots'][0]['sha256'])
                    self.assertEqual(state['uploaded_version'], '0.1.0')
                    self.assertEqual(state['launcher_metadata'], {'pack_name': 'test.pack', 'game_version': '589824'})

    def test_empty_manifest_cannot_remove_confirmed_gallery(self):
        with tempfile.TemporaryDirectory() as folder:
            project = make_project(Path(folder))
            (project.root / 'workshop/screenshots.json').write_text('{"screenshots": []}')
            with self.assertRaisesRegex(RuntimeError, 'cannot remove'):
                prepare_gallery(project, {'gallery': [{'file': 'old.png', 'index': 0}]})


if __name__ == '__main__':
    unittest.main()
