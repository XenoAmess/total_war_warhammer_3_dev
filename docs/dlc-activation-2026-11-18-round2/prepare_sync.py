from pathlib import Path

root=Path(__file__).parent
previous=root.parent/'dlc-activation-20261118'
publication=Path.cwd()/'mods/recruitment_refresh/docs/publication-0.3.3'
(root/'common.py').write_bytes((publication/'common.py').read_bytes())
for name in ['dlc_client.py','cef_read.py','download_state.js','store-dlc-catalog.json']:
    (root/name).write_bytes((previous/name).read_bytes())
text=(previous/'controller.py').read_text(encoding='utf-8')
text=text.replace('import os,re','''import os,re,argparse
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args()
if set(a.mod)!={'recruitment_refresh','move_capital'}:raise RuntimeError('Explicitly select both Mods')''')
text=text.replace("inspect_ready(75);control('offline')\n if not wait_native_offline(20):raise RuntimeError('Controlled client not offline')",
                  "inspect_ready(75)\n if not wait_native_offline(25):raise RuntimeError('Controlled client offline readiness timed out')\n require_offline('controlled-startup-offline.json')")
text=text.replace(" inventory('dlc-online-after.json');save('manifest-after.json',manifest());event('online_operations_finished')",
                  " save('manifest-after.json',manifest());event('online_operations_finished')")
(root/'sync_controller.py').write_bytes(text.encode('utf-8'))
for path in root.glob('*.py'):compile(path.read_text(encoding='utf-8'),str(path),'exec')
print('Prepared one online inventory/install pass, download monitoring and mandatory offline restoration')
