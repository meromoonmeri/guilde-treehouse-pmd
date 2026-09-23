"""Run inside the extracted pack: python assemble.py --tick 64 --out assembled.
Requires Pillow and NumPy. Recreates ten transparent terrains and demonstration PNGs.
The demonstration uses native state PNGs without changing their scale or layout.
"""
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image

def add(base,over):
 b=np.array(base).astype(np.uint16);o=np.array(over).astype(np.uint16)
 b[:,:,:3]=np.minimum((b[:,:,:3]>>3)+((o[:,:,:3]>>3)*(o[:,:,3:4]>0)),31)*255//31
 return Image.fromarray(b.astype(np.uint8))

def main():
 p=argparse.ArgumentParser();p.add_argument('--tick',type=int,default=64);p.add_argument('--out',default='assembled');p.add_argument('--pack',type=Path,default=Path(__file__).parent);a=p.parse_args()
 assert a.tick>=0
 root=a.pack;manifest=json.loads((root/'manifest.json').read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 def image(rel):return Image.open(root/rel).convert('RGBA')
 def frame(group):
  record=manifest['animations'][group]
  index=((a.tick//7)%14)*32+(a.tick//8)%32 if group=='foret' else (a.tick//record['frame_ticks'])%len(record['frames'])
  return image(record['frames'][index])
 for rec in manifest['maps']:
  biome=rec['id'].split('_')[0];size=tuple(rec['size']);terrain=Image.new('RGBA',size)
  for f in rec['layers']:terrain.alpha_composite(image(f))
  terrain.save(out/(rec['id']+'_terrain.png'))
  if biome=='ile':scene=frame('ile')
  elif biome=='volcan':scene=frame('volcan_lave')
  else:scene=Image.new('RGBA',size,{'foret':'#112c17','desert':'#392e16','marin':'#03243f'}[biome])
  scene.alpha_composite(terrain)
  if biome in ['foret','marin']:scene=add(scene,frame(biome))
  elif biome=='volcan':scene.alpha_composite(frame('volcan_cendres'))
  elif biome=='desert':
   im=frame('desert_voile');data=np.array(im);xs=(np.arange(size[0])-a.tick//4)%im.width
   overlay=Image.new('RGBA',size);overlay.paste(Image.fromarray(data[:,xs]),(0,0));scene=add(scene,overlay)
  scene.save(out/(rec['id']+f'_tick{a.tick}.png'))
 print('Wrote ten transparent terrains and ten composed PNGs to',out)
if __name__=='__main__':main()
