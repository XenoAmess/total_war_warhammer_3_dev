from pathlib import Path
import json,hashlib,shutil,subprocess,sys,os,time,psutil,argparse
p=argparse.ArgumentParser();p.add_argument('--mod',action='append',required=True);a=p.parse_args();assert set(a.mod)=={'recruitment_refresh','move_capital'}
r=Path(__file__).parent;repo=Path.cwd();game=Path('C:/SteamLibrary/steamapps/common/Total War WARHAMMER III');state=json.loads((r/'session.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
profile=Path(os.environ['APPDATA'])/'The Creative Assembly/Warhammer3/save_games';saves=sorted(profile.glob('*.save'),key=lambda p:p.stat().st_mtime_ns)
save=saves[-1];assert '3294118498' in save.name;assert time.time()-save.stat().st_mtime>20
before=sha(save);(r/'checkpoint.save').write_bytes(save.read_bytes());assert sha(r/'checkpoint.save')==before
(r/'checkpoint.json').write_text(json.dumps({'source':str(save),'sha256':before,'bytes':save.stat().st_size,'note':'Native autosave, before original-hire fixture; resume may require one ordinary turn.'},ensure_ascii=False,indent=2),encoding='utf-8')
old_expected=json.loads((r/'expected-final.json').read_text()) if (r/'expected-final.json').exists() else None
if old_expected:
 archive=r/('intermediate-'+old_expected['sha256'][:12]);archive.mkdir(exist_ok=False)
 shutil.copytree(r/'evidence',archive/'evidence');shutil.copy2(r/'expected-final.json',archive/'expected.json')
proc=psutil.Process(state['pid']);assert Path(proc.exe()).resolve()==game/'Warhammer3.exe';proc.terminate();proc.wait(20)
assert not any(p.info['name'].lower()=='warhammer3.exe'for p in psutil.process_iter(['name']))
log=r/'native/native.log';log.rename((archive/'native.log') if old_expected else (r/'native-published-0.3.2.log'))
sys.path.insert(0,str(repo/'tools'));from pack import read_pack
pack=repo/'mods/recruitment_refresh/build/xatw3_campaign_utilities.pack';manifest=json.loads(pack.with_name('manifest.json').read_text());assert sha(pack)==manifest['sha256'] and manifest['version']=='0.3.3'
files=read_pack(pack.read_bytes());identity=files['script/xatw3_release_recruitment_refresh.lua'].decode().split("'")[1]
if old_expected:
 tools=(r/'load_final_tools.lua').read_text(encoding='utf-8').replace(old_expected['sha256'],manifest['sha256']).replace(old_expected['release_identity'],identity)
 (r/'load_final_tools.lua').write_text(tools,encoding='utf-8')
item=state['installed'][0];assert sha(Path(item['path']))==item['sha256'];shutil.copy2(pack,item['path']);item['sha256']=manifest['sha256']
bootstrap=(r/'bootstrap.lua').read_text(encoding='utf-8').replace("version=='0.3.2'","version=='0.3.3'")
bootstrap+="\nassert(require('script.xatw3_release_recruitment_refresh')=='"+identity+"')\nxatw3_test.package_sha='"+manifest['sha256']+"'\nxatw3_test.record('FINAL_COLD_PACK "+manifest['sha256']+"')\n"
(r/'native/command.lua').write_text(bootstrap,encoding='utf-8')
(r/'expected-final.json').write_text(json.dumps({**manifest,'release_identity':identity},indent=2),encoding='utf-8')
nav="""local function inspect()
 local root=core:get_ui_root();local b=find_uicomponent(root,'main','left_holder','buttons_holder','buttons_list','campaign','button_campaign')
 if not b or not b:Visible(true)then core:get_tm():real_callback(inspect,1000,'dlc_cold_frontend');return end
 b:SimulateLClick()
 core:get_tm():real_callback(function()
  local function walk(c,path,depth)
   if not c:Visible(true)then return end
   local p=path..'/'..c:Id();xatw3_test.record('FRONTEND '..p..' state='..c:CurrentState())
   if depth<8 then for i=0,c:ChildCount()-1 do walk(UIComponent(c:Find(i)),p,depth+1)end end
  end
  walk(root,'',0)
 end,1500,'dlc_cold_continue_inspect')
end
inspect()
"""
(r/'native/frontend-command.lua').write_text(nav,encoding='utf-8')
receipt=r/('offline-before-cold-'+str(time.time_ns())+'.json');subprocess.run([sys.executable,str(repo/'mods/recruitment_refresh/docs/publication-0.3.1/steam_release_probe.py'),'--receipt',str(receipt)],check=True,capture_output=True);offline=json.loads(receipt.read_text());assert offline['status']=='offline' and offline['offline_mode'] is True
env={**os.environ,'SteamAppId':'1142710','SteamGameId':'1142710'};si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=4
new=subprocess.Popen([str(game/'Warhammer3.exe')],cwd=game,env=env,startupinfo=si)
state.setdefault('previous_pids',[]).append(state['pid']);state.update(pid=new.pid,final_phase='chd',final_candidate_sha256=manifest['sha256'],final_offline_receipt=str(receipt));(r/'session.json').write_text(json.dumps(state,indent=2))
print(json.dumps({'pid':new.pid,'pack_sha256':manifest['sha256'],'checkpoint':str(save),'offline':True}))
