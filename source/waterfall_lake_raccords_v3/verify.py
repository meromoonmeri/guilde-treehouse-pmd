from pathlib import Path
import json,io,zipfile,sys,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_raccords_v3';OLD=R/'renders/waterfall_lake_trois_v2';m=json.loads((O/'manifest.json').read_text());W,H=m['size'];sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for l in ls:out.alpha_composite(l)
 return out
repair=a(O/'MASQUE_REPRISE_LOCALE.png')[:,:,0]>0;rock=a(O/'MASQUE_ROCHE.png')[:,:,0]>0
for mode in ['jour','nuit']:
 P=O/mode
 for phase in range(24):
  layers={}
  for n in m['layer_order']:
   suffix=f'_{phase:02}' if n in m['animated'] else '';l=im(P/f'lake3_{mode}_{n}{suffix}.png');layers[n]=l;assert l.size==(W,H)
   if n not in m['replaced_layers']:assert np.array_equal(np.array(l),a(OLD/f'{mode}/lake2_{mode}_{n}{suffix}.png'))
   if mode=='nuit':assert np.array_equal(np.array(l),np.array(night(im(O/f'jour/lake3_jour_{n}{suffix}.png'))))
  out=np.array(merge([layers[n] for n in m['layer_order']]));assert np.all(out[:,:,3]==255);assert np.array_equal(out,a(P/f'lake3_{mode}_composition_{phase:02}.png'));assert np.array_equal(out[~repair],a(OLD/f'{mode}/lake2_{mode}_composition_{phase:02}.png')[~repair])
  for k,ch in enumerate(m['side_channels'],1):
   fall=np.array(layers[f'07_cascade_laterale_{k}'])[:,:,3]>0;foam=np.array(layers[f'08_ecume_laterale_{k}'])[:,:,3]>0
   assert not np.any(fall&rock);assert np.array_equal(fall,a(O/f'MASQUE_CHUTE_{k}.png')[:,:,0]>0);assert nd.label(fall,np.ones((3,3)))[1]==1
   assert all(fall[y].any() for y in range(ch['top'],ch['bottom']+1));assert np.any(fall&foam)
   labs,count=nd.label(foam,np.ones((3,3)))
   for label in range(1,count+1):assert np.any(nd.binary_dilation(fall)&(labs==label))
 with zipfile.ZipFile(P/f'lake3_{mode}.ora') as z:
  ls=[im(io.BytesIO(z.read(l.get('src')))) for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack'))];assert np.array_equal(np.array(merge(ls)),a(P/'COMPOSITION.png'))
 assert Image.open(P/'ANIMATION.webp').n_frames==24
assert sum(m['durations_ms'])==4000
report={'layers':28,'checked_compositions':48,'approved_layers_unchanged':len(m['layer_order'])-len(m['replaced_layers']),'unchanged_outside_repair_mask_all_frames':True,'generated_water_masks_disjoint_from_generated_rock':True,'channels_continuous_and_fixed_all_frames':True,'all_foam_components_attached':True,'central_waterfall_unchanged':True,'lake_ring_and_platform_animations_unchanged':True,'ora_exact':True,'night_filter_exact':True,'runtime_validated':False}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS:48states,28layers,22approved layers unchanged; every pixel outside repair unchanged; exact rock/water boundary; continuous channels; attached foam; ORA/night. No runtime test.')
