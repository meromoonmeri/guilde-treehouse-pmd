from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_ambiances_v2';V=R/'renders/sky_peak_canonique_v1';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def load(p):return Image.open(p).convert('RGBA')
src=np.array(m['layout_change']['source_x']);dst=np.array(m['layout_change']['destination_x']);xs=np.rint(np.interp(np.arange(504),dst,src)).astype(int);assert max(abs(xs-np.arange(504)))<=12
for n in ['05_sol_et_rebord_herbeux','06_paroi_et_rochers']:
 original=np.array(load(V/'jour'/(n+'.png')));modified=np.array(load(O/'jour'/(n+'.png')));assert np.array_equal(modified,original[:,xs]);assert np.array_equal(np.array(night(Image.fromarray(modified))),np.array(load(O/'nuit'/(n+'.png'))))
for spec in m['modes']:
 p=O/spec['id'];comp=Image.new('RGBA',(504,504))
 for n in spec['layers']:comp.alpha_composite(load(p/(n+'.png')))
 assert np.array_equal(np.array(comp),np.array(load(p/'composition.png')))
 with Image.open(p/'fleurs_animation.webp') as webp:
  assert webp.n_frames==32
  for f in range(32):
   im=Image.new('RGBA',(504,504))
   for n in spec['layers']:im.alpha_composite(load(p/'fleurs'/f'{f:02}.png') if n=='07_fleurs' else load(p/(n+'.png')))
   webp.seek(f);assert np.array_equal(np.array(im),np.array(webp.convert('RGBA')))
result={'checks':['Transformation horizontale terrain exactement conforme au remapping, déplacement max12px, aucune transformation verticale','Terrain nuit exactement égal au filtre Abyss','5 compositions et 160 frames WebP égales aux PNG de calques exportés'],'runtime_validated':False};(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('\n'.join(result['checks']))
