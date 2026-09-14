from pathlib import Path
import re,json,hashlib,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/dungeon_autotiles_v1';ref=json.loads((O/'reference_manifest.json').read_text());m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
banks={}
for name in ['AppleWoods','BeachCave']:
 _,b,_=tiles(P/'assets'/(name+'.tile'));banks[name]={xy:straight(im) for xy,im in b.items()}
def load(p):return Image.open(p).convert('RGBA')
exact=0;blank_animation=[]
for source,entry in ref['sources'].items():
 imgs={fn:load(O/'references_dtef'/source/fn) for fn in entry['files']}
 for rec in entry['records']:
  slot=rec['slot'];typ=['wall','secondary','floor'].index(rec['type']);x=(typ*6+slot%6)*24;y=slot//6*24;tile=imgs[rec['file']].crop((x,y,x+24,y+24));f=rec['source'];native=banks[f['Sheet']][(f['TexLoc']['X'],f['TexLoc']['Y'])];assert np.array_equal(np.array(tile),np.array(native));exact+=1
  if rec['layer'] and tile.getbbox() is None:blank_animation.append((source,rec['file'],slot))
assert not blank_animation,('DTEF importer would skip blank frames',blank_animation[:5])
count=0
for e in m['themes']:
 source=ref['sources'][e['source']];d=O/'dtef'/e['id']
 keys=[]
 for fn in source['files']:
  match=re.match(r'tileset_(\d+)_frame(\d+)_(\d+)\.(\d+)\.png',fn)
  if match:keys.append(tuple(match.groups()[:3]))
 assert len(keys)==len(set(keys)), 'Ambiguous DTEF layer/frame index'
 assert set(p.name for p in d.glob('tileset_*.png'))==set(source['files'])
 for fn in source['files']:
  im=load(d/fn);assert im.size==(432,192);raw=load(O/'references_dtef'/e['source']/fn);assert np.array_equal(np.array(im)[:,:,3],np.array(raw)[:,:,3]);count+=1
 for key,spec in e['animation_layers'].items():
  vi,li=map(int,key.split(':'))
  for fi in range(spec['count']):assert (d/f'tileset_{vi}_frame{li}_{fi}.{spec["duration"]}.png').exists()
# Canonical8-neighbor normalization must produce exactly the engine's47 adjacency cases.
cases=set()
for bits in range(256):
 code=bits&15
 for i in range(4):
  if (bits&(1<<i)) and (bits&(1<<((i+1)%4))) and bits&(1<<(i+4)):code|=1<<(i+4)
 cases.add(code)
assert cases==set(ref['mapping'])-{-1}
hashes={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in P.rglob('*') if p.is_file() and p.name!='hashes.json'};(P/'hashes.json').write_text(json.dumps(hashes,indent=2))
report={'themes':6,'dtef_sheets':count,'native_tile_frame_copies_verified':exact,'adjacency_cases':len(cases),'transparent_animation_frames_skipped_by_importer':0,'alpha_preserved':True,'frame_names_order_durations_preserved':True,'importer_structural_emulation_only':True,'pmdo_runtime_validated':False}
(O/'verification.json').write_text(json.dumps(report,indent=2));print(report)
