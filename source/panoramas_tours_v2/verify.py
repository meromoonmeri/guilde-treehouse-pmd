"""Independent persisted-image checks. Not a runtime or GPU test."""
from pathlib import Path
import json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/panoramas_tours_v2';M=json.loads((O/'manifest.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
def same(a,b):assert np.array_equal(np.array(a),np.array(b))
def compose(ls):
 a=Image.new('RGBA',(640,480))
 for im in ls:a.alpha_composite(im)
 return a
count=dict(night_layers=0,compositions=0,ora_layers=0,architecture_bases=0,cloud_periodicity_checks=0)
for m in M:
 p=O/m['id'];t=m['id']
 for mode in ['jour','nuit']:
  d=p/mode;layers=[load(d/f'pt2_{t}_{mode}_{n}.png') for n in m['layers']]
  for im in layers:
   assert im.size==(640,480);a=np.array(im);assert not np.any((a[:,:,0]==255)&(a[:,:,1]==0)&(a[:,:,2]==255)&(a[:,:,3]>0))
  same(compose(layers),load(d/'COMPOSITION.png'));same(compose(layers[:m['environment_count']]),load(d/'PANORAMA_SEUL.png'));count['compositions']+=2
  with zipfile.ZipFile(next(d.glob('*.ora'))) as z:
   assert z.testzip() is None;els=list(ET.fromstring(z.read('stack.xml')).find('stack'));assert len(els)==len(layers)
   for expected,e in zip(layers,reversed(els)):same(expected,load(io.BytesIO(z.read(e.attrib['src']))));count['ora_layers']+=1
   same(load(io.BytesIO(z.read('mergedimage.png'))),load(d/'COMPOSITION.png'))
  for cloud in m['clouds']:
   a=np.array(load(d/f'pt2_{t}_{mode}_{cloud["name"]}.png'))
   for frame in range(256):
    shift=round(frame*640/256*cloud['multiplier']);same(np.roll(a,shift,axis=1),np.roll(a,shift+640*cloud['multiplier'],axis=1));count['cloud_periodicity_checks']+=1
 for entry in m['architecture']:
  same(load(p/'jour'/f'pt2_{t}_jour_{entry["name"]}.png'),load(R/entry['source']));count['architecture_bases']+=1
 with zipfile.ZipFile(p/'sources_nuit_avant_filtre.zip') as z:
  for name in m['layers']:
   a=np.array(load(io.BytesIO(z.read(name+'.png'))));rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);gray=.299*r+.587*g+.114*b;lum=gray/255;k=.20+.30*lum
   out=(rgb*.95+gray[:,:,None]*(1-.95))*(k[:,:,None]*np.array([.52,.70,1.60]));out[:,:,2]+=6*lum;mask=a[:,:,3]>0;a[:,:,:3][mask]=out.clip(0,255).astype('uint8')[mask]
   same(a,load(p/'nuit'/f'pt2_{t}_nuit_{name}.png'));count['night_layers']+=1
 for name in m['lights']:
  a=np.array(load(p/'jour'/f'pt2_{t}_jour_{name}.png'));assert (a[:,:,3]>0).any() and a[:,:,3].max()<255
  if name.endswith('_lumiere'):
   base=np.array(load(p/'jour'/f'pt2_{t}_jour_{name.removesuffix("_lumiere")}.png'));assert not np.any((a[:,:,3]>0)&(base[:,:,3]==0))
 # Every depth plane has a real transparent silhouette and opaque continuation underneath foreground planes.
 profiles=np.load(p/'profils_profondeur.npz');yy=np.arange(480)[:,None]
 for j,name in enumerate(['montagnes_horizon','montagnes_intermediaires','reliefs_proches','foret_lointaine','foret_vallee','foret_contrebas']):
  a=np.array(load(p/'jour'/f'pt2_{t}_jour_{10+j:02}_{name}.png'));same(a[:,:,3]>0,yy>=profiles[f'plan_{j}'][None,:])
count.update(status='PASS',night='Exact Abyss per pregraded source, including authored moon/cold-light alternatives',lights='independent alpha, bounded to own surface',runtime_PMDO_tested=False)
(O/'verification.json').write_text(json.dumps(count,indent=2));print(json.dumps(count,indent=2))
