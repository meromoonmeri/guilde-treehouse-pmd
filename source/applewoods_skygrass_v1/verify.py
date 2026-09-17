from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/applewoods_skygrass_v1';P=O/'entree_pommier';m=json.loads((O/'manifest.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
static={n:load(P/f'apple_sky_{n}.png') for n in m['static_layers']};seen=set();path=np.array(Image.open(O/'MASQUE_CHEMIN.png'))>0
for phase in range(4):
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'apple_sky_{n}_{phase:03}.png');c.alpha_composite(im)
  if n in m['animation_groups']:assert not np.any((np.array(im)[:,:,3]>0)&path)
 assert np.array_equal(np.array(c),np.array(load(P/f'apple_sky_scene_{phase:03}.png')));assert np.all(np.array(c)[:,:,3]==255);seen.add(hashlib.sha256(c.tobytes()).hexdigest())
assert len(seen)==4
for k,source in enumerate(m['flower_sources']):
 for phase in range(4):
  im=np.array(load(O/f'sprites/fleur_sky_{k:02}_phase_{phase:02}.png'));ref=np.array(load(R/f'source/sky_peak_v1/gif_{phase}.png').crop(tuple(source['bbox'])));visible=im[:,:,3]>0;assert np.array_equal(im[visible],ref[visible])
for phase in range(4):
 out={n:Image.new('RGBA',tuple(m['size'])) for n in m['animation_groups']}
 for site in m['flower_sites']:
  x,y=site['center'];g=2 if y<195 else (0 if x<276 else 1);im=load(O/f'sprites/fleur_sky_{site["sprite"]:02}_phase_{(phase+site["phase_offset"])%4:02}.png');out[m['animation_groups'][g]].alpha_composite(im,tuple(site['origin']))
 for n,im in out.items():assert np.array_equal(np.array(im),np.array(load(P/f'apple_sky_{n}_{phase:03}.png')))
assert len(m['trees'])==20 and all(t['name'] in static for t in m['trees'])
m['tests'].update({'all_four_saved_frames_recompose':True,'four_unique_compositions':True,'native_flower_pixels_preserved_without_resizing':True,'flower_layers_exact_source_phase_assembly':True,'flowers_off_path':True,'twenty_individual_tree_layers':True})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m['tests'],indent=2))
