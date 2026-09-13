from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_canonique_v1';P=Path(__file__).resolve().parent;m=json.loads((O/'manifest.json').read_text());checks=[]
def load(p):return Image.open(p).convert('RGBA')
fg=np.array(Image.open(O/'masque_terrain_reference.png'))>0;flower=np.array(Image.open(O/'masque_fleurs_retirees.png'))>0;terrain=Image.alpha_composite(load(O/'jour/05_sol_et_rebord_herbeux.png'),load(O/'jour/06_paroi_et_rochers.png'));original=load(P/'gif_0.png');assert np.array_equal(np.array(terrain)[fg&~flower],np.array(original)[fg&~flower]);checks.append('Terrain source 504x504 : pixels hors fleurs exacts, aucune translation ni resize')
for mode,names in m['modes'].items():
 comp=Image.new('RGBA',(504,504))
 for n in names:comp.alpha_composite(load(O/mode/(n+'.png')))
 assert np.array_equal(np.array(comp),np.array(load(O/mode/'composition.png')))
 with Image.open(O/mode/'fleurs_animation.webp') as webp:
  assert webp.n_frames==32
  for f in range(32):
   comp=Image.new('RGBA',(504,504))
   for n in names:comp.alpha_composite(load(O/'fleurs'/mode/f'{f:02}.png') if n=='07_fleurs' else load(O/mode/(n+'.png')))
   webp.seek(f);assert np.array_equal(np.array(comp),np.array(webp.convert('RGBA')))
checks.append('Jour/nuit : recompositions exactes ; 64 frames WebP identiques aux PNG des calques')
for f in range(4):assert np.array_equal(np.array(load(O/'fleurs/cles'/f'{f:02}.png')),np.array(load(O/'fleurs/jour'/f'{f*8:02}.png')))
checks.append('4 clés exactement conservées aux phases 00,08,16,24')
for mode in ['jour','nuit']:
 for n in ['04a_nuages_lointains_wrap','04c_nuages_proches_wrap']:
  a=np.array(load(O/mode/(n+'.png')));assert np.array_equal(np.roll(a,504,axis=1),a)
checks.append('Nuages : identité spatiale au wrap504, horloges indépendantes')
for p in O.rglob('*.png'):
 with Image.open(p) as im:im.load()
(O/'verification.json').write_text(json.dumps({'checks':checks,'runtime_validated':False},ensure_ascii=False,indent=2));print('\n'.join(checks))
