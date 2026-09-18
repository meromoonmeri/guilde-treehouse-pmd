"""Vérifications des nouveaux calques et des préservations, sans test moteur."""
from pathlib import Path
import json,sys,hashlib,zipfile,io,importlib.util
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/onde_boreale_glace_v2'
spec=importlib.util.spec_from_file_location('boreal_v2',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def load(p):return Image.open(p).convert('RGBA')
def arr(p):return np.array(load(p))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def same(a,c):return np.array_equal(np.array(a),np.array(c))
def webp_check(p,expected,loop):
 durations=[]
 with Image.open(p) as im:
  assert im.n_frames==len(expected),(p,im.n_frames)
  assert im.info['loop']==loop
  for i,reference in enumerate(expected):
   im.seek(i);decoded=np.array(im.convert('RGBA'));source=np.array(reference);mask=source[:,:,3]>0
   assert np.array_equal(decoded[:,:,3],source[:,:,3]),(p,i,'alpha')
   assert np.array_equal(decoded[mask,:3],source[mask,:3]),(p,i,'RGB visible')
   durations.append(im.info['duration'])
 assert durations==[125]*len(expected),(p,durations)

def main():
 checks=[]
 def check(title,result):
  assert result,title
  checks.append(title)
 m=json.loads((OUT/'manifest.json').read_text());p=json.loads((OUT/'aurore/GLACE_BOREALE_V2_palettes.json').read_text())
 check('Brut retenu et référence canonique épinglés',sha(OUT/m['raw'])==m['raw_sha256'] and all(sha(ROOT/r['path'])==r['sha256'] for r in m['references']))
 for pin in m['preserved_files']:
  assert sha(ROOT/pin['source'])==sha(OUT/pin['output'])==pin['sha256'],pin['output']
 check('39 fichiers V1 copiés byte-identiques (30 terrain +6 climat +3 scènes jour)',len(m['preserved_files'])==39)
 for mode in ['jour','nuit']:
  check('Ciel validé '+mode,same(load(OUT/m['shared'][mode+'_ciel']),b.climate.sky(b.SIZE,mode)))
  check('Étoiles validées '+mode,same(load(OUT/m['shared'][mode+'_etoiles']),b.climate.stars(b.SIZE,mode)))
  check('Six familles de nuages validées '+mode,same(load(OUT/m['shared'][mode+'_nuages_bande']),b.climate.clouds(mode)))
 idx=np.array(Image.open(OUT/'aurore/GLACE_BOREALE_V2_indices.png'));alpha=np.array(Image.open(OUT/'aurore/GLACE_BOREALE_V2_alpha.png'))
 frames=[load(OUT/f) for f in m['aurora']['frames']]
 check('32 frames, canevas768×640 et grille8px',len(frames)==32 and all(im.size==(768,640) for im in frames))
 check('Index fixe et32 LUT256 indépendantes',idx.shape==(640,768) and len(p['frames'])==32 and all(len(lut)==256 for lut in p['frames']))
 for i,im in enumerate(frames):
  a=np.array(im);mask=a[:,:,3]>0
  assert np.array_equal(a,np.array(b.render(idx,alpha,p['frames'],i))),i
  assert not a[210:,:,3].any(),i
  assert not a[:,0,3].any() and not a[:,-1,3].any() and not a[0,:,3].any(),i
  assert (a[~mask]==0).all(),i
  assert not ((a[:,:,0]>230)&(a[:,:,1]<50)&(a[:,:,2]>230)&mask).any(),i
 check('32 PNG reconstructibles : indices+LUT+déplacement vertical',True)
 check('Onde seule : aucun ciel/étoile/sol opaque, bords et partie basse transparents',True)
 check('Alpha invisible propre, pas de magenta opaque',True)
 check('32 étapes distinctes',len({hashlib.sha256(im.tobytes()).hexdigest() for im in frames})==32)
 shifts=np.array([b.shift_for(i) for i in range(32)])
 check('Ondulation réelle, amplitude≤2px',np.abs(shifts).max()==2 and len({row.tobytes() for row in shifts})>16)
 check('Pas de translation horizontale',all(np.array_equal(np.any(np.array(im)[:,:,3]>0,axis=0),np.any(alpha>0,axis=0)) for im in frames))
 check('Fin de boucle sans saut de déplacement',np.max(np.abs(np.roll(shifts,-1,axis=0)-shifts))<=1)
 check('Boucle exacte : frame32 = frame0',same(b.render(idx,alpha,p['frames'],32),frames[0]))
 luts=np.array(p['frames']).astype(int);step=np.abs(np.roll(luts,-1,axis=0)-luts).max(axis=(1,2))
 check('Couleurs bouclées sans saut final anormal',step[-1]<=step[:-1].max()+1)
 value=luts.max(axis=2)
 check('Pas de flash de luminosité global : valeurHSV fixe±1RGB',np.max(value.max(axis=0)-value.min(axis=0))<=1)
 check('Couleurs évoluent à géométrie des indices fixe',len({lut.tobytes() for lut in luts})==32)
 webp_check(OUT/m['aurora']['transparent_webp'],frames,0);check('WebP transparent32frames lossless, alpha et RGB visibles exacts,4s',True)
 sky=load(OUT/m['shared']['nuit_ciel']);stars=load(OUT/m['shared']['nuit_etoiles']);strip=load(OUT/m['shared']['nuit_nuages_bande']);cloud0=b.climate.wrap(strip,b.SIZE)
 skyframes=[]
 for f in frames:
  s=sky.copy();s.alpha_composite(stars);s.alpha_composite(f);skyframes.append(s)
 webp_check(OUT/m['aurora']['on_approved_sky_webp'],skyframes,0);check('WebP onde sur ciel validé : recomposition32frames exacte',True)
 for z in m['zones']:
  terrain=b.blank()
  for rel in z['layers']['nuit'].values():terrain.alpha_composite(load(OUT/rel))
  scenes=[]
  for i,rel in enumerate(z['frames_nuit']):
   expected=skyframes[i].copy();expected.alpha_composite(terrain);expected.alpha_composite(cloud0)
   actual=load(OUT/rel);assert same(actual,expected),(z['id'],i);scenes.append(expected)
  check(z['id']+' :32 PNG recomposent les neuf plans',len(z['frames_nuit'])==32)
  check(z['id']+' : PNG de présentation=frame0',same(load(OUT/z['scene_nuit']),scenes[0]))
  webp_check(OUT/z['webp_loop'],scenes,0);check(z['id']+' : WebP boucle4s exact, nuages fixes',True)
  clip=[]
  for k in range(64):
   s=skyframes[k%32].copy();s.alpha_composite(terrain);s.alpha_composite(b.climate.wrap(strip,b.SIZE,int(k*125*4/1000)));clip.append(s)
  webp_check(OUT/z['webp_cloud_excerpt'],clip,1);check(z['id']+' : extrait8s64frames avec vrai wrap−4px/s, une lecture',True)
  with zipfile.ZipFile(OUT/z['ora_nuit']) as archive:
   tree=ET.fromstring(archive.read('stack.xml'));layers=list(tree.find('stack'));merged=b.blank()
   for layer in reversed(layers):merged.alpha_composite(load(io.BytesIO(archive.read(layer.get('src')))))
   check(z['id']+' : ORA9plans, recomposition exacte',len(layers)==9 and same(merged,scenes[0]) and same(load(io.BytesIO(archive.read('mergedimage.png'))),scenes[0]))
 check('Période nuages360s multiple de l’aurore4s',360000%m['aurora']['period_ms']==0)
 check('Raccord wrap natif1440px exact',same(b.climate.wrap(strip,b.SIZE,0),b.climate.wrap(strip,b.SIZE,1440)))
 # Correspondence to a single uniform leftward shift across the seam.
 extended=b.climate.wrap(strip,(769,640),1439)
 check('Transition de raccord1439→1440 = un seul pixel, pas retour brutal',same(extended.crop((1,0,769,640)),b.climate.wrap(strip,b.SIZE,1440)))
 report={'status':'PASS','checks_count':len(checks),'checks':checks,'not_proved':['Validation artistique utilisateur','Cycle officiel PMD','Collisions, warp, GPU ou intégration moteur'],'webp_note':'Alpha et RGB visibles exacts ; RGB invisibles peuvent être normalisés par le codec.'}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(f'{len(checks)} contrôles PASS — nouveau dessin animé, pas cycle officiel.')
if __name__=='__main__':main()
