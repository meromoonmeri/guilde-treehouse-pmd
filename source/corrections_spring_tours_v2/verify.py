"""Independent disk/ORA/night checks. Image checks, NOT PMDO runtime validation."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET,io
import numpy as np
from scipy.ndimage import label
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/corrections_spring_tours_v2'
def load(p):return Image.open(p).convert('RGBA')
def equal(a,b):assert np.array_equal(np.array(a),np.array(b))
def merge(ls,size):
 a=Image.new('RGBA',size)
 for l in ls:a.alpha_composite(l)
 return a
M=json.loads((O/'manifest.json').read_text());counts={'night_layers':0,'ora_compositions':0,'spring_frames':0}
for m in M:
 p=O/m['id'];prefix=m.get('prefix','cs2_spring')
 for day in (p/'jour').glob('cs2_*.png'):
  a=np.array(load(day));rgb=a[:,:,:3].astype(float);gray=.299*rgb[:,:,0]+.587*rgb[:,:,1]+.114*rgb[:,:,2];lum=gray/255;k=.20+.30*lum
  result=(rgb*.95+gray[:,:,None]*(1-.95))*(k[:,:,None]*np.array([.52,.70,1.60]));result[:,:,2]+=6*lum
  mask=a[:,:,3]>0;a[:,:,:3][mask]=result.clip(0,255).astype('uint8')[mask]
  equal(a,load(p/'nuit'/day.name.replace('_jour_','_nuit_')));counts['night_layers']+=1
 for mode in ['jour','nuit']:
  d=p/mode;ls=[load(d/f'{prefix}_{mode}_{n}{"_39" if n in m["animated"] else ""}.png') for n in m['layers']]
  equal(merge(ls,tuple(m['size'])),load(d/'COMPOSITION.png'))
  with zipfile.ZipFile(next(d.glob('*.ora'))) as z:
   assert z.testzip() is None;stack=ET.fromstring(z.read('stack.xml')).find('stack');ora_layers=[load(io.BytesIO(z.read(e.attrib['src']))) for e in reversed(list(stack))]
   equal(merge(ora_layers,tuple(m['size'])),load(d/'COMPOSITION.png'));equal(load(io.BytesIO(z.read('mergedimage.png'))),load(d/'COMPOSITION.png'));counts['ora_compositions']+=1
 if m['id']=='spring':
  yy,xx=np.mgrid[:600,:600];outside=~((xx>=275)&(xx<325)&(yy<201));old=R/'renders/spring_pulsation_v2';native=R/'renders/soleil_spring_v1/spring';fixed=None
  for f in range(78):
   day=p/'jour';ls=[load(day/f'cs2_spring_jour_{n}{f"_{f:02}" if n in m["animated"] else ""}.png') for n in m['layers']];beam=np.array(ls[-1]);original=np.array(load(old/'colonne'/f'{f:02}.png'))
   equal(beam[:,:,:3],original[:,:,:3]);assert beam[:,:,3].max()<=89
   if fixed is None:fixed=beam[:,:,:3]
   equal(fixed,beam[:,:,:3]);prior=merge([load(old/'01_decor_escalier.png'),load(native/'02_cycle_3'/f'{f//2%3:02}.png'),load(native/'03_cycle_13'/f'{f//2%13:02}.png'),load(old/'02_colonne_nettoyee.png'),Image.fromarray(original)],(600,600))
   equal(np.array(merge(ls,(600,600)))[outside],np.array(prior)[outside]);counts['spring_frames']+=1
  assert sum(m['durations_ms'])==6500
 else:
  tower=m['id'].split('_')[0];mask=np.array(Image.open(p/'MASQUE_ARCHITECTURE_PRESERVEE.png'))>0
  equal(np.array(load(p/'jour/COMPOSITION.png'))[mask],np.array(load(R/f'renders/tours_hooh_v1/{tower}_entree/jour/COMPOSITION.png'))[mask])
  path=np.array(Image.open(p/'MASQUE_CHEMIN.png'))>0;components,n=label(path);assert n==1 and path[-1].any() and path[305,320]
  native=load(R/'Apple_Woods_entrance_TDS.png')
  for key,stem in [('grass_samples','apple_herbe_native'),('path_samples','apple_chemin_natif')]:
   for i,(x,y) in enumerate(m[key]):equal(native.crop((x,y,x+24,y+24)),load(O/'sprites'/f'{stem}_{i}.png'))
  for i,t in enumerate(m['tree_provenance']):
   original=np.array(load(O/'sprites'/f'pommier_natif_{i}.png'));autumn=np.array(load(O/'sprites'/f'pommier_automne_{i}.png'));equal(original[:,:,3],autumn[:,:,3]);mask=original[:,:,3]>0;equal(original[mask],np.array(native.crop(tuple(t['source_box'])))[mask])
counts.update(status='PASS',path_connectivity='single image-mask component; not collision validation',native_materials='exact sample RGB; tree geometry unscaled, foliage adapted',night='exact Abyss formula per layer',runtime_PMDO_tested=False)
(O/'verification_independante.json').write_text(json.dumps(counts,indent=2));print(json.dumps(counts,indent=2))
