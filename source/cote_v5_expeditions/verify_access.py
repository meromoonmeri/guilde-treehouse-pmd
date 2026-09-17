"""Check 16x16 clearance from arrival to all three entrance thresholds."""
from pathlib import Path
from collections import deque
import json,zipfile,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];WEB=ROOT/'sprites/cote_v5_expeditions';PACK=Path.home()/'.cache/cote_v5_expeditions_pack'

def verify_access():
 m=json.loads((WEB/'manifest.json').read_text());results=[]
 for z in m['zones']:
  g=np.array(Image.open(WEB/z['id']/'MASQUE_HERBE.png'))>0
  g &= np.array(Image.open(WEB/z['id']/'05_ACCES_NATIF.png'))[:,:,3]==0
  free=np.array([[g[y:y+16,x:x+16].all() for x in range(0,g.shape[1]-15,8)] for y in range(0,g.shape[0]-15,8)])
  sx,sy=(v//8 for v in z['entry']);assert free[sy,sx],z['id']
  for mode,v in z['variants'].items():
   o=json.loads((PACK/f'Data/Ground/{v["asset"]}.rsground').read_text())['Object']
   assert len(o['Entities'][0]['Markers'])==(2 if z['door'] else 1)
  if not z['door']:continue
  tx,ty=(v//8 for v in z['door']['threshold']);assert free[ty,tx]
  queue=deque([(sx,sy)]);seen={(sx,sy)}
  while queue:
   x,y=queue.popleft()
   for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if 0<=ny<free.shape[0] and 0<=nx<free.shape[1] and free[ny,nx] and (nx,ny) not in seen:
     seen.add((nx,ny));queue.append((nx,ny))
  assert (tx,ty) in seen,z['id']
  results.append({'id':z['id'],'arrival':z['entry'],'threshold':z['door']['threshold'],'clearance_px':[16,16],'reachable':True,'dungeon_destination':None})
 assert len(results)==3
 # Every old Ground and resource in the new project is unchanged, not rebuilt.
 count=0
 with zipfile.ZipFile(ROOT/'cotes_metano_abyss_0812_pmdo.zip') as a:
  for name in a.namelist():
   rel=name.split('/',1)[-1]
   if rel.startswith(('Data/Ground/','Content/')) and not rel.endswith('index.idx'):
    assert (PACK/rel).read_bytes()==a.read(name),rel
    count+=1
 report={'entrances':results,'previous_files_byte_identical':count,'graphical_runtime_tested':False}
 for path in [WEB/'access_verification.json',PACK/'access_verification.json',ROOT/'source/cote_v5_expeditions/access_verification.json']:
  path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('PASS: 3 reachable 16px thresholds; previous Ground/resources unchanged.')
 return report

if __name__=='__main__':verify_access()
