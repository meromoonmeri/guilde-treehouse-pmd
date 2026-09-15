from pathlib import Path
import io,json,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_ecumes_v6';P=O/'antre';S=O/'sprites';m=json.loads((O/'manifest.json').read_text());W,H=m['size']
def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
def merge(layers):
 out=Image.new('RGBA',(W,H))
 for layer in layers:out.alpha_composite(layer)
 return out
static={n:im(P/f'ecumes6_{n}.png') for n in m['static']};rocknames=['02_paroi_fond','03_bordure_gauche','04_bordure_droite','05_rebord_bas'];platformnames=['06_disque_natif']+[f'07_pas_japonais_{k}' for k in range(1,4)]
rock=np.maximum.reduce([np.array(static[n])[:,:,3] for n in rocknames])>0;stone=np.array(merge([static[n] for n in platformnames]));dry=rock|(stone[:,:,3]>0)
for n in rocknames:assert np.array_equal(np.array(static[n]),a(R/f'renders/antre_harmonie_v3/antre/harmonie_{n}.png'))
assert m['native_platform_proof']['FrameLength']==10 and len(m['native_platform_proof']['Frames'])==8
contacts=[n for n in m['animated'] if n.startswith('08_')]
for p in range(m['frames']):
 layers=dict(static)
 for n in m['animated']:
  layers[n]=im(P/f'ecumes6_{n}_{p:02}.png');arr=np.array(layers[n]);assert layers[n].size==(W,H)
  if n!='00_bassin_regenere':assert not np.any(arr[:,:,3][dry]),(p,n)
  period=8 if n.startswith('08_') else 3 if n.startswith('20_') else 4
  assert np.array_equal(arr,a(P/f'ecumes6_{n}_{p%period:02}.png'))
 out=np.array(merge([layers[n] for n in m['order']]));assert np.all(out[:,:,3]==255);assert np.array_equal(out,a(P/f'ecumes6_composition_{p:02}.png'));assert np.array_equal(out[stone[:,:,3]>0],stone[stone[:,:,3]>0])
 # Reconstruct the actual native8key full platform sprite from the separated water and stone layers.
 native=Image.new('RGBA',(W,H));native.alpha_composite(im(S/f'plateforme_native_complete_{p%8:02}.png'),tuple(m['platform']['origin']));expected=np.array(native);expected[rock]=0
 recovered=np.array(merge([layers[n] for n in contacts]+[layers[n] for n in platformnames]));assert np.array_equal(recovered,expected)
 for k in range(1,7):
  stream=np.array(layers[f'10_cascade_{k}'])[:,:,3]>0;foam=np.array(layers[f'20_ecume_{k}'])[:,:,3]>0;assert (stream&foam).sum()>=5,(k,p,int((stream&foam).sum()))
with zipfile.ZipFile(P/'antre_ecumes_v6.ora') as z:
 ls=[im(io.BytesIO(z.read(l.get('src')))) for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack'))];assert np.array_equal(np.array(merge(ls)),a(P/'COMPOSITION.png'))
assert sum(m['durations_ms'])==4000
assert len({a(S/f'bassin_regenere_{i:02}.png').tobytes() for i in range(4)})==4
assert Image.open(P/'ANIMATION.webp').n_frames==24
assert m['platform']['disc_size']==[72,53]
print('PASS:26layers/24states; unchanged walls and stone RGB; native8pose water reconstructed exactly;4basin poses;4/3/8periods; all6fall/foam junctions overlap every frame; ORA exact; no engine validation.')

from scipy import ndimage as nd
wet=~dry;distance=nd.distance_transform_edt(~rock);edge=(distance>0)&(distance<=6)&wet
new=[];old=[]
for p in range(4):
 new.append(a(P/f'ecumes6_00_bassin_regenere_{p:02}.png')[:,:,:3].astype(float))
 old.append(a(R/f'renders/antre_bassin_v4/antre/bassin4_00_bassin_regenere_{p:02}.png')[:,:,:3].astype(float))
 bank=a(P/f'ecumes6_09_rives_roche_eau_{p:02}.png');bm=bank[:,:,3]>0
 assert not np.any(bm&~edge);assert bank[:,:,3].max()<=255
 assert np.all(new[-1][edge & (distance<=3)]==[131,218,230])
new_motion=float(np.mean([abs(new[(p+1)%4]-new[p])[wet].mean() for p in range(4)]));old_motion=float(np.mean([abs(old[(p+1)%4]-old[p])[wet].mean() for p in range(4)]));assert new_motion<old_motion*.25
for p in range(24):
 for k in range(1,7):
  fa=a(P/f'ecumes6_20_ecume_{k}_{p:02}.png')[:,:,3]>0;stream=a(P/f'ecumes6_10_cascade_{k}_{p:02}.png')[:,:,3]>0;labs,count=nd.label(fa,np.ones((3,3)))
  assert count>0
  for lab in range(1,count+1):assert np.any((labs==lab)&stream)
print('PASS additional:bank only on wet6px border,stable basin tone at shores,all foam components attached to their cascade. Mean cyclic RGB change',new_motion,'versus V4',old_motion)
(O/'audit.json').write_text(json.dumps({'mean_basin_cyclic_change':new_motion,'previous_change':old_motion,'ratio':new_motion/old_motion,'foam_connected_all24states':True,'banks_wet_side_only':True,'native_platform_unchanged':True,'runtime_validated':False},indent=2)+'\n')

# Every bank color is taken from the actual native shoreline pose, not an approximate low-alpha blue.
for p in range(4):
 bank=a(P/f'ecumes6_09_rives_roche_eau_{p:02}.png');ref=a(S/f'rive_altere_native_{p}.png')
 assert set(map(tuple,bank[bank[:,:,3]>0])).issubset(set(map(tuple,ref[ref[:,:,3]>0])))
assert len({a(P/f'ecumes6_09_rives_roche_eau_{p:02}.png').tobytes() for p in range(4)})==4
print('PASS: four distinct native-color blue bank poses; generated left/front/right foam attached throughout.')
