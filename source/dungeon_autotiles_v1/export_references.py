from pathlib import Path
import json,re,sys
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/dungeon_autotiles_v1';sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
text=(P/'engine/DtefImportHelper.cs').read_text();mapping=[int(x,16) if x.startswith('0x') else -1 for x in re.search(r'FieldDtefMapping\s*=\s*\{(.*?)\}',text,re.S).group(1).replace('\n','').replace(' ','').split(',') if x]
assert len(mapping)==48 and len(set(mapping)-{-1})==47
banks={}
for n in ['AppleWoods','BeachCave']:
 _,b,_=tiles(P/'assets'/(n+'.tile'));banks[n]={xy:straight(im) for xy,im in b.items()}
manifest={'tile_size':24,'sheet_size':[432,192],'mapping':mapping,'sources':{}}
for name in ['apple_woods','beach_cave']:
 d=O/'references_dtef'/name;d.mkdir(parents=True,exist_ok=True);
 for old in d.glob('tileset_*.png'):old.unlink()
 sheets={};spec={};records=[];global_layers={}
 for typ,t in enumerate(['wall','secondary','floor']):
  o=json.loads((P/'assets'/f'{name}_{t}.json').read_text(encoding='utf-8-sig'))['Object']['Tiles']
  for slot,mask in enumerate(mapping):
   if mask<0:continue
   for vi,layers in enumerate(o[f'Tilex{mask:02X}']):
    for li,l in enumerate(layers):
     for fi,f in enumerate(l['Frames']):
      group=(typ,li,len(l['Frames']),l['FrameLength'])
      if li and group not in global_layers:global_layers[group]=len(global_layers)
      gl=global_layers.get(group,-1)
      key=f'tileset_{vi}.png' if li==0 else f'tileset_{vi}_frame{gl}_{fi}.{l["FrameLength"]}.png'
      if key not in sheets:sheets[key]=Image.new('RGBA',(432,192))
      x=(typ*6+slot%6)*24;y=slot//6*24;tile=banks[f['Sheet']][(f['TexLoc']['X'],f['TexLoc']['Y'])];sheets[key].alpha_composite(tile,(x,y));records.append({'file':key,'slot':slot,'type':t,'variant':vi,'layer':li,'frame':fi,'duration':l['FrameLength'],'source':f})
      if li:spec[f'{vi}:{gl}']={'count':len(l['Frames']),'duration':l['FrameLength']}
 for key,im in sheets.items():im.save(d/key)
 preview=sheets['tileset_0.png'].copy()
 for key,im in sheets.items():
  if re.match(r'tileset_0_frame\d+_0\.',key):preview.alpha_composite(im)
 preview.resize((1296,576),Image.Resampling.NEAREST).save(d/'REFERENCE_COMPOSEE.png')
 manifest['sources'][name]={'animation_layers':spec,'records':records,'files':list(sheets)}
(O/'reference_manifest.json').write_text(json.dumps(manifest,indent=2));print('Exported exact native DTEF references,47 masks,3 variants,all animation layers')
