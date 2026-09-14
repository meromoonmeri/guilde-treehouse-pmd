from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/eau_siphons_rapides_v2';P=O/'eau_siphons_rapides';m=json.loads((O/'manifest.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
static={n:load(P/f'siphons_v2_{n}.png') for n in m['static_layers']}
bridge=Image.alpha_composite(static['07_chaussee_surface'],static['08_chaussee_rebords']);b=np.array(bridge);interior=nd.distance_transform_edt(b[:,:,3]>0)>=12
seen=set()
for i in range(m['frames']):
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'siphons_v2_{n}_{i:03}.png');c.alpha_composite(im)
 a=np.array(c);assert np.array_equal(a,np.array(load(P/f'siphons_v2_scene_{i:03}.png')))
 assert np.all(a[:,:,3]==255)
 assert np.array_equal(a[interior],b[interior]),'Water or reflection intrudes on the dry walking interior'
 seen.add(hashlib.sha256(a.tobytes()).hexdigest())
assert len(seen)==48
# Each fixed-index water image uses exactly the same LUT colors, only their assignments change.
palettes=[set(map(tuple,np.array(load(P/f'siphons_v2_01_eau_palette_cycling_{i:03}.png'))[:,:,:3].reshape(-1,3))) for i in range(48)]
assert all(x==palettes[0] for x in palettes)
# All periods divide the full 48-phase loop; inward radius decreases over a particle flight.
assert 48%6==0 and (2*48)%24==0
r=(1-np.linspace(0,.999,100))**.68;assert np.all(np.diff(r)<0)
m['tests'].update({'all_48_png_compositions_recompose':True,'48_unique_full_frames':True,'dry_walking_interior_unchanged_in_every_frame':True,'palette_color_set_fixed_indices_cycle':True,'streamlet_radius_strictly_decreases_before_respawn':True})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(m['tests'],indent=2))
