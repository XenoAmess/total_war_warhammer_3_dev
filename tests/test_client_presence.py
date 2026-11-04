from datetime import timedelta
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from test_account_confirmation import OWNER, NOW
from account_confirmation import confirmed_idle_client_persona
from project import ModProject
from workshop import publish


def receipt():
    return dict(schema_version=1, owner=OWNER,
                source='live_own_account_persona_on_authenticated_server_connection',
                offline=False, server_connected=True, server_logged_on=True,
                initial_connection_complete=True, initialized=True, statusInitialized=True,
                persona=3, app=0, gameid='0', game='', age_ms=178.2,
                observed_at_utc=(NOW-timedelta(seconds=2)).isoformat())


class ClientPresenceTests(unittest.TestCase):
    def test_valid_evidence_retains_source_and_connection_fields(self):
        actual = confirmed_idle_client_persona(OWNER, receipt(), NOW)
        self.assertEqual(actual['status'], 'CLIENT_PERSONA_IDLE')
        self.assertEqual(actual['source'], receipt()['source'])
        self.assertIs(actual['server_connected'], True)
        self.assertEqual(actual['observed_at_utc'], receipt()['observed_at_utc'])

    def test_busy_stale_disconnected_or_ambiguous_evidence_rejected(self):
        values = [('owner', OWNER[:-1]+'8'), ('schema_version', True), ('schema_version', 2),
                  ('source', 'user_current_session_statement'), ('offline', True),
                  ('persona', 0), ('persona', 7), ('persona', True), ('app', True),
                  ('app', 1142710), ('gameid', 0), ('gameid', '1142710'), ('game', 'game'),
                  ('age_ms', True), ('age_ms', -1), ('age_ms', 5001),
                  ('age_ms', float('nan')), ('age_ms', float('inf')),
                  ('observed_at_utc', (NOW-timedelta(seconds=31)).isoformat()),
                  ('observed_at_utc', (NOW+timedelta(seconds=6)).isoformat()),
                  ('observed_at_utc', '2026-10-31T14:45:00'), ('observed_at_utc', None)]
        for key in ('server_connected', 'server_logged_on', 'initial_connection_complete',
                    'initialized', 'statusInitialized'):
            values.extend([(key, False), (key, 1), (key, None)])
        for key, value in values:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                confirmed_idle_client_persona(OWNER, dict(receipt(), **{key:value}), NOW)
        for value in (None, [], True):
            with self.assertRaises(ValueError):
                confirmed_idle_client_persona(OWNER, value, NOW)

    def test_publisher_checks_client_evidence_before_sdk_and_does_not_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = root/'test.pack'; pack.write_bytes(b'accepted')
            acceptance = root/'acceptance.json'
            acceptance.write_text(json.dumps(dict(mod_id='test',
                release_pack_sha256=hashlib.sha256(b'accepted').hexdigest(),
                L0='PASS', L1='PASS', L2='PASS', L3='PASS')))
            project = ModProject(root, {'id':'test', 'pack_name':'test.pack',
                                       'workshop':{'game_version':'9.0.5.0'}})
            with patch('workshop.account_activity') as public, patch('workshop.Steam') as sdk:
                with self.assertRaises(ValueError):
                    publish(root/'unused.dll', pack, acceptance, root/'state.json', None,
                            OWNER, project=project, client_presence=dict(receipt(), app=1142710))
                public.assert_not_called(); sdk.assert_not_called()
                with patch('account_confirmation.datetime') as date:
                    date.now.return_value = NOW
                    date.fromisoformat.side_effect = __import__('datetime').datetime.fromisoformat
                    sdk.side_effect = RuntimeError('SDK boundary reached')
                    with self.assertRaisesRegex(RuntimeError, 'SDK boundary reached'):
                        publish(root/'unused.dll', pack, acceptance, root/'state.json', None,
                                OWNER, project=project, client_presence=receipt())
                public.assert_not_called(); sdk.assert_called_once()


if __name__ == '__main__':
    unittest.main()
