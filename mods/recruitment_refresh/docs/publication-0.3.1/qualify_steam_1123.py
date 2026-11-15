from pathlib import Path
import pefile,struct,re,json,hashlib,capstone
r=Path(__file__).parent;path=Path('D:/steam/SteamUI.dll');raw=path.read_bytes();pe=pefile.PE(data=raw)
def rva(offset):return pe.get_rva_from_offset(offset)
def rel(offset,disp_at,end_at):return rva(offset)+end_at+struct.unpack_from('<i',raw,offset+disp_at)[0]
def text_at(addr):
 try:
  off=pe.get_offset_from_rva(addr);return raw[off:off+100].split(b'\0')[0].decode(errors='replace')
 except:return ''
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def asm(offset,count):return '\n'.join(f'{i.address:x} {i.mnemonic} {i.op_str}' for i in md.disasm(raw[offset:offset+count],rva(offset)))
out={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'image_size':pe.OPTIONAL_HEADER.SizeOfImage,'producers':[],'getters':[],'tray':[]}
for m in re.finditer(rb'\x44\x0f\xb6\x05....\x48\x8d\x15....\x48\x8b\xcb\xe8....',raw,re.S):
 off=m.start();key=text_at(rel(off,11,15))
 if key=='bIsOfflineMode':out['producers'].append({'rva':rva(off),'value_rva':rel(off,4,8),'bytes':m.group().hex(),'asm':asm(off,24)})
for m in re.finditer(rb'\x40\x53\x48\x83\xec\x20\x48\x8b\xd9\xe8....\x48\x8b\xc8\x48\x8b\x10\xff\x92\x88\0\0\0\x88\x83....\x48\x83\xc4\x20\x5b\xc3',raw,re.S):
 out['getters'].append({'rva':rva(m.start()),'bytes':m.group().hex(),'offset':struct.unpack_from('<I',m.group(),28)[0]})
if out['producers']:
 value=out['producers'][0]['value_rva']
 for m in re.finditer(rb'\x80\x3d....\0\x74.\x48\x8b\x0d....\x45\x33\xc0\xba\x04\0\0\0\xe8....',raw,re.S):
  if rel(m.start(),2,7)==value:out['tray'].append({'rva':rva(m.start()),'bytes':m.group().hex(),'manager_rva':rel(m.start(),12,16),'asm':asm(m.start(),30)})
out['callers']=[]
if len(out['producers'])==1 and len(out['getters'])==1:
 obj=out['producers'][0]['value_rva']-out['getters'][0]['offset']
 for m in re.finditer(rb'\x48\x8d\x0d....\xe8....',raw,re.S):
  if rel(m.start(),3,7)==obj and rel(m.start(),8,12)==out['getters'][0]['rva']:
   out['callers'].append({'rva':rva(m.start()),'bytes':m.group().hex(),'object_rva':obj,'asm':asm(m.start(),12)})
 tray=out['tray'][0];off=pe.get_offset_from_rva(tray['rva']);callee=rel(off,25,29)
 out['tray_callee_rva']=callee;out['tray_asm']=asm(pe.get_offset_from_rva(callee),170)
(r/'steam1123-static.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
