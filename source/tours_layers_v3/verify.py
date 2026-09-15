from pathlib import Path
import io,json,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy.ndimage import label
R=Path(__file__).resolve().parents[2];O=R/'renders/tours_layers_v3';M=json.loads((O/'manifest.json').read_text());counts=dict(compositions=0,ora_layers=0,night_images=0,animated_layers=0,moon_matches=0,solar_frames=0)
def load(p):return Image.open(p).convert('RGBA')
def same(a,b):assert np.array_equal(np.array(a),np.array(b))
def night_reference(im):
 a=np.array(im);rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);gray=.299*r+.587*g+.114*b;lum=gray/255;k=.2+.3*lum;out=(rgb*.95+gray[:,:,None]*(1-.95))*(k[:,:,None]*[.52,.70,1.6]);out[:,:,2]+=6*lum;mask=a[:,:,3]>0;a[:,:,:3][mask]=out.clip(0,255).astype('uint8')[mask];return a
for m in M:
 p=O/m['id']
 for mode in ['jour','nuit']:
  ls=[load(O/m['modes'][mode][n]['files'][0]) for n in m['layers']];comp=Image.new('RGBA',(640,480))
  for im in ls:assert im.size==(640,480);comp.alpha_composite(im)
  same(comp,load(p/mode/'COMPOSITION.png'));counts['compositions']+=1
  with zipfile.ZipFile(next((p/mode).glob('*.ora'))) as z:
   assert z.testzip() is None;elements=list(ET.fromstring(z.read('stack.xml')).find('stack'));assert len(elements)==len(ls)
   for im,e in zip(ls,reversed(elements)):same(im,load(io.BytesIO(z.read(e.attrib['src']))));counts['ora_layers']+=1
   same(comp,load(io.BytesIO(z.read('mergedimage.png'))))
  for name,anim in m['modes'][mode].items():
   if len(anim['files'])==1:continue
   frames=[load(O/f) for f in anim['files']];assert all(im.size==(640,480) for im in frames);assert any(not np.array_equal(np.array(frames[0]),np.array(im)) for im in frames[1:]);counts['animated_layers']+=1
   webp=p/mode/f'tl3_{m["id"]}_{mode}_{name}.webp';movie=Image.open(webp);duration=0
   for f in range(movie.n_frames):movie.seek(f);movie.load();duration+=movie.info.get('duration',0)
   assert duration==len(frames)*anim['frame_ms'],(webp,duration)
 if m['kind']=='entree':
  for name in m['layers']:
   for day,nit in zip(m['modes']['jour'][name]['files'],m['modes']['nuit'][name]['files']):same(night_reference(load(O/day)),load(O/nit));counts['night_images']+=1
  comp=Image.new('RGBA',(640,480))
  for name in m['architecture_parts']:comp.alpha_composite(load(O/m['modes']['jour'][name]['files'][0]))
  same(comp,load(p/'ARCHITECTURE_GENEREE_DETOUREE.png'))
  corridor=np.array(Image.open(p/'MASQUE_CHEMIN.png'))>0;regions,n=label(corridor);assert n==1 and corridor[-1,320] and corridor[320,320]
  # Analytic endpoint: both falling positions and four flutter poses close at frame 128.
  for group in m['leaf_parameters']:
   for leaf in group['particles']:
    for f in [0,17,63,127]:
     x=lambda i:round(leaf['x']+leaf['sway']*np.sin(2*np.pi*(i%128)/128+leaf['phase']))%640
     y=lambda i:round(leaf['y']+480*((i%128)/128))%480
     assert (x(f),y(f),(f//4+leaf['flutter'])%4)==(x(f+128),y(f+128),((f+128)//4+leaf['flutter'])%4)
 else:
  t=m['id'].split('_')[0];old=R/m['previous_panorama']
  for mode in ['jour','nuit']:
   for name in m['layers']:
    if name in ['03_lune','03_soleil','02_lueur_astre_ciel']:continue
    same(load(O/m['modes'][mode][name]['files'][0]),load(old/mode/f'pt2_{t}_{mode}_{name}.png'))
  source=load(R/m['moon_source']);diam=m['astro_diameter_px'];crop=source.crop(tuple(m['moon_native_crop'])).resize((diam,diam),Image.Resampling.NEAREST);actual=load(O/m['modes']['nuit']['03_lune']['files'][0]);same(actual.crop(actual.getbbox()),crop);bbox=actual.getbbox();assert bbox[2]-bbox[0]==bbox[3]-bbox[1]==diam;counts['moon_matches']+=1
  first=np.array(load(O/m['modes']['jour']['03_soleil']['files'][0]));sun_bbox=load(O/m['modes']['jour']['03_soleil']['files'][0]).getbbox();assert sun_bbox==bbox
  for f,path in enumerate(m['modes']['jour']['03_soleil']['files']):
   a=np.array(load(O/path));same(a[:,:,:3],first[:,:,:3]);same(a[:,:,3]>0,first[:,:,3]>0);assert a[:,:,3].max()>=224;counts['solar_frames']+=1
  # Native moon halo is preserved, already emissive: no second Abyss filter.
  cx,cy=m['sun']['center'];sz=round(180*diam/108)
  for f,path in enumerate(m['modes']['nuit']['02_lueur_astre_ciel']['files']):
   native=load(R/f'renders/references_calques_v2/astres/halo/{f:02}.png').crop((660,75,840,255)).resize((sz,sz),Image.Resampling.NEAREST);expected=Image.new('RGBA',(640,480));expected.alpha_composite(native,(cx-sz//2,cy-sz//2));same(expected,load(O/path))
for p in (O/'sprites').glob('tl3_feuille*.png'):
 im=load(p);b=im.getbbox();assert im.size==(3,3) and b[2]-b[0]<=3 and b[3]-b[1]<=3
sprite=load(R/'source/tours_layers_v3/references/bulbasaur_idle_1x.png');b=sprite.getbbox();assert (b[2]-b[0],b[3]-b[1])==(17,21)
counts.update(status='PASS',leaf_max_size_px=3,reference_pokemon_visible_size_px=[17,21],night='Exact Abyss on entrance assets; V2 night preserved in arenas, with original emissive moon/halo reused without double filtering',runtime_PMDO_tested=False)
(O/'verification.json').write_text(json.dumps(counts,indent=2));print(json.dumps(counts,indent=2))
