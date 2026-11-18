from pathlib import Path
import sys,json
source=Path('D:/workspace/.codex-wh3-runtime/launcher-both-followup-20261031T141338Z/steam_control_force.py').read_text(encoding='utf-8')
exec(compile(source.split("action=sys.argv")[0],'<owned-cef-reader>','exec'))
expression=Path(sys.argv[1]).read_text(encoding='utf-8')
for port in ports:
 for item in probe.http_json(port,'/json/list',3):
  parsed=urlsplit(item.get('url',''))
  if item.get('type')!='page' or item.get('title')!='SharedJSContext':continue
  if parsed.scheme!='https' or parsed.hostname!='steamloopback.host' or parsed.path!='/index.html':continue
  target_id=item['id'];ws=urlsplit(item['webSocketDebuggerUrl'])
  assert re.fullmatch(r'[A-Za-z0-9_-]{1,128}',target_id)
  assert ws.scheme=='ws' and ws.hostname in ('localhost','127.0.0.1') and ws.port in (None,port) and ws.path=='/devtools/page/'+target_id
  url='ws://127.0.0.1:'+str(port)+ws.path
  identity=evaluate(url,"({owner:friendStore.currentUserSteamID.ConvertTo64BitString(),offline:App.BIsOfflineMode()})")
  assert identity['owner']=='76561198273714027'
  print(json.dumps({'identity':identity,'value':evaluate(url,expression)}));sys.exit(0)
raise RuntimeError('No owned Steam shared context')
