from common import *
import argparse,html,re
from concurrent.futures import ThreadPoolExecutor
parser=argparse.ArgumentParser();parser.add_argument('--mod',required=True,choices=['recruitment_refresh']);parser.parse_args()
accepted=read(PROJECT.root/'docs/acceptance-results-0.3.4.json');download=read(ROOT/'subscription-download.json')
if sha(Path(download['pack']))!=accepted['release_pack_sha256']:raise RuntimeError('Downloaded package changed')
expected=(PROJECT.root/'workshop/description.bbcode').read_text(encoding='utf-8').strip()
for attempt in range(6):
 row=public_details();save('public-after-'+str(attempt)+'.json',row)
 if row['visibility']==0 and row['file_size']==str(PROJECT.pack_path.stat().st_size) and row['title']==PROJECT.metadata['title'] and row['description'].strip()==expected:break
 time.sleep(3)
else:raise RuntimeError('Public metadata/description mismatch')
save('public-after.json',row)
urls=[('main','https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217&l=schinese'),('changelog','https://steamcommunity.com/sharedfiles/filedetails/changelog/3830548217?l=schinese')]
checks=[]
page_errors=[]
for kind,url in urls:
 for attempt in range(3):
  target=url if attempt%2==0 else url+'&verify='+str(time.time_ns())
  request=urllib.request.Request(target,headers={'Cache-Control':'no-cache','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36','Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8'})
  try:
   with urllib.request.urlopen(request,timeout=20) as response:raw=response.read(2500001)
   if len(raw)>2500000:raise RuntimeError('Public page too large')
   file=ROOT/f'public-{kind}-{attempt}.html';file.write_bytes(raw)
   text=html.unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8','replace')))
   normal=' '.join(text.split())
   if '0.3.4' in normal and 'Bhashiva and four Verminlord types now directly tested' in normal:
    checks.append({'kind':kind,'url':target,'path':str(file),'sha256':sha(file),'bytes':len(raw),'status':'PASS'});break
  except (OSError,RuntimeError) as error:
   page_errors.append({'kind':kind,'attempt':attempt,'utc':now(),'error':str(error)[:200]})
   save('public-page-retries.json',page_errors)
   event('public_page_retry',kind=kind,attempt=attempt,error=str(error)[:200])
  time.sleep(20)
 else:raise RuntimeError('New public '+kind+' not visible')
save('public-pages-check.json',checks)
main=Path(checks[0]['path']).read_text(encoding='utf-8').replace('\\/','/')
if '3811098873' not in main:raise RuntimeError('Required dependency missing from public page')
old=read(PROJECT.root/'docs/workshop-publication-0.3.3.json');gallery=[x for x in old['images'] if 'slot' in x]
if len(gallery)!=3 or not all(x['url'] in main for x in gallery):raise RuntimeError('Existing gallery missing or changed')
requests=[{'file':'preview.png','url':row['preview_url'],'sha256':sha(PROJECT.build_dir/'preview.png')},*gallery]
def check_image(record):
 request=urllib.request.Request(record['url'],headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(request,timeout=20) as response:raw=response.read(16777217)
 if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise RuntimeError('Image hash mismatch: '+record['file'])
 return {**record,'status':'PASS','bytes':len(raw)}
with ThreadPoolExecutor(max_workers=4) as pool:images=list(pool.map(check_image,requests))
save('images.json',images)
metadata=read(ROOT/'remote-launcher-metadata.json')
from workshop_metadata import build_launcher_metadata
from workshop_launcher import owned_values
if not all(owned_values(metadata,k)==[v] for k,v in build_launcher_metadata(PROJECT).items()):raise RuntimeError('Launcher metadata mismatch')
result={'status':'PASS','mod_id':'recruitment_refresh','version':'0.3.4','item_id':'3830548217','observed_at_utc':now(),'pack_sha256':accepted['release_pack_sha256'],'public_description':'PASS','public_changelog':'PASS','required_dependency':'PASS','launcher_metadata':'PASS','cover':'PASS','gallery':'PASS_UNCHANGED_3_IMAGES','real_subscribed_download':'PASS'}
save('public-verification.json',result);event('public_verification_passed',**result)
