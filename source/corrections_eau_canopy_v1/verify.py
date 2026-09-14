from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/corrections_eau_canopy_v1'
def load(p):return Image.open(p).convert('RGBA')
m=json.loads((O/'manifest.json').read_text());checks={}
for s in m['scenes']:
 p=O/s['id'];w,h=s['size']
 if s['animation_groups']:
  groups=s['animation_groups'];layers=[load(p/l['file']) for l in s['layers']]
  for i in range(24):
   c=Image.new('RGBA',(w,h))
   for g in groups:c.alpha_composite(load(p/g['files'][(i*60//g['duration_ms'])%len(g['files'])]))
   for im in layers:c.alpha_composite(im)
   a=np.array(c);assert np.array_equal(a,np.array(load(p/f'{s["id"]}_scene_{i:03}.png')))
   assert np.all(a[:,:,3]==255) and np.all(a[:,:,0]<=a[:,:,1]) and np.all(a[:,:,0]<=a[:,:,2])
  waters=[np.array(load(p/f)).astype(int) for f in groups[0]['files']]
  assert all(np.max(np.abs(a-b))<=2 for a,b in zip(waters,waters[1:]+waters[:1]))
  for i,f in enumerate(groups[1]['files']):
   old=R/f'renders/layouts_magenta_v1/variantes/sables_siphons_eau/sables_siphons_eau_01_siphons_eau_adaptes_{i:03}.png'
   assert np.array_equal(np.array(load(p/f)),np.array(load(old)))
  checks['water']={'all_24_frames_recomposed':True,'no_warm_sand_pixels':True,'all_six_siphons_unchanged':True,'water_modulation_max_step_including_wrap':2}
 else:
  masks=[np.array(load(p/l['file']))[:,:,3]>0 for l in s['layers'][-2:]];mask=masks[0]|masks[1];parent='foret_mousse_doree' if 'mousse' in s['id'] else 'foret_emeraude'
  a=np.array(load(p/'COMPOSITION.png'));b=np.array(load(R/f'renders/layouts_magenta_v1/zones/{parent}/COMPOSITION.png'))
  assert np.array_equal(a[~mask],b[~mask]);assert not mask[:,202:302].any()
  checks[s['id']]={'unchanged_outside_canopy':True,'foreground_coverage_percent':round(mask.mean()*100,2),'central_access_clear':True}
(O/'verification.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
