from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import hashlib,json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from account_confirmation import confirmed_idle
from project import ModProject
from workshop import publish

OWNER='76561198273714027'
NOW=datetime(2026,10,31,14,45,tzinfo=timezone.utc)
def confirmation():
    return dict(schema_version=1,owner=OWNER,authorized_by='user',source='user_current_session_statement',
                received_at_utc=(NOW-timedelta(seconds=20)).isoformat(),statement='All other Steam games have exited')

class AccountConfirmationTests(unittest.TestCase):
    def test_fresh_statement_retains_its_source_and_original_time(self):
        record=confirmation(); actual=confirmed_idle(OWNER,record,NOW)
        self.assertEqual(actual['status'],'USER_CONFIRMED_IDLE')
        self.assertEqual(actual['source'],record['source'])
        self.assertEqual(actual['observed_at_utc'],record['received_at_utc'])
        self.assertEqual(actual['statement'],record['statement'])

    def test_expired_future_naive_or_invalid_time_rejected(self):
        for value in ((NOW-timedelta(seconds=301)).isoformat(),(NOW+timedelta(seconds=6)).isoformat(),
                      '2026-10-31T14:45:00','invalid',None,True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                confirmed_idle(OWNER,dict(confirmation(),received_at_utc=value),NOW)

    def test_owner_schema_source_and_statement_must_be_explicit(self):
        for key,value in [('owner','76561198273714028'),('schema_version',True),('schema_version',2),
                          ('authorized_by','agent'),('source','cached_presence'),('statement','  '),('statement',True)]:
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                confirmed_idle(OWNER,dict(confirmation(),**{key:value}),NOW)
        for value in (None,[],True):
            with self.assertRaises(ValueError):confirmed_idle(OWNER,value,NOW)

    def test_bad_confirmation_never_contacts_network_or_initializes_sdk(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); pack=root/'test.pack'; pack.write_bytes(b'accepted')
            acceptance=root/'acceptance.json';acceptance.write_text(json.dumps(dict(mod_id='test',
                release_pack_sha256=hashlib.sha256(b'accepted').hexdigest(),L0='PASS',L1='PASS',L2='PASS',L3='PASS')))
            project=ModProject(root,{'id':'test','pack_name':'test.pack','workshop':{'game_version':'9.0.4.0'}})
            with patch('workshop.account_activity') as activity, patch('workshop.Steam') as sdk:
                with self.assertRaises(ValueError):
                    publish(root/'missing.dll',pack,acceptance,root/'state.json',None,OWNER,project=project,
                            account_confirmation=dict(confirmation(),owner='76561198273714028'))
                activity.assert_not_called();sdk.assert_not_called()

if __name__=='__main__':unittest.main()
