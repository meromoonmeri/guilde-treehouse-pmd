from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'renders/mega_evolution_v1';m=json.loads((out/'manifest.json').read_text());report={}
for name in m['layers']:
 im=Image.open(out/f'MEGA_V1_{name}.png').convert('RGBA');assert im.size==(3072,3072)
 first=np.array(im.crop((0,0,256,256)));last=np.array(im.crop((2816,2816,3072,3072)))
 assert not first[:,:,3].any() and not last[:,:,3].any()
 report[name]={'size':im.size,'transparent_start_end':True}
for d in range(8):
 im=Image.open(out/f'preview_{d}.webp');assert 1<im.n_frames<=144;assert im.size==(256,256)
 duration=0
 for f in range(im.n_frames):
  im.seek(f);im.load();duration+=im.info['duration']
 assert duration==4800
 report[f'preview_{d}']={'encoded_frames':im.n_frames,'duration_ms':duration}
report['previews']='8 sequences, 144 rendered phases / 4800ms; WebP may merge identical holds';report['coverage']=m['coverage_test'];report['runtime']='NOT TESTED';report['artistic_approval']='NOT OBTAINED'
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
