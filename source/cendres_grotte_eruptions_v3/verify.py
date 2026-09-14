from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/cendres_grotte_eruptions_v3';P=O/'cendres_grotte';m=json.loads((O/'manifest.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
static={n:load(P/f'grotte_v3_{n}.png') for n in m['static_layers']};terrain=Image.new('RGBA',tuple(m['size']))
for im in static.values():terrain.alpha_composite(im)
a=np.array(terrain);solid=a[:,:,3]>0;walk=np.array(Image.open(O/'masque_approche_grotte.png'))>0
seen=set();lava=[]
for i in range(m['frames']):
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'grotte_v3_{n}_{i:03}.png');c.alpha_composite(im)
  if n.startswith('07_eruption'):assert not np.any(np.array(im)[:,:,3][solid])
 ar=np.array(c);assert np.array_equal(ar,np.array(load(P/f'grotte_v3_scene_{i:03}.png')))
 assert np.all(ar[:,:,3]==255);assert np.array_equal(ar[walk],a[walk]);seen.add(hashlib.sha256(ar.tobytes()).hexdigest())
 lava.append(np.array(load(P/f'grotte_v3_01_magma_genere_{i:03}.png')).astype(float))
assert len(seen)==64
# Reorder each site's cyclic timeline from its own first bubble; flames MUST follow the burst.
for k,v in enumerate(m['vents']):
 states=[m['timeline'][(j-v['offset'])%64][k] for j in range(64)];runs=[states[0]]
 for s in states[1:]:
  if s!=runs[-1]:runs.append(s)
 assert runs==m['event_stages']+['repos'],runs
 assert states.index('jet_naissant')>states.index('eclatement')>states.index('bulle_fissuree')
 for i,row in enumerate(m['timeline']):
  if row[k]=='repos':assert not np.any(np.array(load(P/f'grotte_v3_07_eruption_{k:02}_{i:03}.png'))[:,:,3])
deltas=[float(np.mean(np.abs(lava[(i+1)%64]-lava[i]))) for i in range(64)]
assert deltas[-1]<=max(deltas[:-1])*1.5+1
m['tests'].update({'all_64_saved_frames_exactly_recompose':True,'64_unique_compositions':True,'walking_corridor_unchanged_all_frames':True,'all_six_sites_bubble_then_burst_then_flame_then_rest':True,'idle_sites_fully_transparent':True,'magma_wrap_mean_pixel_delta':deltas[-1],'magma_mean_regular_pixel_delta':float(np.mean(deltas[:-1]))})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m['tests'],indent=2))
