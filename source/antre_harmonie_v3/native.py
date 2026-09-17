from pathlib import Path
import json,sys
from PIL import Image
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent/'references';sys.path.insert(0,str(R/'source/amp_plains_fleurie_v1'));from inspect_references import decode
banks={p.stem:decode(p)[1] for p in O.glob('*.tile')};banks['Metano_Town_Animation_Tileset']=decode(R/'source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile')[1]
obj=json.loads((O/'altere_pond.rsground').read_text(encoding='utf-8-sig'))['Object'];proof=[]
for li,num in [(1,4),(6,3)]:
 for phase in range(num):
  im=Image.new('RGBA',(928,768));layer=obj['Layers'][li]
  for x,col in enumerate(layer['Tiles']):
   for y,tile in enumerate(col):
    for sub in tile['Layers']:
     f=sub['Frames'][phase%len(sub['Frames'])];loc=f['TexLoc']
     if not f['Sheet']:continue
     im.alpha_composite(banks[f['Sheet']][loc['X'],loc['Y']],(x*8,y*8))
     if 62<=x<=73 and 19<=y<=36 and len(sub['Frames'])>1 and phase==0:proof.append({'layer':li,'cell':[x,y],**sub})
  if li==1:
   im.crop((520,168,568,280)).save(O/f'chute_native_{phase}.png');im.crop((432,320,464,352)).save(O/f'eau_native_{phase}.png')
  else:im.crop((496,240,592,296)).save(O/f'ecume_native_{phase}.png')
(O/'timing_proof.json').write_text(json.dumps(proof,indent=2))
