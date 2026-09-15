from pathlib import Path
import io,json,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_fidele_v1';m=json.loads((O/'manifest.json').read_text());W,H=m['size'];ox,oy=m['source_origin']
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
def mask(name):return a(O/name)[:,:,0]>0
original=im(R/m['source']);src=np.array(original);allow=mask('MASQUE_MODIFICATIONS_AUTORISEES.png');core=mask('MASQUE_source_preservee.png');reference=np.pad(src,((16,32),(24,24),(0,0)),mode='reflect')
terrain_names=['02_roche_cascade','03_herbe_berges','04_vegetation_arriere','05_canopy_avant_gauche','06_canopy_avant_droite']
terrain=np.maximum.reduce([a(O/f'jour/lake_jour_{n}.png')[:,:,3] for n in terrain_names])>0
statics=m['static'];stone_names=[n for n in statics if n.startswith(('10_','11_'))];stone_mask=np.maximum.reduce([a(O/f'jour/lake_jour_{n}.png')[:,:,3] for n in stone_names])>0
actual=[]
for mode in ['jour','nuit']:
 P=O/mode;ref=reference if mode=='jour' else np.array(night(Image.fromarray(reference)))
 for phase in range(m['frames']):
  layers={}
  for n in m['layer_order']:
   path=P/(f'lake_{mode}_{n}_{phase:02}.png' if n in m['animated'] else f'lake_{mode}_{n}.png');layer=im(path);assert layer.size==(W,H);layers[n]=layer
   if mode=='nuit':
    day=im(O/'jour'/(f'lake_jour_{n}_{phase:02}.png' if n in m['animated'] else f'lake_jour_{n}.png'));assert np.array_equal(np.array(layer),np.array(night(day)))
   if n.startswith('12_'):assert not np.any((np.array(layer)[:,:,3]>0)&(terrain|stone_mask))
  out=Image.new('RGBA',(W,H))
  for n in m['layer_order']:out.alpha_composite(layers[n])
  aa=np.array(out);assert np.all(aa[:,:,3]==255);assert np.array_equal(aa,a(P/f'lake_{mode}_composition_{phase:02}.png'));assert np.array_equal(aa[core&~allow],ref[core&~allow])
  if mode=='jour':actual.append(int(np.all(aa[oy:oy+312,ox:ox+456]==src,axis=2).sum()))
  for n in m['animated']:
   if n.startswith('07_'):continue
   period=3 if n.startswith('08_') else 8;assert np.array_equal(np.array(layers[n]),a(P/f'lake_{mode}_{n}_{phase%period:02}.png'))
  foam=np.array(layers['08_ecume_impact'])[:,:,3]>0;fall=np.array(layers['07_cascade_descendante'])[:,:,3]>0;assert np.any(nd.binary_dilation(fall)&foam)
 with zipfile.ZipFile(P/f'waterfall_lake_{mode}.ora') as z:
  out=Image.new('RGBA',(W,H))
  for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack')):out.alpha_composite(im(io.BytesIO(z.read(l.get('src')))))
  assert np.array_equal(np.array(out),a(P/'COMPOSITION.png'))
 assert np.array_equal(a(P/'COMPOSITION_CADRE_ORIGINAL.png'),a(P/'COMPOSITION.png')[oy:oy+312,ox:ox+456])
 assert Image.open(P/'ANIMATION.webp').n_frames==24
assert sum(m['durations_ms'])==4000
# Recover material coordinates to independently verify downward motion and seamless temporal wrap.
material=a(O/'sprites/matiere_cascade_gba.png');yy,xx=np.mgrid[:H,:W];fallmask=mask('MASQUE_cascade.png')
for phase in range(24):
 expected=material[(yy-oy-2*phase)%48,np.clip(xx-ox-188,0,75)];got=a(O/f'jour/lake_jour_07_cascade_descendante_{phase:02}.png');assert np.array_equal(got[fallmask],expected[fallmask])
assert np.array_equal(material[(yy-oy-48)%48,np.clip(xx-ox-188,0,75)],material[(yy-oy)%48,np.clip(xx-ox-188,0,75)])
report={'source_size':[456,312],'original_pixels_guaranteed_unchanged':int((core&~allow).sum()),'actual_unchanged_pixels_per_frame':actual,'actual_unchanged_percent_initial':actual[0]/(456*312)*100,'day_night_layer_filter_exact':True,'no_original_core_rescaling':True,'original_water_depths_preserved_outside_local_replacements':True,'fall_motion_downward':True,'ora_exact_both_modes':True,'runtime_validated':False}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS:original core unchanged outside localized edits,24day/nightstates,22layers, exact night filter,3/8cycles,downward waterfall and loop,ORA,crops. No runtime test.',report['actual_unchanged_percent_initial'])
