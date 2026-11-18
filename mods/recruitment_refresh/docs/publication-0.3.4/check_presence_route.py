from pathlib import Path
from datetime import datetime,timezone
from io import BytesIO
import argparse,json,sys,unittest
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
repo=Path.cwd();sys.path[:0]=[str(repo/'tools'),str(repo/'tests')]
from workshop import _html_account_activity
from test_tools import PublicationGateTests
suite=unittest.defaultTestLoader.loadTestsFromTestCase(PublicationGateTests)
result=unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful()
page=BytesIO(b'g_rgProfileData = {"steamid":"76561198273714027"};<div class="profile_in_game persona in-game"></div><div class="recent_games"></div>')
page.headers={'Age':'0'}
with patch('workshop.urllib.request.urlopen',return_value=page)as request:
 assert _html_account_activity('76561198273714027',datetime.now(timezone.utc).isoformat(),language='schinese')['status']=='BUSY'
 assert 'l=schinese&presence_check='in request.call_args.args[0].full_url
with patch('workshop.urllib.request.urlopen')as request:
 try:_html_account_activity('76561198273714027',datetime.now(timezone.utc).isoformat(),language='unsupported')
 except ValueError:pass
 else:raise AssertionError('Invalid route accepted')
 request.assert_not_called()
receipt={'status':'PASS','mod_id':'recruitment_refresh','existing_publication_gate_tests':result.testsRun,'additional_route_checks':['schinese route keeps busy detection','unsupported route rejected before HTTP'],'live_idle_evidence':'account-initial.json','source':'existing strict canonical full-profile parser; language route only, no public-presence safety checks removed','observed_at_utc':datetime.now(timezone.utc).isoformat()}
(Path(__file__).parent/'presence-route-verification.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode('utf-8'))
print(json.dumps(receipt))
