from pathlib import Path
import json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/mont_horn_altitude_v2';P=O/'mont_horn';S=O/'sprites';m=json.loads((O/'manifest.json').read_text());W,H=m['size']
def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
back=a(S/'horn_nuages_lointains_texture_wrap.png');front=a(S/'horn_nuages_overlay_texture_wrap.png');yy,xx=np.mgrid[:H,:W];v=np.clip((np.abs(xx-W//2)-65)/90,0,1);v=v*v*(3-2*v)
static={n:im(P/f'horn_{n}.png') for n in m['static_layers']};order=m['layer_order']
walk=a(O/'GUIDE_APPROCHE_24PX.png')[:,:,0]>0
for k in range(m['frames']):
 far=a(P/f'horn_02_nuages_lointains_{k:03}.png');near=a(P/f'horn_07_nuages_overlay_{k:03}.png');expected=np.roll(front,k*4,axis=1);expected[:,:,3]=np.rint(expected[:,:,3]*v).astype('uint8');expected[expected[:,:,3]==0]=0
 assert np.array_equal(far,np.roll(back,k*2,axis=1));assert np.array_equal(near,expected);assert not np.any(near[:,:,3][walk]);assert near[:,:,3].max()<=69
 layers=dict(static,**{'02_nuages_lointains':Image.fromarray(far),'07_nuages_overlay':Image.fromarray(near)});out=Image.new('RGBA',(W,H))
 for n in order:out.alpha_composite(layers[n])
 assert np.all(np.array(out)[:,:,3]==255)
 if k%40==0:assert np.array_equal(np.array(out),a(P/f'horn_composition_cle_{k:03}.png'))
assert np.array_equal(np.roll(a(P/'horn_02_nuages_lointains_323.png'),2,axis=1),back)
assert np.array_equal(np.roll(front,4*324,axis=1),front)
with zipfile.ZipFile(P/'mont_horn_panorama.ora') as z:
 out=Image.new('RGBA',(W,H))
 for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack')):out.alpha_composite(im(io.BytesIO(z.read(l.get('src')))))
 assert np.array_equal(np.array(out),a(P/'COMPOSITION.png'))
webp=Image.open(P/'ANIMATION_WRAP.webp');assert webp.n_frames==324
for p in P.glob('*.png'):assert Image.open(p).size==(W,H)
print('PASS: 324 aligned cloud phases; exact modulo wrapping at both velocities; overlay absent over approach; opaque composites; PNG keys and ORA exact; WebP324frames. Not a PMDO/collision test.')

assert np.all(a(P/'horn_01a_ciel.png')[:,:,3]==255)
assert not np.any(a(P/'horn_01b_montagnes_lointaines.png')[245:,:,3])
assert not np.any(a(P/'horn_06b_brume_altitude_pied_masque.png')[:,:,3][walk])
old=R/'renders/mont_horn_panorama_v1/mont_horn'
for n in ['03_falaises_gauches','04_falaises_droites','05_chemin_pierre_grise','06_entree_nord_et_marches']:
 assert np.array_equal(a(P/f'horn_{n}.png'),a(old/f'horn_{n}.png'))
fog=a(P/'horn_06b_brume_altitude_pied_masque.png')[:,:,3]
assert np.all(fog[450:,:202]==255) and np.all(fog[450:,446:]==255)
print('PASS V2: opaque separate sky, transparent distant mountains only above245px, original foreground unchanged, base hidden under opaque altitude haze, approach unaffected.')
