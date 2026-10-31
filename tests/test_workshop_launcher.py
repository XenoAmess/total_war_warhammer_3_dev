from pathlib import Path
from types import SimpleNamespace
import ctypes as C
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from project import load_project
from workshop_metadata import build_launcher_metadata
from workshop_launcher import QueryCompleted, query_launcher_metadata, repair_launcher_metadata


class FakeSteam:
    ugc = 17

    def __init__(self, data, fail=None):
        self.data, self.fail, self.calls, self.queries = data, fail, [], 0
        self.cached, self.returned, self.wrong_handle = False, 1, False

    def bind(self, name, result, *signature):
        short = name.removeprefix('SteamAPI_ISteamUGC_')
        def invoke(*args):
            self.calls.append((short, args))
            if short == self.fail:
                return False
            if short == 'CreateQueryUGCDetailsRequest':
                self.queries += 1
                self.query = 200 + self.queries
                return self.query
            if short == 'SendQueryUGCRequest': return 300 + self.queries
            if short == 'GetQueryUGCNumKeyValueTags': return len(self.data[self.queries-1])
            if short == 'GetQueryUGCKeyValueTag':
                key, value = self.data[self.queries-1][args[3]]
                args[4].value, args[6].value = key, value
                return True
            if short == 'StartItemUpdate': return 400
            if short == 'SubmitItemUpdate': return 500
            if short in ('SetReturnKeyValueTags', 'SetAllowCachedResponse', 'ReleaseQueryUGCRequest',
                         'RemoveItemKeyValueTags', 'AddItemKeyValueTag'): return True
            raise AssertionError('Forbidden/unexpected API: '+short)
        return invoke

    def wait(self, handle, result, callback, **kwargs):
        self.calls.append(('wait', (handle, callback)))
        if callback == 3401:
            assert result == QueryCompleted and kwargs == {'check_agreement': False, 'timeout':45}
            return SimpleNamespace(handle=self.query+int(self.wrong_handle), returned=self.returned, cached=self.cached)
        assert callback == 3404
        if self.fail == 'submit_timeout': raise TimeoutError('Unknown submit outcome')
        return SimpleNamespace(result=1, needs_agreement=False)


EXPECTED = {'pack_name': 'test.pack', 'game_version': '589824'}
TAGS = [(k.encode(), v.encode()) for k,v in EXPECTED.items()]


class LauncherRepairTests(unittest.TestCase):
    def test_both_real_mods_keep_distinct_pack_identity(self):
        for mod, pack in [('recruitment_refresh','xatw3_campaign_utilities.pack'), ('move_capital','xatw3_move_capital.pack')]:
            with self.subTest(mod=mod):
                self.assertEqual(build_launcher_metadata(load_project(mod)), {'pack_name':pack,'game_version':'589824'})

    def test_query_abi_buffers_duplicates_and_no_cache(self):
        self.assertEqual((C.sizeof(QueryCompleted), QueryCompleted.cursor.offset), (280,21))
        steam = FakeSteam([[*TAGS, (b'other',b'value'), (b'pack_name',b'old.pack')]])
        actual = query_launcher_metadata(steam, 123)
        self.assertEqual(actual['pack_name'], ['test.pack','old.pack'])
        self.assertIn(('SetAllowCachedResponse',(17,201,0)), steam.calls)
        self.assertEqual(steam.calls[-1], ('ReleaseQueryUGCRequest',(17,201)))

    def test_every_query_setup_failure_releases_handle(self):
        for fail in ('SetReturnKeyValueTags','SetAllowCachedResponse','SendQueryUGCRequest','GetQueryUGCKeyValueTag'):
            steam = FakeSteam([TAGS],fail)
            with self.subTest(fail=fail), self.assertRaises(RuntimeError): query_launcher_metadata(steam,123)
            self.assertEqual(steam.calls[-1][0], 'ReleaseQueryUGCRequest')

    def test_cached_wrong_or_missing_results_are_rejected_and_released(self):
        for field, value in [('cached',True),('returned',0),('wrong_handle',True)]:
            steam = FakeSteam([TAGS]); setattr(steam,field,value)
            with self.subTest(field=field), self.assertRaises(RuntimeError): query_launcher_metadata(steam,123)
            self.assertEqual(steam.calls[-1][0], 'ReleaseQueryUGCRequest')

    def test_matching_metadata_is_read_only(self):
        steam = FakeSteam([TAGS])
        self.assertEqual(repair_launcher_metadata(steam,123,EXPECTED)['status'],'SKIPPED')
        self.assertFalse(any('Update' in name or name.startswith(('Add','Remove')) for name,_ in steam.calls))

    def test_server_canonical_key_case_is_accepted_without_republishing(self):
        steam = FakeSteam([[(b'PACK_NAME',b'test.pack'),(b'game_version',b'589824')]])
        receipt = repair_launcher_metadata(steam,123,EXPECTED)
        self.assertEqual(receipt['status'],'SKIPPED')
        self.assertIn('PACK_NAME',receipt['after'])
        self.assertFalse(any(name=='StartItemUpdate' for name,_ in steam.calls))

    def test_mixed_case_duplicates_are_repaired(self):
        steam = FakeSteam([[*TAGS,(b'PACK_NAME',b'old.pack')],[(b'PACK_NAME',b'test.pack'),(b'game_version',b'589824')]])
        self.assertEqual(repair_launcher_metadata(steam,123,EXPECTED)['status'],'REPAIRED')

    def test_repair_changes_only_owned_metadata_and_verifies_remote_values(self):
        steam = FakeSteam([[(b'other',b'keep')], [*TAGS,(b'other',b'keep')]])
        receipt = repair_launcher_metadata(steam,123,EXPECTED)
        self.assertEqual(receipt['status'],'REPAIRED')
        self.assertEqual(receipt['after']['other'],['keep'])
        self.assertEqual([args[2] for name,args in steam.calls if name=='RemoveItemKeyValueTags'],[b'pack_name',b'game_version'])
        self.assertEqual(sum(name=='SubmitItemUpdate' for name,_ in steam.calls),1)

    def test_unknown_submit_or_failed_readback_never_replays_update(self):
        for fail in ('submit_timeout',None):
            steam = FakeSteam([[],[]],fail)
            with self.subTest(fail=fail), self.assertRaises((TimeoutError,RuntimeError)):
                repair_launcher_metadata(steam,123,EXPECTED)
            self.assertEqual(sum(name=='SubmitItemUpdate' for name,_ in steam.calls),1)

    def test_invalid_input_never_starts_query_or_update(self):
        for item in (True,0,-1,2**64-1):
            with self.subTest(item=item), self.assertRaises(ValueError): query_launcher_metadata(None,item)
        for metadata in ({},dict(EXPECTED,pack_name='../bad.pack'),dict(EXPECTED,game_version='0')):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError): repair_launcher_metadata(None,123,metadata)


if __name__ == '__main__': unittest.main()
