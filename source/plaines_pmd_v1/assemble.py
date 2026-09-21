"""Extract ZIP: python assemble.py --tick 0 --out assembled (Pillow only)."""
from pathlib import Path
from PIL import Image
import json,argparse
p=argparse.ArgumentParser();p.add_argument('--pack',type=Path,default=Path(__file__).parent);p.add_argument('--out',type=Path,default=Path('assembled'));p.add_argument('--tick',type=int,default=0);a=p.parse_args();assert a.tick>=0;a.out.mkdir(parents=True,exist_ok=True)
m=json.loads((a.pack/'manifest.json').read_text())
for rec in m['maps']:
 im=Image.new('RGBA',tuple(rec['size']))
 for layer in rec['layers']:
  name=layer['frames'][(a.tick//layer['frame_ticks'])%len(layer['frames'])] if 'frames' in layer else layer['file']
  im.alpha_composite(Image.open(a.pack/name).convert('RGBA'))
 im.save(a.out/f"WP1_{rec['id']}_tick{a.tick}.png")
print('Recomposed both plains at tick',a.tick)
