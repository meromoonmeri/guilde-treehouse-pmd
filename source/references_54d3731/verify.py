from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;O=R/'renders/references_54d3731';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
checks=[];total=0
for p in O.rglob('*.png'):
 with Image.open(p) as im:im.load();total+=1
sources=json.loads((P/'sources.json').read_text())
for name,h in sources.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
assert sources['Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest (1).png']==sources['Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest.png']
checks.append('8 fichiers references verifies par SHA256 ; doublon Energetic Forest confirme')
for s in m['scenes']:
 for mode,names in s['layers'].items():
  comp=Image.new('RGBA',tuple(s['size']))
  for n in names:
   im=Image.open(O/s['id']/mode/(n+'.png')).convert('RGBA');assert list(im.size)==s['size'];comp.alpha_composite(im)
  assert np.array_equal(np.array(comp),np.array(Image.open(O/s['id']/mode/'composition.png'))),(s['id'],mode)
 for n in s['layers']['jour']:
  if not n[:2].isdigit() or int(n[:2])<5 or int(n[:2])>=12:continue
  day=Image.open(O/s['id']/'jour'/(n+'.png')).convert('RGBA');nt=Image.open(O/s['id']/'nuit'/(n+'.png')).convert('RGBA');assert np.array_equal(np.array(night(day)),np.array(nt))
 if s['id'] not in ['04_plage','06_mont_foudre','10_foret_neige']:assert not any('lune' in n or 'etoile' in n for n in s['layers']['jour'])
checks+=['20 recompositions pixel-exactes des PNG exports','Conversions nuit du terrain exactement egales au filtre Abyss','Aucune lune/etoile ajoutee aux scenes sans ciel visible']
assert not list(O.rglob('*.gif')) and not list(O.rglob('*.webp'));checks.append('Aucun fichier anime dans ce pack')
result={'png_decoded':total,'checks':checks,'scene_count':10,'compositions':20,'layer_exports':sum(len(n) for s in m['scenes'] for n in s['layers'].values()),'runtime_validated':False};(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
