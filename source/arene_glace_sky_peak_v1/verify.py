from pathlib import Path
import json,io,zipfile,importlib.util
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/arene_glace_sky_peak_v1'
spec=importlib.util.spec_from_file_location('arena_peak',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
 m=json.loads((OUT/'manifest.json').read_text());checks=[]
 def check(title,ok):
  assert ok,title
  checks.append(title)
 check('Références et bruts épinglés',all(b.sha(ROOT/r['path'])==r['sha256'] for r in m['references']) and all(b.sha(OUT/r['path'])==r['sha256'] for r in m['raws']))
 layers={name:b.load(OUT/p) for name,p in m['layers'].items()}
 check('Huit plans RGBA960×720, grille8px',len(layers)==8 and all(im.size==(960,720) and im.mode=='RGBA' for im in layers.values()))
 for name,im in layers.items():
  a=np.array(im);mask=a[:,:,3]>0
  check(name+' : transparence propre',bool((a[~mask]==0).all()))
  check(name+' : aucune clé magenta opaque',not bool(((a[:,:,0]>220)&(a[:,:,1]<70)&(a[:,:,2]>220)&mask).any()))
 sky=np.array(layers['01_ciel_bleu_noir']);ref=np.array(b.climate.sky((960,720),'nuit'))
 check('65 lignes sombres du ciel validé inchangées',np.array_equal(sky[:65],ref[:65]))
 colors,counts=np.unique(ref[64,:,:3],axis=0,return_counts=True)
 check('Prolongement bleu-noir sans stries, RGB issu de la source',bool((sky[65:,:,:3]==colors[counts.argmax()]).all()))
 check('Étoiles natives inchangées',layers['02_etoiles_natives'].tobytes()==b.climate.stars((960,720),'nuit').tobytes())
 moon,meta=b.moon_native();sprite=b.load(OUT/'sprites/ARENE_SKYPEAK_V1_croissant_natif.png')
 check('Lune native33×36,516pixels visibles, RGBA exacts',sprite.size==(33,36) and meta['opaque_pixels']==516 and sprite.tobytes()==moon.tobytes())
 expected=b.blank();expected.paste(moon,(800,64))
 check('Lune placée sans redessin, resampling ni recoloration',expected.tobytes()==layers['03_lune_canonique'].tobytes())
 terrain=b.blank()
 for name,im in layers.items():
  if int(name[:2])>=5:terrain.alpha_composite(im)
 expected,_=b.place(b.grade(b.key(b.load(OUT/'bruts/arene_magenta.png'))),960,(0,140))
 check('Recomposition des quatre plans terrain exacte',terrain.tobytes()==expected.tobytes()==b.load(OUT/m['terrain']).tobytes())
 mountain,_=b.place(b.key(b.load(OUT/'bruts/montagnes_lointaines_magenta.png')),960,(0,45))
 check('Panorama indépendant, placement et normalisation exacts',mountain.tobytes()==layers['04_montagnes_lointaines'].tobytes())
 scene=b.blank()
 for im in layers.values():scene.alpha_composite(im)
 check('Recomposition finale PNG exacte',scene.tobytes()==b.load(OUT/m['composition']).tobytes())
 with zipfile.ZipFile(OUT/m['ora']) as archive:
  tree=ET.fromstring(archive.read('stack.xml'));planes=list(tree.find('stack'));ora=b.blank()
  for layer in reversed(planes):ora.alpha_composite(b.load(io.BytesIO(archive.read(layer.get('src')))))
  check('ORA huit plans : recomposition et mergedimage exacts',len(planes)==8 and ora.tobytes()==scene.tobytes()==b.load(io.BytesIO(archive.read('mergedimage.png'))).tobytes())
 route=Image.new('L',(960,720));ImageDraw.Draw(route).line([tuple(p) for p in m['route_check']['centerline']],fill=255,width=16)
 walkable=np.array(Image.open(OUT/'controle/ARENE_SKYPEAK_V1_sol_visible_masque.png'))>0
 check('Accès sud→centre, corridor16px sur le masque du sol visible',bool(walkable[np.array(route)>0].all()))
 moonmask=np.array(layers['03_lune_canonique'])[:,:,3]>0;combined=np.array(scene)
 check('Lune entièrement visible devant le ciel, non cachée par montagne',all(not np.array(im)[:,:,3][moonmask].any() for name,im in layers.items() if int(name[:2])>=4))
 report={'status':'PASS','checks_count':len(checks),'checks':checks,'not_tested':['Échelle en jeu, collisions et gameplay PMDO','RenduGPU ou intégration Ground','Approbation artistique utilisateur'],'note':'Le contrôle du corridor est une vérification sur les masques, pas un test de déplacement moteur.'}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'contrôles PASS')
if __name__=='__main__':main()
