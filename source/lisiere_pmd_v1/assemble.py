"""Inside the extracted ZIP: python assemble.py --tick 64 --out assembled
Requires Pillow and NumPy. Does not invent PMDO collision/warp entities.
"""
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image

def main():
 p=argparse.ArgumentParser();p.add_argument('--tick',type=int,default=64);p.add_argument('--out',type=Path,default=Path('assembled'));p.add_argument('--pack',type=Path,default=Path(__file__).parent);a=p.parse_args();assert a.tick>=0
 m=json.loads((a.pack/'manifest.json').read_text());a.out.mkdir(parents=True,exist_ok=True)
 def image(path):return Image.open(a.pack/path).convert('RGBA')
 terrain=Image.new('RGBA',tuple(m['size']))
 for path in m['static_layers']:terrain.alpha_composite(image(path))
 terrain.save(a.out/'LE1_terrain_transparent.png')
 b=Image.new('RGBA',terrain.size,(4,44,12,255));b.alpha_composite(terrain);effect=Image.new('RGBA',terrain.size)
 for name in ['rayons','particules']:
  rec=m['animations'][name];effect.alpha_composite(image(rec['frames'][(a.tick//rec['frame_ticks'])%len(rec['frames'])]))
 ba=np.array(b).astype(np.uint16);oa=np.array(effect).astype(np.uint16);ba[:,:,:3]=np.minimum((ba[:,:,:3]>>3)+((oa[:,:,:3]>>3)*(oa[:,:,3:4]>0)),31)*255//31
 Image.fromarray(ba.astype(np.uint8)).save(a.out/f'LE1_composition_tick{a.tick}.png')
 print('Recomposed transparent terrain and illuminated scene in',a.out)
if __name__=='__main__':main()
