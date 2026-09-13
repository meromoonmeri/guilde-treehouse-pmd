from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/northern_calques_v1';C=R/'renders/crooked_statique_v2';L=R/'renders/spring_pulsation_v2';checks=[]
def load(p):return Image.open(p).convert('RGBA')
for root in [O,C,L]:
 for p in root.rglob('*.png'):
  with Image.open(p) as im:im.load()
for mode in ['jour','nuit']:
 files=sorted((O/mode).glob('0*.png'));assert len(files)==9;comp=Image.new('RGBA',(456,432))
 for p in files:im=load(p);assert im.size==(456,432);comp.alpha_composite(im)
 assert np.array_equal(np.array(comp),np.array(load(O/mode/'composition.png')))
terrain=Image.new('RGBA',(456,432))
for n in ['05_rochers_arriere','06_arene_centrale','07_socle_arene','08_falaises_avant']:terrain.alpha_composite(load(O/'jour'/(n+'.png')))
assert np.array_equal(np.array(terrain),np.array(load(O/'terrain_detoure.png')))
m=np.array(Image.open(O/'masque_arene.png'))>0;assert m[216,228];yy,xx=np.where(m);center=[float(xx.mean()),float(yy.mean())];assert abs(center[0]-228)<20 and abs(center[1]-216)<20
checks.append('Northern: 2 recompositions exactes, 4 strates terrain recomposees sans perte, arene couvrant le centre [228,216]')
for idx in ['01','02','03']:
 comp=Image.new('RGBA',(320,240))
 for p in sorted((C/idx).glob('0*.png')):comp.alpha_composite(load(p))
 assert np.array_equal(np.array(comp),np.array(load(C/idx/'composition.png')))
assert not list(C.rglob('*.gif')) and not list(C.rglob('*.webp'))
checks.append('Crooked: 3 compositions statiques exactes, aucun fichier anime dans ce nouveau pack')
first=np.array(load(L/'colonne/00.png'));steps=[];alphas=[]
for f in range(78):
 a=np.array(load(L/'colonne'/f'{f:02}.png'));mask=(a[:,:,3]>0)&(first[:,:,3]>0);assert np.array_equal(a[:,:,:3][mask],first[:,:,:3][mask]);assert not np.any(a[a[:,:,3]==0]);assert np.all(a[:,:275,3]==0) and np.all(a[:,325:,3]==0) and np.all(a[201:,:,3]==0);alphas.append(float(a[:,:,3].sum()))
assert alphas[0]==min(alphas) and alphas[39]==max(alphas)
assert all(alphas[i+1]>=alphas[i] for i in range(39));assert all(alphas[i+1]<=alphas[i] for i in range(39,77))
checks.append('Spring: 78 frames, RGB fixes, alpha monte puis descend une fois par boucle ; aucune couleur parasite dans alpha zero ou hors colonne')
with Image.open(L/'animation.webp') as im:
 assert im.n_frames==78
 for f in range(78):im.seek(f);im.load()
checks.append('WebP Spring: 78 images decodees')
result={'checks':checks,'arena_mask_centroid':center,'runtime_validated':False};(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('\n'.join(checks))
