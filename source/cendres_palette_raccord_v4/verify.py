from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/cendres_palette_raccord_v4';P=O/'cendres_palette_raccord';V3=R/'renders/cendres_grotte_eruptions_v3';m=json.loads((O/'manifest.json').read_text());pm=json.loads((O/'PALETTES_064.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
static={n:load(P/f'grotte_v4_{n}.png') for n in m['static_layers']};terrain=Image.new('RGBA',tuple(m['size']))
for n,im in static.items():
 if n!='03a_contact_refroidi':terrain.alpha_composite(im)
a=np.array(terrain);solid=a[:,:,3]>0;walk=np.array(Image.open(O/'masque_approche_grotte.png'))>0
seen=set();magma=[];indices=np.array(Image.open(O/'MAGMA_INDICES_FIXES.png'));classes=np.array(Image.open(O/'MAGMA_CLASSES_THERMIQUES.png'));cold=classes<=3
master=set(map(tuple,pm['master_heat_rgb']));allpal=[]
for i in range(m['frames']):
 indexed=Image.open(P/f'grotte_v4_01_magma_palette_cycling_{i:03}.png');assert indexed.mode=='P'
 assert np.array_equal(np.array(indexed),indices),'Magma geometry moved'
 assert np.array_equal(np.array(indexed.getpalette()).reshape(256,3),np.array(pm['palette_by_frame'][i]))
 allpal.append(indexed.getpalette());ma=np.array(indexed.convert('RGBA'));magma.append(ma)
 assert np.array_equal(ma[cold],magma[0][cold]),'Cold crust cycles'
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'grotte_v4_{n}_{i:03}.png');c.alpha_composite(im)
  ar=np.array(im)
  if n.startswith('07_eruption'):
   assert not np.any(ar[:,:,3][solid]);colors=set(map(tuple,ar[:,:,:3][ar[:,:,3]>0]));assert colors<=master
  if n in ['01_magma_palette_cycling','02_chauffe_locale']:
   assert set(map(tuple,ar[:,:,:3][ar[:,:,3]>0]))<=master
 ar=np.array(c);assert np.array_equal(ar,np.array(load(P/f'grotte_v4_scene_{i:03}.png')))
 assert np.all(ar[:,:,3]==255);assert np.array_equal(ar[walk],a[walk]);seen.add(hashlib.sha256(ar.tobytes()).hexdigest())
assert len({tuple(p) for p in allpal})>32
old=Image.new('RGBA',tuple(m['size']))
for n in json.loads((V3/'manifest.json').read_text())['static_layers']:old.alpha_composite(load(V3/'cendres_grotte'/f'grotte_v3_{n}.png'))
b=np.array(old);oldsolid=b[:,:,3]>0;add=np.array(Image.open(O/'masque_reparation_locale.png'))>0
assert np.array_equal(a[oldsolid],b[oldsolid]);assert np.array_equal(a[~add],b[~add]);assert solid[235,135] and not oldsolid[235,135]
for k,v in enumerate(m['vents']):
 states=[m['timeline'][(j-v['offset'])%64][k] for j in range(64)];runs=[states[0]]
 for state in states[1:]:
  if state!=runs[-1]:runs.append(state)
 assert runs==m['event_stages']+['repos']
 for i,row in enumerate(m['timeline']):
  if row[k]=='repos':assert not np.any(np.array(load(P/f'grotte_v4_07_eruption_{k:02}_{i:03}.png'))[:,:,3])
deltas=[float(np.mean(np.abs(magma[(i+1)%64].astype(float)-magma[i]))) for i in range(64)]
assert deltas[-1]<=max(deltas[:-1])*1.5+1
m['tests'].update({'all_64_saved_frames_exactly_recompose':True,'unique_full_compositions':len(seen),'all_magma_index_planes_identical':True,'palette_tables_match_indexed_pngs':True,'cold_classes_rgb_fixed_all_frames':True,'magma_and_eruptions_share_master_ramp':True,'all_old_rock_pixels_unchanged':True,'terrain_changed_only_in_local_addition_mask':True,'walking_corridor_unchanged_all_frames':True,'all_sites_bubble_then_burst_then_flame_then_rest':True,'magma_wrap_mean_pixel_delta':deltas[-1],'magma_mean_regular_pixel_delta':float(np.mean(deltas[:-1]))})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m['tests'],indent=2))
