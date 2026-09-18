from pathlib import Path
import json,hashlib,io,zipfile,importlib.util
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'renders/arene_glace_sky_peak_v2'
spec=importlib.util.spec_from_file_location('arena_panorama_v2',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def same(a,c):return np.array_equal(np.array(a),np.array(c))
def webp(path,expected):
 with Image.open(path) as im:
  assert im.n_frames==32 and im.info['loop']==0
  for i,ref in enumerate(expected):
   im.seek(i);a=np.array(im.convert('RGBA'));ref=np.array(ref);mask=ref[:,:,3]>0
   assert np.array_equal(a[:,:,3],ref[:,:,3]) and np.array_equal(a[mask,:3],ref[mask,:3]),(path,i)
   assert im.info['duration']==125

def main():
 m=json.loads((O/'manifest.json').read_text());checks=[]
 def check(name,result):assert result,name;checks.append(name)
 for pin in m['preserved']:assert b.sha(R/pin['source'])==b.sha(O/pin['output'])==pin['sha256'],pin['output']
 check('Huit calques V1 conservés byte-identiques',len(m['preserved'])==8)
 check('Bruts et références épinglés',all(b.sha(O/p['path'])==p['sha256'] for p in m['new_raws']) and all(b.sha(R/p['path'])==p['sha256'] for p in m['references']))
 layers={name:b.load(O/rel) for name,rel in m['layers'].items()}
 check('Dix plans alignés960×720, divisibles par8',len(layers)==10 and all(im.size==b.SIZE for im in layers.values()))
 idx=np.array(Image.open(O/m['aurora']['indexed']));alpha=np.array(Image.open(O/m['aurora']['alpha']));p=json.loads((O/m['aurora']['palette']).read_text())
 effects=[b.load(O/rel) for rel in m['aurora']['frames']]
 terrain=b.compose({name:im for name,im in layers.items() if name.startswith(('05_','06_','07_','08_'))});tm=np.array(terrain)[:,:,3]==255
 moon=np.array(layers['03_lune_canonique']);mm=moon[:,:,3]==255
 hide=b.compose({name:im for name,im in layers.items() if name.startswith(('04','05','06','07','08'))});clear=np.array(hide)[:,:,3]==0
 baseline=np.array(b.load(R/'renders/arene_glace_sky_peak_v1/ARENE_SKYPEAK_V1_composition_nuit.png'))
 scenes=[];skyframes=[];sides=[]
 for f,im in enumerate(effects):
  a=np.array(im);mask=a[:,:,3]>0
  assert same(im,b.frame(idx,alpha,p['frames'],f)),f
  assert (a[~mask]==0).all() and not a[400:,:,3].any(),f
  assert not ((a[:,:,0]>230)&(a[:,:,1]<50)&(a[:,:,2]>230)&mask).any(),f
  # No artificial fade to zero at the screen edges: actual filled sky, not bbox only.
  assert mask[:,0].sum()>100 and mask[:,-1].sum()>100
  assert np.any(mask,axis=0).all()
  visible=(a[:,:,3]>=24)&clear
  left=int(visible[:300,:120].sum());right=int(visible[:300,-120:].sum())
  assert left>15000 and right>15000,(f,left,right)
  sides.append((left,right))
  current={name:im if name=='02b_aurore_panoramique' else layer for name,layer in layers.items()}
  expected=b.compose(current);actual=b.load(O/m['scene_frames'][f]);assert same(actual,expected),f
  c=np.array(actual);assert np.array_equal(c[tm],baseline[tm]),(f,'terrain');assert np.array_equal(c[mm],moon[mm]),(f,'moon')
  scenes.append(actual)
  skyframes.append(b.compose({name:current[name] for name in ['01_ciel_bleu_noir','02_etoiles_natives','02b_aurore_panoramique','03_lune_canonique']}))
 check('32frames reconstructibles depuis indices/LUT/déplacement',len(effects)==32)
 check('Onde seule : alpha propre, pas de magenta/terrain ou ciel opaque',True)
 check('Chaque colonne du panorama possède des pixels d’aurore',True)
 check('Chaque bord conserve >100pixels alpha à toutes les phases',True)
 check('Aurore réellement visible dans les deux côtés du ciel : >15000pixels par côté/frame',True)
 check('32 compositions exactes de dix plans',len(scenes)==32)
 check('Terrain opaque inchangé dans toutes les compositions',True)
 check('Pixels opaques de lune natifs jamais recouverts par l’aurore',True)
 check('32frames distinctes',len({hashlib.sha256(im.tobytes()).hexdigest() for im in effects})==32)
 shifts=np.array([b.shift(f) for f in range(32)])
 check('Amplitude≤2px, mouvement non statique',np.abs(shifts).max()==2 and len({x.tobytes() for x in shifts})>16)
 check('Pas de saut final : déplacement≤1px/colonne entre deux frames',np.abs(np.roll(shifts,-1,axis=0)-shifts).max()<=1)
 check('Boucle exacte32=0',same(b.frame(idx,alpha,p['frames'],32),effects[0]))
 check('Aucune translation horizontale',all(np.array_equal(np.any(np.array(im)[:,:,3]>0,axis=0),np.any(alpha>0,axis=0)) for im in effects))
 lut=np.array(p['frames']).astype(int);delta=np.abs(np.roll(lut,-1,axis=0)-lut).max(axis=(1,2))
 check('Palette évolutive sans saut de raccord',len({x.tobytes() for x in lut})==32 and delta[-1]<=delta[:-1].max()+1)
 check('Valeur HSV constante à arrondiRGB près',np.ptp(lut.max(axis=2),axis=0).max()<=1)
 check('PNG de présentation = composition phase0',same(b.load(O/m['composition']),scenes[0]))
 for path,expected,title in [(m['webp'],scenes,'composition'),(m['overlay_webp'],effects,'onde transparente'),(m['sky_webp'],skyframes,'ciel et lune')]:
  webp(O/path,expected);check('WebP '+title+' :32frames,4s,alpha/RGB visibles exacts',True)
 with zipfile.ZipFile(O/m['ora']) as z:
  root=ET.fromstring(z.read('stack.xml'));parts=list(root.find('stack'));merged=b.blank()
  for part in reversed(parts):merged.alpha_composite(b.load(io.BytesIO(z.read(part.get('src')))))
  check('ORA dix calques et PNG recomposés exactement',len(parts)==10 and same(merged,scenes[0]) and same(b.load(io.BytesIO(z.read('mergedimage.png'))),scenes[0]))
 report={'status':'PASS','checks_count':len(checks),'checks':checks,'minimum_visible_pixels_left':min(x[0] for x in sides),'minimum_visible_pixels_right':min(x[1] for x in sides),'not_tested':['Validation artistique utilisateur','Rendu GPU, collisions ou navigation PMDO','Motifs natifs ou cycle officiel d’aurore']}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(f'{len(checks)} contrôles PASS — couverture gauche/droite vérifiée sur32frames.')
if __name__=='__main__':main()
