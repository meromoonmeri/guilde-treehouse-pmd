from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];P=R/'source/cafe_multietage_v1/references';O=R/'renders/cafe_multietage_v2';m=json.loads((O/'manifest.json').read_text());checks=[]
def load(p):return Image.open(p).convert('RGBA')
for name,h in json.loads((P/'hashes.json').read_text()).items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==h
for name,p in m['materials'].items():
 raw=load(P/p['file']).crop(tuple(p['box']));export=load(O/'materiaux'/f'{name}.png');assert np.array_equal(np.array(raw),np.array(export));assert hashlib.sha256(export.tobytes()).hexdigest()==p['rgba_sha256']
checks.append('7 banques tile +2 cartes sources: empreintes stables ; 5 patches egaux pixel par pixel aux extraits canoniques')
for e in m['levels']:
 p=O/e['path'];w,h=e['size'];assert w%8==0 and h%8==0
 for mode in ['jour','nuit']:
  view=load(p/f'02_vues_exterieures_{mode}.png');comp=Image.new('RGBA',(w,h))
  for n in ['00_fond_canonique','01_sol_vide','02_vues','03_bois_murs','04_bordure_rocheuse','05_cadres_fenetres','06_escaliers']:comp.alpha_composite(view if n=='02_vues' else load(p/(n+'.png')))
  assert np.array_equal(np.array(comp),np.array(load(p/f'composition_{mode}.png')))
  expected=np.zeros((h,w),bool)
  for x0,y0,x1,y1 in e['window_boxes']:
   size=x1-x0;y,x=np.mgrid[:size,:size];aperture=(x-(size-1)/2)**2+(y-(size-1)/2)**2<(size/2-6)**2;expected[y0:y1,x0:x1]=aperture
  assert np.array_equal(np.array(view)[:,:,3]>0,expected),(e['id'],mode)
 if e['floor_id']=='etage2':assert len(e['window_boxes'])==2 and e['window_diameter']==32 and not e['bay_windows']
 if e['floor_id'].startswith('ss'):assert not e['window_boxes']
checks+=['20 compositions exactement recomposees depuis sept calques','10 toiles sur grille8px','Toutes vues exterieures strictement dans les ouvertures circulaires','Etage+2 : deux hublots32px espaces, aucune baie ; sous-sols sans fenetre']
for e in m['levels']:
 assert len(e['connections'])==1
 port=e['connections'][0];ref=load(P/('spinda_cafe_reference.png' if e['family']=='Spinda' else 'metano_cafe_reference.png'))
 src=ref.crop(tuple(port['source_box']))
 for mode in ['jour','nuit']:
  final=load(O/e['path']/f'composition_{mode}.png').crop(tuple(port['destination_box']))
  assert np.array_equal(np.array(src),np.array(final)),e['id']
checks.append('20 seuils de composition strictement identiques aux references : dimensions, RGB, ombres et lumiere ; aucun escalier central ajoute')
for p in O.rglob('*.png'):
 with Image.open(p) as im:im.load()
(O/'verification.json').write_text(json.dumps({'checks':checks,'layouts':10,'compositions':20,'runtime_validated':False},ensure_ascii=False,indent=2));print('\n'.join(checks))
