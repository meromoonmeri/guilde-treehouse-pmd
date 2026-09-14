from pathlib import Path
import json,hashlib
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/cendres_fissures_matiere_v5';P=O/'cendres_fissures_matiere';V4=R/'renders/cendres_palette_raccord_v4';S=V4/'cendres_palette_raccord';m=json.loads((O/'manifest.json').read_text());pal=json.loads((O/'PALETTES_064.json').read_text());colors=set(map(tuple,pal['master_heat_rgb']))
def load(p):return Image.open(p).convert('RGBA')
static={n:load(P/f'grotte_v5_{n}.png') for n in m['static_layers']};terrain=Image.new('RGBA',tuple(m['size']))
for n,im in static.items():
 if n not in ['03a_contact_refroidi','08_gorges_fissures']:terrain.alpha_composite(im)
solid=np.array(terrain)[:,:,3]>0;safe=np.array(Image.open(O/'CORRIDOR_PROTEGE.png'))>0;cracks=np.array(Image.open(O/'MASQUE_FISSURES.png'))>0
assert np.all(solid[cracks]) and not np.any(cracks&safe)
for n in json.loads((V4/'manifest.json').read_text())['static_layers']:assert np.array_equal(np.array(static[n]),np.array(load(S/f'grotte_v4_{n}.png')))
indices=np.array(Image.open(O/'INDICES_FISSURES.png'));seen=set();crackframes=set()
for i in range(64):
 p=P/f'grotte_v5_01_magma_palette_cycling_{i:03}.png';assert p.read_bytes()==(S/f'grotte_v4_01_magma_palette_cycling_{i:03}.png').read_bytes()
 live=Image.alpha_composite(load(p),load(P/f'grotte_v5_02_chauffe_locale_{i:03}.png'));live=np.array(live)
 f=np.array(load(P/f'grotte_v5_09_magma_fissures_{i:03}.png'));assert np.array_equal(f[:,:,3]>0,cracks)
 table=np.array(pal['palette_by_frame'][i],dtype='uint8');assert np.array_equal(f[:,:,:3][cracks],table[indices][cracks]);crackframes.add(hashlib.sha256(f.tobytes()).hexdigest())
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'grotte_v5_{n}_{i:03}.png');c.alpha_composite(im)
  if n.startswith('10_eruption'):
   ar=np.array(im);alpha=ar[:,:,3]>0;assert not np.any(alpha&solid);assert set(map(tuple,ar[:,:,:3][alpha]))<=colors
   k=int(n[-2:]);x,y=m['vents'][k]['anchor'];contact=alpha[y];assert np.array_equal(ar[y,:,:3][contact],live[y,:,:3][contact])
 a=np.array(c);assert np.all(a[:,:,3]==255);assert np.array_equal(a,np.array(load(P/f'grotte_v5_scene_{i:03}.png')))
 # Extra fissure layers and new eruption sprites do not change the protected walking strip.
 old=np.array(load(S/f'grotte_v4_scene_{i:03}.png'));assert np.array_equal(a[safe],old[safe]);seen.add(hashlib.sha256(a.tobytes()).hexdigest())
assert len(seen)==64 and len(crackframes)>16
for k,v in enumerate(m['vents']):
 sequence=[m['timeline'][(j-v['offset'])%64][k] for j in range(64)];runs=[sequence[0]]
 for state in sequence[1:]:
  if state!=runs[-1]:runs.append(state)
 assert runs==m['event_stages']+['repos']
 for i,row in enumerate(m['timeline']):
  if row[k]=='repos':assert not np.any(np.array(load(P/f'grotte_v5_10_eruption_matiere_{k:02}_{i:03}.png'))[:,:,3])
# In the generated sheet the lower-row jet crosses the mathematical half: the chosen gutter prevents contamination.
poses=[load(O/f'pose_generee_{k:02}.png') for k in range(8)];assert poses[0].height<poses[1].height<poses[2].height
for im in poses[:3]:
 mask=np.array(im)[:,:,3]>0;labels,n=nd.label(mask,np.ones((3,3)));counts=np.bincount(labels.ravel());counts[0]=0;largest=counts.argmax();assert np.any(labels[-1]==largest),'Bubble foot belongs to another sprite'
m['tests'].update({'all_64_saved_compositions_recompose':True,'64_unique_compositions':True,'magma_cycling_preserved_byte_for_byte':True,'all_parent_terrain_layers_unchanged':True,'fissure_alpha_fixed_and_only_on_rock':True,'fissure_frames_use_shared_palette_tables':True,'distinct_fissure_frames':len(crackframes),'protected_corridor_unchanged_all_frames':True,'saved_eruption_contact_pixels_match_live_magma':True,'eruption_colors_in_shared_16_color_ramp':True,'all_sites_preserve_causal_sequence':True,'bubble_extraction_has_no_lower_row_jet_fragments':True})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m['tests'],indent=2))
