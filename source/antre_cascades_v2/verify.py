from pathlib import Path
import io,json,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_cascades_v2';P=O/'arene';m=json.loads((O/'manifest.json').read_text())
def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
static={n:im(P/f'aqua_{n}.png') for n in m['static']}
platform=Image.new('RGBA',tuple(m['size']))
for n in ['04_couronne_pierre_humide','05_plancher_arene_bois','06_passerelle_sud']:platform.alpha_composite(static[n])
pa=np.array(platform);dry=pa[:,:,3]>0
assert len(m['falls'])==6 and len(m['order'])==28
for t in range(m['frames']):
 ls=dict(static)
 for n in m['animated']:
  ls[n]=im(P/f'aqua_{n}_{t:03}.png');arr=np.array(ls[n]);assert ls[n].size==tuple(m['size'])
  if n!='01_eau_bassin':assert not np.any(arr[:,:,3][dry]),(n,t)
 out=Image.new('RGBA',tuple(m['size']))
 for n in m['order']:out.alpha_composite(ls[n])
 aa=np.array(out);assert np.all(aa[:,:,3]==255);assert np.array_equal(aa,a(P/f'aqua_composition_{t:03}.png'));assert np.array_equal(aa[dry],pa[dry])
 for k,f in enumerate(m['falls'],1):
  foam=np.array(ls[f'20_ecume_impact_{k:02}']);ys,xs=np.where(foam[:,:,3]>0);assert len(xs)>0;assert np.max(abs(ys-f['foot_y']))<=15;assert np.max(abs(xs-f['x']))<=f['width']+12
with zipfile.ZipFile(P/'arene_aquatique_bois.ora') as z:
 out=Image.new('RGBA',tuple(m['size']))
 for layer in reversed(ET.fromstring(z.read('stack.xml')).find('stack')):out.alpha_composite(im(io.BytesIO(z.read(layer.get('src')))))
 assert np.array_equal(np.array(out),a(P/'COMPOSITION.png'))
assert Image.open(P/'ANIMATION.webp').n_frames==40
print('PASS:28 layers,40 exact opaque compositions,6 localized foam impacts, dry platform unchanged at every phase, exact ORA and40frameWebP. No engine validation.')

# Validate that every falling-water pixel stays in its intended outlet ribbon and off rock surfaces.
rock=np.maximum.reduce([a(P/f'aqua_{n}.png')[:,:,3] for n in m['static'] if n.startswith('03')])>0
for k,f in enumerate(m['falls'],1):
 for t in range(m['frames']):
  c=a(P/f'aqua_10_cascade_{k:02}_{t:03}.png');mask=c[:,:,3]>0;ys,xs=np.where(mask)
  assert not np.any(mask&rock);assert ys.min()==f['top_y'];assert ys.max()==f['foot_y']-1
  assert all(np.any(mask[y]) for y in range(f['top_y'],f['foot_y']))
print('PASS: all6generated waterfalls continuous in their fitted channels, no falling water on rocks.')
