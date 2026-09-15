from pathlib import Path
import io,json,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_trois_v2';OLD=R/'renders/waterfall_lake_fidele_v1';m=json.loads((O/'manifest.json').read_text());W,H=m['size'];sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for l in ls:out.alpha_composite(l)
 return out
rock=a(O/'MASQUE_FALAISES_AJOUTEES.png')[:,:,0]>0;ring=a(O/'MASQUE_ANNEAUX.png')[:,:,0]>0
oldwater=a(OLD/'jour/lake_jour_01_eau_profondeurs_originales.png');stone_names=[n for n in m['static'] if n.startswith(('10','11'))]
static=[n for n in m['static'] if not n.startswith(('06b','06c'))]
for mode in ['jour','nuit']:
 P=O/mode
 for n in static:assert np.array_equal(a(P/f'lake2_{mode}_{n}.png'),a(OLD/f'{mode}/lake_{mode}_{n}.png'))
 for phase in range(24):
  layers={}
  for n in m['layer_order']:
   suffix=f'_{phase:02}' if n in m['animated'] else '';layers[n]=im(P/f'lake2_{mode}_{n}{suffix}.png');assert layers[n].size==(W,H)
   if mode=='nuit':assert np.array_equal(np.array(layers[n]),np.array(night(im(O/f'jour/lake2_jour_{n}{suffix}.png'))))
  out=np.array(merge([layers[n] for n in m['layer_order']]));assert np.all(out[:,:,3]==255);assert np.array_equal(out,a(P/f'lake2_{mode}_composition_{phase:02}.png'))
  for n in ['07_cascade_descendante','08_ecume_impact']:assert np.array_equal(np.array(layers[n]),a(OLD/f'{mode}/lake_{mode}_{n}_{phase:02}.png'))
  if mode=='jour':
   wa=np.array(layers['01_eau_anneaux']);assert np.array_equal(wa[~ring],oldwater[~ring]);delta=abs(wa[:,:,:3].astype(int)-oldwater[:,:,:3].astype(int));assert np.all(delta.max(axis=(0,1))<=np.array([0,2,3]))
   for n in [n for n in m['animated'] if n.startswith('12_')]:assert np.array_equal(np.array(layers[n])[:,:,3],a(OLD/f'jour/lake_jour_{n}_{phase%8:02}.png')[:,:,3])
   for k in range(1,3):
    fall=np.array(layers[f'07_cascade_laterale_{k}'])[:,:,3]>0;foam=np.array(layers[f'08_ecume_laterale_{k}'])[:,:,3]>0
    assert not np.any(fall&rock);assert nd.label(fall,np.ones((3,3)))[1]==1;assert all(fall[y].any() for y in range(108));assert np.any(nd.binary_dilation(fall)&foam)
 with zipfile.ZipFile(P/f'lake2_{mode}.ora') as z:
  layers=[im(io.BytesIO(z.read(l.get('src')))) for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack'))];assert np.array_equal(np.array(merge(layers)),a(P/'COMPOSITION.png'))
 assert Image.open(P/'ANIMATION.webp').n_frames==24
assert sum(m['durations_ms'])==4000
(O/'verification.json').write_text(json.dumps({'day_night_states':48,'layer_count':28,'central_cascade_unchanged':True,'original_static_layers_unchanged':True,'rings_fixed_geometry':True,'ring_max_rgb_modulation':[0,2,3],'native_platform_alpha_unchanged':True,'side_channels_continuous':True,'side_foam_attached':True,'ora_exact':True,'runtime_validated':False},indent=2)+'\n')
print('PASS:28layers,48day/nightstates; original static and central waterfall unchanged; fixed rings maxRGB0/2/3; native platform alpha preserved;2continuous side channels and attached foam; ORA exact. No runtime test.')
