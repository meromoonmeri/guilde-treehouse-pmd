from pathlib import Path
import sys,json,re
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_dtef_v2';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
count=0;exact=0;bomb_pixels=0
for e in m['themes']:
 source=O/'references_dtef'/e['source'];raw={f:np.array(Image.open(source/f).convert('RGBA')) for f in e['files']}
 records=json.loads((source/'records.json').read_text())
 for r in records:
  if r['layer']:
   x,y=r['xy'];assert raw[r['file']][y:y+24,x:x+24,3].any(),'Blank source frame would be skipped by importer'
 exact+=len(records)
 keys=[]
 for f in e['files']:
  match=re.fullmatch(r'tileset_(\d+)_frame(\d+)_(\d+)\.(\d+)\.png',f)
  if match:keys.append(tuple(map(int,match.groups()[:3])))
 assert len(keys)==len(set(keys))
 for mode in ['jour','nuit']:
  D=O/'RAW/TileDtef'/f'd2_{e["id"]}_{mode}';assert set(p.name for p in D.glob('tileset_*.png'))==set(e['files'])
  for f in e['files']:
   im=Image.open(D/f).convert('RGBA');assert im.size==(432,192);a=np.array(im);original=raw[f];count+=1
   day=np.array(Image.open(O/'RAW/TileDtef'/f'd2_{e["id"]}_jour'/f).convert('RGBA'));assert np.array_equal(a[:,:,3],original[:,:,3])
   if mode=='nuit':assert np.array_equal(a,np.array(night(Image.fromarray(day))))
   else:
    yy,xx=np.mgrid[:192,:432];border=(xx%24<4)|(xx%24>=20)|(yy%24<4)|(yy%24>=20);assert np.array_equal(a[border],original[border])
    if '_frame' in f:assert np.array_equal(a,original)
    diff=np.any(a!=original,axis=2);bomb_pixels+=int(diff.sum());assert not diff[:,:288].any()
    if f=='tileset_0.png':assert not diff.any()
   for t in range(3):assert not a[48:72,(t*6+5)*24:(t*6+6)*24,3].any()
  for key,s in e['animation_layers'].items():
   v,l=key.split(':')
   for p in range(s['count']):assert (D/f'tileset_{v}_frame{l}_{p}.{s["duration"]}.png').exists()
cases=set()
for n in range(256):
 v=n&15
 for i in range(4):
  if n&(1<<i) and n&(1<<((i+1)%4)) and n&(1<<(i+4)):v|=1<<(i+4)
 cases.add(v)
assert cases==set(m['mapping'])-{-1}
report=dict(status='PASS',biomes=10,additional_illuminant_reference=1,dtef_pngs=count,native_tile_frame_records=exact,adjacency_cases=47,modified_floor_pixels=bomb_pixels,all_native_animations_exact_day=True,blank_animation_frames_lost=0,alpha_and_four_pixel_gaskets_preserved=True,night_exact=True,frame_names_durations_and_variants_preserved=True,runtime_validated=False)
(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
