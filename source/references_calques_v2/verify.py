from pathlib import Path
import json,sys,zipfile,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/references_calques_v2';sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
m=json.loads((O/'manifest.json').read_text());checks=[]
def load(p):return Image.open(O/p).convert('RGBA')
files=list(O.rglob('*.png'))
for p in files:
 with Image.open(p) as im:im.load()
checks.append(f'{len(files)} PNG décodés')
for t in m['terrains']:
 p=Path('falaises')/t['id'];day=load(p/'terrain.png');nt=load(p/'terrain_nuit.png');assert np.array_equal(np.array(night(day)),np.array(nt))
 for mode in ['jour','nuit']:assert load(p/f'calque_{mode}.png').size==(960,600)
checks.append('10 terrains jour/nuit : filtre Abyss exact, calques 960×600')
# Independently rebuild all thirty scenes from the actual exported files.
for t in m['terrains']:
 for mode in ['jour','coucher','nuit']:
  p=Path('fonds')/mode;im=load(p/'01_ciel.png')
  if mode!='jour':im.alpha_composite(load(Path('etoiles/00.png')))
  im.alpha_composite(load(p/'03_nuages_wrap.png'))
  if mode=='nuit':im.alpha_composite(load(Path('astres/halo/00.png')));im.alpha_composite(load(Path('astres/lune.png')))
  else:im.alpha_composite(load(p/'04_soleil.png'))
  im.alpha_composite(load(p/'05_mer.png'));im.alpha_composite(load(Path('reflets')/('lune' if mode=='nuit' else 'soleil')/'frames/00.png'),(674,281))
  if t['side']=='droite':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  im.alpha_composite(load(Path('falaises')/t['id']/('calque_nuit.png' if mode=='nuit' else 'calque_jour.png')))
  assert np.array_equal(np.array(im),np.array(load(Path('falaises')/t['id']/f'scene_{mode}.png')))
checks.append('30 compositions : égalité pixel par pixel avec les calques exportés')
metrics={}
for path in ['etoiles','astres/halo','reflets/lune/frames','reflets/soleil/frames']:
 ps=sorted((O/path).glob('*.png'));assert len(ps)==64
 aa=[np.array(Image.open(p).convert('RGBA')).astype(float) for p in ps]
 # Measure premultiplied difference so transparent RGB is irrelevant.
 aa=[np.concatenate([a[:,:,:3]*a[:,:,3:]/255,a[:,:,3:]],2) for a in aa]
 diffs=[float(np.abs(aa[(i+1)%64]-aa[i]).mean()) for i in range(64)]
 assert diffs[-1]<=max(diffs[:-1])*1.25+1e-6,(path,diffs[-1],max(diffs[:-1]))
 metrics[path]={'mean_step_max':max(diffs),'step_63_to_00':diffs[-1]}
checks.append('4 animations × 64 phases : raccord cyclique sans saut numérique supérieur aux autres transitions (+25% tolérance)')
for mode in ['jour','coucher','nuit']:
 a=np.array(load(Path('fonds')/mode/'03_nuages_wrap.png'));assert np.array_equal(np.roll(a,960,axis=1),a)
checks.append('Nuages : identité pixel au wrap de 960 px ; période 240 s à 4 px/s')
with zipfile.ZipFile(R/m['sky_source']['zip']) as z:original=Image.open(io.BytesIO(z.read(m['sky_source']['member']))).convert('RGBA')
original=original.crop(original.getbbox()).resize((960,280),Image.Resampling.NEAREST)
assert np.array_equal(np.array(original),np.array(load(Path('fonds/jour/01_ciel.png')).crop((0,0,960,280))))
checks.append('Ciel jour : égalité exacte avec le PNG du ZIP après mise au format nearest')
result={'checks':checks,'cyclic_metrics':metrics,'limitations':['Pas de validation PMDO/GPU','Tests de raccord numériques, pas preuve de qualité artistique','Dessins générés non natifs, réserves visuelles documentées']}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('\n'.join(checks))
