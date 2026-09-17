from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/spring_arc_en_ciel_v1';m=json.loads((O/'manifest.json').read_text());checks=[]
def load(p):return Image.open(p).convert('RGBA')
for p in O.rglob('*.png'):
 with Image.open(p) as im:im.load()
checks.append(f'{len(list(O.rglob("*.png")))} PNG décodés')
for layout in m['layouts']:
 path=O/layout['id'];im=load(path/layout['layers'][0])
 for name in layout['layers'][1:]:im.alpha_composite(load(path/name))
 assert np.array_equal(np.array(im),np.array(load(path/'composition.png')))
 with Image.open(path/'animation.webp') as webp:
  assert webp.n_frames==39
  for f in range(39):
   comp=load(path/layout['layers'][0])
   for name in ['eau_cascades','halo_bassin','faisceau']:comp.alpha_composite(load(O/'commun'/name/f'{f:02}.png'),tuple(layout['offset']))
   webp.seek(f);assert np.array_equal(np.array(comp),np.array(webp.convert('RGBA'))),(layout['id'],f)
checks.append('4 piles de calques exactes ; 156 images WebP identiques aux recompositions des PNG communs + offsets')
metrics={}
for name in ['faisceau','halo_bassin']:
 a=[np.array(load(O/'commun'/name/f'{f:02}.png')).astype(float) for f in range(39)]
 diffs=[float(np.abs(a[(f+1)%39]-a[f]).mean()) for f in range(39)]
 assert diffs[-1]<=max(diffs[:-1])*1.25+1e-8
 metrics[name]={'maximum':max(diffs),'raccord_38_00':diffs[-1]}
checks.append('Raccords des deux lumières contrôlés (pas de saut supérieur au max interne +25%)')
(O/'verification.json').write_text(json.dumps({'checks':checks,'light_steps':metrics,'runtime_validated':False},ensure_ascii=False,indent=2));print('\n'.join(checks))
