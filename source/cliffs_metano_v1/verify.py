"""Contrôles indépendants des exports, sans prétendre valider leur rendu moteur."""
from pathlib import Path
import json,sys,hashlib,io,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/cliffs_metano_v1'
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
from sample import decode
sys.path.insert(0,str(ROOT/"source"))
import ciels_valides as approved

def rgba(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((OUT/'manifest.json').read_text());cfg=json.loads((ROOT/m['palette']).read_text());checks=[]
 def check(name,test):
  assert test,name
  checks.append(name)
 check('4 compositions, identifiants uniques',len(m['zones'])==4 and len({z['id'] for z in m['zones']})==4)
 check('Palette et références épinglées',sha(ROOT/m['palette'])==m['palette_sha256'] and all(sha(ROOT/r['path'])==r['sha256'] for r in m['references']))
 # Rebuild canonical reference swatches directly from native .tile banks.
 native=ROOT/'source/falaises_metano';meta=json.loads((native/'provenance.json').read_text())
 banks=[decode(native/'natifs'/f'Metano_Town_{n}.tile') for n in ['Base','Cliffs']]
 comp=Image.new('RGBA',(max(a.shape[1] for a in banks),max(a.shape[0] for a in banks)))
 for a in banks:comp.alpha_composite(Image.fromarray(a))
 colors=set()
 for name in ['herbe','roche','rebord','pied']:
  patch=comp.crop(meta['patches_from_composed_Base_and_Cliffs_xyxy_px'][name]);check('Échantillon natif exact : '+name,patch.tobytes()==rgba(native/'patches'/f'{name}.png').tobytes())
  a=np.array(patch);colors.update(map(tuple,a[a[:,:,3]==255,:3].tolist()))
 shadow=(96,56,88);check('Ombre mauve présente dans la banque native',bool(((banks[1][:,:,:3]==shadow).all(axis=2)&(banks[1][:,:,3]==255)).any()))
 colors.add(shadow);check('328 couleurs réellement issues des sources natives',colors==set(map(tuple,cfg['allowed_rgb'])) and len(colors)==328)
 basenames=[]
 for z in m['zones']:
  title=z['id'];raw=rgba(OUT/z['raw']);day=rgba(OUT/z['files']['terrain_jour']);a=np.array(day);mask=a[:,:,3]>0
  check(title+' : empreintes',sha(OUT/z['raw'])==z['raw_sha256'] and sha(OUT/z['files']['terrain_jour'])==z['terrain_sha256'])
  check(title+' : dimensions sans resampling, grille 8',raw.size==day.size==tuple(z['size']) and all(n%8==0 for n in day.size))
  check(title+' : alpha binaire et RGB invisible nul',set(np.unique(a[:,:,3]))=={0,255} and bool((a[~mask]==0).all()))
  check(title+' : aucun pixel hors palette',set(map(tuple,np.unique(a[mask,:3],axis=0).tolist()))<=colors)
  check(title+' : pas de magenta opaque',not bool(((a[:,:,0]>220)&(a[:,:,1]<60)&(a[:,:,2]>220)&mask).any()))
  check(title+' : nuit exacte Abyss',rgba(OUT/z['files']['terrain_nuit']).tobytes()==night(day).tobytes())
  mag=Image.new('RGBA',day.size,(255,0,255,255));mag.alpha_composite(day)
  check(title+' : magenta recomposé',mag.tobytes()==rgba(OUT/z['files']['magenta']).tobytes())
  for mode in ['jour','nuit']:
   with zipfile.ZipFile(OUT/z['files']['ora_'+mode]) as archive:
    tree=ET.fromstring(archive.read('stack.xml'));layers=list(tree.find('stack'));merged=Image.new('RGBA',day.size)
    check(title+' '+mode+' : ORA cinq calques',len(layers)==5 and archive.read('mimetype')==b'image/openraster')
    for layer in reversed(layers):merged.alpha_composite(rgba(io.BytesIO(archive.read(layer.get('src')))))
    check(title+' '+mode+' : recomposition ORA/PNG exacte',merged.tobytes()==rgba(OUT/z['files']['scene_'+mode]).tobytes()==rgba(io.BytesIO(archive.read('mergedimage.png'))).tobytes())
  basenames.extend(Path(f).name for f in z['files'].values())
 check('Basenames des exports uniques pour PNG to Tileset',len(basenames)==len(set(basenames)))
 for r in m['backgrounds']:
  actual=rgba(OUT/r['export'])
  if r.get('approved_family'):
   name,mode=r['kind'],r['mode']
   expected=approved.sky(actual.size,mode) if name=='ciel' else approved.stars(actual.size,mode,moon=True) if name=='astres' else approved.wrap(approved.clouds(mode),actual.size)
  else:
   source=ROOT/r['source'];assert sha(source)==r['sha256'];expected=rgba(source).resize(actual.size,Image.Resampling.NEAREST)
  assert actual.tobytes()==expected.tobytes(),r['export']
 check('134 calques : ciels/astres/nuages validés et océan V3',len(m['backgrounds'])==134)
 for mode in ['jour','nuit']:
  strip=rgba(OUT/'contexte'/f'METANO_CLIFFS_V1_nuages_bande_{mode}.png')
  check('Nuages '+mode+' six familles exactes sans agrandissement',strip.tobytes()==rgba(ROOT/'sprites/cote_dix_zones/fonds'/f'{mode}_nuages.png').tobytes())
  check('Wrap '+mode+' boucle exacte',approved.wrap(strip,(1264,848),1440).tobytes()==approved.wrap(strip,(1264,848),0).tobytes())
 for mode in ['jour','nuit']:
  frames=[rgba(OUT/'contexte'/f'METANO_CLIFFS_V1_ocean_{mode}_{i:02d}.png') for i in range(64)]
  check('Océan '+mode+' : 64 phases, alpha fixe, cycle non statique',all(f.getchannel('A').tobytes()==frames[0].getchannel('A').tobytes() for f in frames) and len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames})>8)
 (HERE/'verification.json').write_text(json.dumps({'status':'PASS','checks_count':len(checks),'checks':checks,'not_tested':['Rendu GPU et gameplay PMDO','Échelle en jeu et collisions','Identité des motifs aux tuiles et raccords entre cartes','Validation artistique utilisateur']},ensure_ascii=False,indent=2)+'\n')
 print(f'{len(checks)} contrôles PASS — aucune validation moteur revendiquée.')
if __name__=='__main__':main()
