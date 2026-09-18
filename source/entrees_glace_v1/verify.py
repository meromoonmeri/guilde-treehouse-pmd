"""Tests d'exports, parcours indicatifs et animations. Pas de validation PMDO."""
from pathlib import Path
import json,sys,hashlib,zipfile,io
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/entrees_glace_v1'
sys.path.insert(0,str(ROOT/'source'));import ciels_valides as climate
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'));from night import night
SIZE=(768,640)
def load(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((OUT/'manifest.json').read_text());checks=[];paths=[]
 def check(name,result):
  assert result,name
  checks.append(name)
 canonical=set()
 for ref in m['references']:
  p=ROOT/ref['path'];check('Référence épinglée '+ref['path'],sha(p)==ref['sha256']);canonical.update(map(tuple,np.unique(np.array(load(p))[:,:,:3].reshape(-1,3),axis=0).tolist()))
 check('Palette exclusivement issue des deux PNG PMD',canonical==set(map(tuple,m['ice_palette_rgb'])))
 check('Trois layouts distincts',len(m['zones'])==3 and len({z['raw_sha256'] for z in m['zones']})==3)
 for z in m['zones']:
  slug=z['id'];folder=OUT/slug;prefix='ICE_ENTRY_V1_'+slug
  check(slug+' brut inchangé',sha(OUT/z['raw'])==z['raw_sha256'])
  check(slug+' proportions normalisées uniformément',z['normalization']['resized_size']==[763,512] and z['normalization']['offset']==[2,128])
  terrain=load(folder/(prefix+'_terrain_jour.png'));a=np.array(terrain);valid=a[:,:,3]>0
  masks=[np.array(Image.open(folder/(prefix+'_masque_'+name+'.png')))>0 for name in ['sol_visible','profondeur_grotte','cliffs_reliefs','immersion_gauche','immersion_droite']]
  check(slug+' partitions visibles disjointes et complètes',np.array_equal(sum(v.astype(int) for v in masks),valid.astype(int)))
  route=np.array(Image.open(folder/(prefix+'_controle_parcours.png')))>0;walk=masks[0]|masks[1]
  check(slug+' corridor13px sol/seuil continu sans traverser les reliefs',not bool((route&~walk).any()))
  labels,_=ndimage.label(walk);sx,sy=z['south_xy'];tx,ty=z['threshold_xy'];check(slug+' sud et seuil dans même composante',labels[sy,sx]>0 and labels[sy,sx]==labels[ty,tx] and sy==639 and ty<360)
  paths.append({'id':slug,'south':z['south_xy'],'threshold':z['threshold_xy'],'corridor_width_pixels':13,'pixels':int(route.sum()),'out_of_walkable_pixels':int((route&~walk).sum()),'meaning':'Corridor de contrôle visuel, pas collision moteur ni warp.'})
  for mode in ['jour','nuit']:
   composite=Image.new('RGBA',SIZE)
   for name,path in z['layers'][mode].items():
    layer=load(OUT/path);b=np.array(layer);visible=b[:,:,3]>0
    check(slug+' '+mode+' '+name+' alpha/grille',layer.size==SIZE and set(np.unique(b[:,:,3]))<={0,255} and bool((b[~visible]==0).all()))
    if mode=='jour':check(slug+' '+name+' palette canonique',set(map(tuple,np.unique(b[visible,:3],axis=0).tolist()))<=canonical)
    else:check(slug+' '+name+' nuit Abyss exacte',layer.tobytes()==night(load(OUT/z['layers']['jour'][name])).tobytes())
    composite.alpha_composite(layer)
   expected=terrain if mode=='jour' else night(terrain)
   check(slug+' '+mode+' terrain recomposé exactement',composite.tobytes()==expected.tobytes())
   with zipfile.ZipFile(OUT/z['files']['ora_'+mode]) as archive:
    stack=ET.fromstring(archive.read('stack.xml')).find('stack');layers=list(stack);merged=Image.new('RGBA',SIZE)
    for layer in reversed(layers):merged.alpha_composite(load(io.BytesIO(archive.read(layer.get('src')))))
    check(slug+' '+mode+' ORA9plans exact',len(layers)==9 and merged.tobytes()==load(OUT/z['files']['scene_'+mode]).tobytes()==load(io.BytesIO(archive.read('mergedimage.png'))).tobytes())
  # Night foreground must stay fixed in every lossless animated scene frame.
  nightterrain=night(terrain);nt=np.array(nightterrain);mask=nt[:,:,3]==255
  with Image.open(OUT/z['files']['preview_webp']) as anim:
   check(slug+' aperçu animé 10frames',anim.n_frames==10)
   for i in range(anim.n_frames):
    anim.seek(i);frame=np.array(anim.convert('RGBA'));assert np.array_equal(frame[mask],nt[mask]),(slug,'moving terrain',i)
   check(slug+' terrain fixe dans les 10frames',True)
 for mode in ['jour','nuit']:
  check('Ciel validé '+mode,load(OUT/m['shared'][mode+'_ciel']).tobytes()==climate.sky(SIZE,mode).tobytes())
  check('Étoiles isolées '+mode,load(OUT/m['shared'][mode+'_etoiles']).tobytes()==climate.stars(SIZE,mode).tobytes())
  strip=load(OUT/m['shared'][mode+'_nuages_bande']);approved=load(ROOT/'sprites/cote_dix_zones/fonds'/f'{mode}_nuages.png')
  check('Six familles '+mode+' pixels exacts sans resampling',strip.tobytes()==approved.tobytes())
  f0=np.array(climate.wrap(strip,SIZE,0));fend=np.array(climate.wrap(strip,SIZE,1440));check('Wrap '+mode+' boucle et direction',np.array_equal(f0,fend) and climate.wrap(strip,SIZE,1).tobytes()!=climate.wrap(strip,SIZE,0).tobytes())
  for shift in [0,1,176,767,1439,1440,1441]:
   actual=np.array(climate.wrap(strip,SIZE,shift));expected=np.zeros((640,768,4),np.uint8);expected[:208]=np.array(strip)[:,(np.arange(768)+shift)%1440];assert np.array_equal(actual,expected)
  check('Wrap '+mode+' raccords modulo pixel-exacts',True)
 wave_frames=[]
 for record in m['aurora']['sources']:
  src=ROOT/record['source'];check('Onde source '+src.name,sha(src)==record['sha256'])
  a=np.array(load(src));labels,_=ndimage.label(a[:,:,3]>0);counts=np.bincount(labels.ravel());keep=np.where(counts>=40)[0];keep=keep[keep!=0];a[~np.isin(labels,keep)]=0
  expected=Image.new('RGBA',SIZE);expected.paste(Image.fromarray(a),tuple(record['offset']));actual=load(OUT/record['output']);check('Onde extraite sans ciel '+src.stem,actual.tobytes()==expected.tobytes())
  wave_frames.append(actual)
 check('10 ondes distinctes, sans translation globale',len({im.tobytes() for im in wave_frames})==10 and m['aurora']['wrap'] is False)
 with Image.open(OUT/'climat/ICE_ENTRY_V1_onde_canonique.webp') as anim:
  check('WebP overlay10frames',anim.n_frames==10)
  for i,im in enumerate(wave_frames):anim.seek(i);assert anim.convert('RGBA').tobytes()==im.tobytes()
 check('WebP overlay lossless exact',True)
 for i,f in enumerate(m['cycling_alternative']['frames']):check('Alternative V12 frame'+str(i)+' inchangée',sha(OUT/f)==sha(ROOT/'renders/boreales_palette_cycling_v12/couches'/f'PaletteCycleV12_frame_{i:02d}.png'))
 # Fixed modulo periods: both wave cycles divide the cloud period.
 check('Horloge commune sans saut au wrap360s',360000%1600==360000%960==0)
 allpng=list(OUT.rglob('*.png'));exports=[p.name for p in allpng if 'bruts' not in p.parts]
 check('BasenamesPNG uniques pour import',len(exports)==len(set(exports)))
 report={'status':'PASS','checks_count':len(checks),'checks':checks,'paths':paths,'not_tested':['Collisions et navigation PMDO','Rendu GPU et échelle moteur','Warp/destination de donjon','Approbation artistique utilisateur'],'browser':'voir viewer_checks.json : ne pas confondre DOM simulé et navigateur réel'}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'contrôles PASS ; trois corridors13px sol→seuil, pas de runtime PMDO.')
if __name__=='__main__':main()
