"""Freeze verified public-source assets and the eleven-reference audit (no ROM)."""
from native_archive import native_source_archive

from pathlib import Path
import json,re,hashlib,zipfile,math
from red import decode
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;C=R/'.cache/redport_audit';P=C/'port'
REFS={'energeticforest':'H07P04','finalisland':'H29P04','volcanicpit':'H26P01','witheringdesert':'H20P01','deepseacurrent':'H02P02','jungle':'H14P01','overgrownforest':'H07P03','mtdiscipline':'H16P01','wildplains':'H06P01','secretiveforest':'H07P08','scorchedplains':'H06P05'}
def main():
 trees={n:{r['path']:r for r in json.loads((C/(n+'_tree.json')).read_text())['tree']} for n in ['port','pret']}
 enums=re.findall(r'^\s*(MAP_FILE_ID_\w+),', (P/'include/map_files_table.h').read_text(),re.M)
 table={key:re.search(r'\.bplFileName = "([^"]+)"',body)[1] for key,body in re.findall(r'\[(MAP_FILE_ID_\w+)\] = \{(.*?)\n    \}',(P/'src/map_files_table.c').read_text(),re.S)}
 weatherbody=(P/'data/data_8115F5C_3_.s').read_text().split('gUnknown_811E5F4:')[1].split('.global')[0]
 bytevalues=[int(v,16) for line in weatherbody.splitlines() if line.startswith('.byte') for v in re.findall(r'0x([0-9a-f]+)',line)]
 import struct
 weather=[struct.unpack_from('<hh',bytes(bytevalues),i*4) for i in range(16)]
 conv={}
 for body in re.findall(r'\[MAP_\w+\] = \{(.*?)\n    \}',(P/'src/ground_map_conversion_table.c').read_text(),re.S):
  m=re.search(r'\.mapFileTableId = (MAP_FILE_ID_\w+)',body);w=re.search(r'\.unk6 = (-?\d+)',body)
  if m and w:conv[m[1]]=int(w[1])
 records=[];needed=set();metas={}
 for reference,name in REFS.items():
  enum=next(k for k,v in table.items() if v==name);wid=conv[enum];wn=table[enums[weather[wid][1]]] if wid>=0 else None
  rec={'reference':reference,'map':name,'enum':enum,'weather_id':wid,'weather_map':wn,'batch':1 if reference in list(REFS)[:5] else 2,'new_maps':'entry + finale; generated, not native'}
  for n in [name,wn]:
   if not n:continue
   _,meta,_,_=decode(n);metas[n]=meta
   needed.update(p for p in (P/'data/map_bg').iterdir() if p.name in [n+'.bpl',n+'c.bpc',n+'m.bma'] or re.fullmatch(re.escape(n)+r'[1-4]\.bpa',p.name))
  records.append(rec)
 proof=['src/ground_bg.c','src/ground_weather.c','src/ground_map.c','src/ground_map_conversion_table.c','src/map_files_table.c','include/map_files_table.h','include/structs/str_ground_bg.h','data/data_8115F5C_3_.s','platform/pc/video_pc.c']
 needed.update(P/x for x in proof)
 files=[]
 rebuilt=C/'native_sources_rebuilt.zip'
 with zipfile.ZipFile(rebuilt,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(needed):
   rel=p.relative_to(P).as_posix();b=p.read_bytes();sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert sha==trees['port'][rel]['sha']
   pr=trees['pret'].get(rel,{}).get('sha');files.append(dict(path=rel,bytes=len(b),git_sha1=sha,sha256=hashlib.sha256(b).hexdigest(),pret_git_sha1=pr,identical_to_pret=pr==sha))
   zi=zipfile.ZipInfo(rel,(2026,9,21,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,b)
 assert rebuilt.read_bytes()==native_source_archive().read_bytes(), 'Pinned native bundle changed'
 hpaths=[p for p in trees['port'] if p.startswith('data/map_bg/H')]
 result={'port_repo':'https://github.com/Lyraedan/PMD-Red-PC-Port','port_commit':(C/'port_commit.txt').read_text().strip(),'pret_repo':'https://github.com/pret/pmd-red','pret_commit':(C/'pret_commit.txt').read_text().strip(),'references':records,'metadata':metas,'files':files,'H_bank_comparison':{'count':len(hpaths),'identical':sum(trees['port'][p]['sha']==trees['pret'].get(p,{}).get('sha') for p in hpaths)},'timing':{'BPA':'stored duration + 1 update ticks (postdecrement)','BPL':'duration update ticks (predecrement)','preview_hz':60,'phase':'steady-state phase convention, not an emulator startup capture'},'validation':'Source-level extraction. No PC-port/GBA/PMDO runtime comparison. BPL RGB retained in native PNGs, not a GPU screenshot. Palette bits on fully transparent tiles ignored; out-of-bank visible pixels are fatal.'}
 (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(result['H_bank_comparison']);print([(r['map'],r['weather_map']) for r in records]);print('native source archive', rebuilt.stat().st_size)
def bootstrap():
 import subprocess
 prior=json.loads((HERE/'audit.json').read_text());C.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(native_source_archive()) as z:z.extractall(P)
 for label,repo in [('port','Lyraedan/PMD-Red-PC-Port'),('pret','pret/pmd-red')]:
  pin=prior[label+'_commit'];(C/(label+'_commit.txt')).write_text(pin+'\n')
  raw=subprocess.check_output(['gh','api',f'repos/{repo}/git/trees/{pin}?recursive=1']);tree=json.loads(raw)
  assert not tree.get('truncated'), 'Incomplete Git tree'
  (C/(label+'_tree.json')).write_bytes(raw)
if __name__=='__main__':
 import sys
 if '--bootstrap' in sys.argv:bootstrap()
 main()
