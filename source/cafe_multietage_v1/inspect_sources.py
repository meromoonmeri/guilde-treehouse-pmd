from pathlib import Path
import json,sys,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
banks={}
for p in P.glob('*.tile'):
 size,bank,_=tiles(p);banks[p.stem]={xy:straight(im) for xy,im in bank.items()};w=max(x for x,y in bank)+1;h=max(y for x,y in bank)+1;sheet=Image.new('RGBA',(w*size,h*size))
 for (x,y),im in banks[p.stem].items():sheet.alpha_composite(im,(x*size,y*size))
 sheet.save(P/(p.stem+'.png'))
for p in P.glob('*.rsground'):
 o=json.loads(p.read_text(encoding='utf-8-sig'))['Object'];cell=o['TexSize']*8;size=(len(o['Layers'][0]['Tiles'])*cell,len(o['Layers'][0]['Tiles'][0])*cell);scene=Image.new('RGBA',size)
 for i,l in enumerate(o['Layers']):
  layer=Image.new('RGBA',size)
  for x,col in enumerate(l['Tiles']):
   for y,t in enumerate(col):
    for a in t['Layers']:
     f=a['Frames'][0];pos=f['TexLoc'];layer.alpha_composite(banks[f['Sheet']][pos['X'],pos['Y']],(x*cell,y*cell))
  layer.save(P/f'{p.stem}_layer_{i}.png')
  if l['Visible']:scene.alpha_composite(layer)
 scene.save(P/(p.stem+'_reference.png'))
(P/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.iterdir() if p.suffix in ['.tile','.rsground']},indent=2))
