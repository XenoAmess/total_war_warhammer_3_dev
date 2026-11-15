"""Task-local exact new-client native profile, using the canonical read-only provider.

No canonical source edits; independent release receipt schema because the old
public wire parser admits only tray offset 0x154. This image uses audited 0x160.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys,secrets
sys.path.insert(0,str(Path.cwd().parent/'ck3_eternal_recurrence/tools'))
import steam_offline_native_profiles as profiles
import steam_offline_native_provider_v1 as native
import steam_offline_state_probe as probe

PROFILE=profiles.NativeOfflineProfile(
 'steamui-11.23.65.88-2dfb0a5d','11.23.65.88',
 '2dfb0a5d50dd90667549cc7d413c7bfb0794c9af4ebaf08bf1cf7d938a11ea93',
 19675800,19959808,18653399,18645800,0x160,6691596,
 bytes.fromhex('440fb605c385b600488d15c5297800488bcbe8dd0a3e00'),
 ((6691596,bytes.fromhex('440fb605c385b600488d15c5297800488bcbe8dd0a3e00')),
  (6395968,bytes.fromhex('40534883ec20488bd9e862ebf1ff488bc8488b10ff92880000008883870100004883c4205bc3')),
  (7179695,bytes.fromhex('488d0d9a11af00e8850af4ff')),
  (6685828,bytes.fromhex('803d4c9cb600007419488b0d947eb6004533c0ba04000000e83f0bf6ff')),
  (6033406,bytes.fromhex('8bfa4c8bf13b9160010000')),
  (6033454,bytes.fromhex('4189be60010000'))))
profiles.PROFILES=(*profiles.PROFILES,PROFILE);native.PROFILES=profiles.PROFILES

def observe():
 reader=probe.WindowsReader();rows=reader.processes()
 roots=[pid for pid,(_,name) in rows.items() if name.lower()=='steam.exe']
 receipt={'schema':'wh3.release-steam-offline/v1','machine_id':probe.current_machine_id(),
  'observed_at_utc':datetime.now(timezone.utc).isoformat(),'nonce':secrets.token_hex(16),'status':'unavailable'}
 if len(roots)!=1:return {**receipt,'reason':'ambiguous_or_missing_steam'}
 identity=reader.identity(roots[0]);result=native.probe_native_offline_mode(receipt['machine_id'],receipt['nonce'],steam=identity,reader=reader)
 receipt['steam']=identity.to_wire()
 if result.status!='observed':return {**receipt,'reason':result.reason,'detail':result.detail}
 e=result.evidence
 assert e.tray_state_offset==str(profiles.select_profile(identity.file_version,result.source.bytes,result.source.sha256).tray_offset)
 assert e.raw_samples==(1,1) and e.tray_state_samples==(4,4)
 return {**receipt,'status':'offline','offline_mode':True,'observation_method':'native_current_user_byte','source':result.source.to_wire(),'native_evidence':e.to_wire()}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--timeout');args=p.parse_args()
 result=observe();args.receipt.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
