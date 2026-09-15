from pathlib import Path
import json,subprocess,base64,sys,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent/'references';sys.path.insert(0,str(R/'source/amp_plains_fleurie_v1'));from inspect_references import decode
j=json.loads((O/'tree_selection.json').read_text());chosen=[x for x in j['tree'] if x['path'].endswith('.tile') and 'Altere_Pond_' in x['path'] or x['path']=='Data/Ground/altere_pond.rsground'];prov=[];banks={}
for x in chosen:
 p=O/Path(x['path']).name
 if not p.exists():
  b=json.loads(subprocess.check_output(['gh','api','repos/Palikadude/Halcyon/git/blobs/'+x['sha']]));p.write_bytes(base64.b64decode(b['content']))
 prov.append({'path':x['path'],'blob':x['sha'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 if p.suffix=='.tile':
  size,bank=decode(p);banks[p.stem]=bank;im=Image.new('RGBA',((max(x for x,y in bank)+1)*8,(max(y for x,y in bank)+1)*8))
  for (x,y),t in bank.items():im.alpha_composite(t,(x*8,y*8))
  im.save(p.with_suffix('.png'))
banks['Metano_Town_Animation_Tileset']=decode(R/'source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile')[1]
obj=json.loads((O/'altere_pond.rsground').read_text(encoding='utf-8-sig'))['Object'];scene=None;anims=[]
for li,layer in enumerate(obj['Layers']):
 im=Image.new('RGBA',(len(layer['Tiles'])*8,len(layer['Tiles'][0])*8))
 for x,col in enumerate(layer['Tiles']):
  for y,tile in enumerate(col):
   for sub in tile['Layers']:
    f=sub['Frames'][0];loc=f['TexLoc']
    if not f['Sheet']:continue
    im.alpha_composite(banks[f['Sheet']][loc['X'],loc['Y']],(x*8,y*8))
    if len(sub['Frames'])>1:anims.append(sub)
 im.save(O/f'altere_layer_{li}.png')
 if scene is None:scene=Image.new('RGBA',im.size)
 if layer['Visible']:scene.alpha_composite(im)
scene.save(O/'altere_composition.png');(O/'provenance.json').write_text(json.dumps({'commit':j['sha'],'files':prov},indent=2));(O/'animations.json').write_text(json.dumps(anims));print(scene.size,[(l['Name'],l['Visible']) for l in obj['Layers']])
