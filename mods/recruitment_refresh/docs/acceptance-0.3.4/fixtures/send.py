from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,subprocess,sys,time,psutil

p=argparse.ArgumentParser()
p.add_argument('--mod',action='append',required=True)
p.add_argument('--scene',choices=['model','ui','frontend'],default='model')
p.add_argument('file')
a=p.parse_args()
if set(a.mod)!={'recruitment_refresh','move_capital'}:raise RuntimeError('Select both Mods')
r=Path(__file__).parent
state=json.loads((r/'session.json').read_text(encoding='utf-8'))
process=psutil.Process(state['pid'])
if Path(process.exe()).resolve()!=Path(state['game_exe']).resolve():raise RuntimeError('Game process identity changed')
file=(r/a.file).resolve()
if not file.is_relative_to(r.resolve()):raise RuntimeError('Command source is outside this acceptance run')
source=file.read_bytes()
if not source:raise RuntimeError('Empty command source')
names={'model':'command.lua','ui':'ui-command.lua','frontend':'frontend-command.lua'}
target=r/'native'/names[a.scene]
if target.exists():raise RuntimeError('Another command is pending; do not overwrite')
nonce=str(time.time_ns())
code=("xatw3_test.record('HARNESS_BEGIN "+nonce+"')\nlocal function invoke()\n").encode()+source+b"\nend\nlocal ok,result=pcall(invoke)\nxatw3_test.record('HARNESS_END "+nonce.encode()+b" ok='..tostring(ok)..' result='..tostring(result))\nif not ok then error(result)end\n"
log=r/'native/native.log';offset=log.stat().st_size
temporary=target.with_name('publish-'+nonce+'.pending');temporary.write_bytes(code);temporary.rename(target)
end=time.monotonic()+18;output=''
while time.monotonic()<end:
 with log.open('rb')as handle:handle.seek(offset);output=handle.read().decode('utf-8')
 if 'HARNESS_END '+nonce in output:break
 time.sleep(.2)
else:raise RuntimeError('No matching execution acknowledgement; do not replay: '+output[-1200:])
time.sleep(2)
with log.open('rb')as handle:handle.seek(offset);output=handle.read().decode('utf-8')
folder=r/'dispatch-receipts';folder.mkdir(exist_ok=True)
receipt={'machine_id':'pc-20260924rtuf-f11af23c08','observed_at_utc':datetime.now(timezone.utc).isoformat(),
         'nonce':nonce,'scene':a.scene,'file':a.file,'source_sha256':hashlib.sha256(source).hexdigest(),
         'payload_bytes':len(code),'acknowledged':True,'success':'HARNESS_END '+nonce+' ok=true'in output,
         'log_offset':offset,'log_bytes_observed':len(output.encode('utf-8'))}
(folder/(nonce+'.json')).write_bytes((json.dumps(receipt,indent=2)+'\n').encode('utf-8'))
print(output[-5000:])
if not receipt['success']:raise RuntimeError('Campaign command failed; see its acknowledged error')
