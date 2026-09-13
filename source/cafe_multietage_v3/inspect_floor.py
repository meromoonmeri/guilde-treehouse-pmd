from pathlib import Path
import json,sys,subprocess,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
o=json.loads((P/'guild_second_floor.rsground').read_text(encoding='utf-8-sig'))['Object'];banks={};pin=(P/'halcyon_commit.txt').read_text().strip()
for l in o['Layers']:
 for col in l['Tiles']:
  for t in col:
   for a in t['Layers']:
    name=a['Frames'][0]['Sheet']
    if name in banks:continue
    p=P/(name+'.tile')
    if not p.exists():p.write_bytes(subprocess.check_output(['gh','api',f'repos/Palikadude/Halcyon/contents/Content/Tile/{name}.tile?ref={pin}','-H','Accept: application/vnd.github.raw+json']))
    _,bank,_=tiles(p);banks[name]={xy:straight(im) for xy,im in bank.items()}
cell=o['TexSize']*8;size=(len(o['Layers'][0]['Tiles'])*cell,len(o['Layers'][0]['Tiles'][0])*cell);scene=Image.new('RGBA',size)
for l in o['Layers']:
 if not l['Visible']:continue
 layer=Image.new('RGBA',size)
 for x,col in enumerate(l['Tiles']):
  for y,t in enumerate(col):
   for a in t['Layers']:
    f=a['Frames'][0];v=f['TexLoc'];layer.alpha_composite(banks[f['Sheet']][v['X'],v['Y']],(x*cell,y*cell))
 scene.alpha_composite(layer)
scene.save(P/'guild_second_floor_reference.png')
(P/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.iterdir() if p.suffix in ['.tile','.rsground']},indent=2))
print(size)
