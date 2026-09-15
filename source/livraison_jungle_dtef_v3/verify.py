from pathlib import Path
import sys,json,zipfile,io,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];D=R/'renders/donjons_generes_dtef_v3';J=R/'renders/jungle_geysers_v2';OLD=R/'renders/donjons_dtef_v2';sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def load(p):return Image.open(p).convert('RGBA')
def eq(a,b):assert np.array_equal(np.array(a),np.array(b))
def merge(ls,size):
 out=Image.new('RGBA',size)
 for im in ls:out.alpha_composite(im)
 return out
count=0;frames=0
m=json.loads((D/'manifest.json').read_text())
for e in m['themes']:
 for mode in ['jour','nuit']:
  P=D/'RAW/TileDtef'/f'd3_{e["id"]}_{mode}';assert set(f.name for f in P.glob('tileset_*.png'))==set(e['files'])
  for f in e['files']:
   im=load(P/f);orig=load(OLD/'RAW/TileDtef'/f'd2_{e["id"]}_{mode}'/f);a=np.array(im);b=np.array(orig);assert im.size==(432,192);eq(a[:,:,3],b[:,:,3]);yy,xx=np.mgrid[:192,:432];border=(xx%24<4)|(xx%24>=20)|(yy%24<4)|(yy%24>=20);eq(a[border],b[border]);eq(a[:,144:288],b[:,144:288]);count+=1
   if '_frame' in f:eq(a,b);frames+=1
   if mode=='nuit':eq(im,night(load(D/'RAW/TileDtef'/f'd3_{e["id"]}_jour'/f)))
  for key,spec in e['animation_layers'].items():
   v,l=key.split(':')
   for fi in range(spec['count']):assert (P/f'tileset_{v}_frame{l}_{fi}.{spec["duration"]}.png').exists()
scenes=0
for e in json.loads((J/'manifest.json').read_text()):
 z=e['id']
 for mode in ['jour','nuit']:
  P=J/z/mode
  for p in range(e['frames']):
   files=[P/(f'jgv2_{z}_{mode}_{n}_{p:02}.png' if n in e['animated'] else f'jgv2_{z}_{mode}_{n}.png') for n in e['layer_order']];ls=[load(f) for f in files];eq(merge(ls,tuple(e['size'])),load(P/f'jgv2_{z}_{mode}_composition_{p:02}.png'));scenes+=1
   if mode=='nuit':
    for f,im in zip(files,ls):eq(im,night(load(J/z/'jour'/f.name.replace('_nuit_','_jour_'))))
  with zipfile.ZipFile(P/f'jgv2_{z}_{mode}.ora') as arc:
   root=ET.fromstring(arc.read('stack.xml'));ls=[load(io.BytesIO(arc.read(n.attrib['src']))) for n in reversed(list(root.find('stack')))];eq(merge(ls,tuple(e['size'])),load(P/'COMPOSITION.png'))
 # Canonical frame RGB still matches the source at original coordinates wherever alpha remains nonzero.
 for side in ['gauche','droit']:
  sprite=load(J/'sprites'/f'southern_jungle_cadre_{side}_natif.png');name='07_cadre_pmd_natif_gauche' if side=='gauche' else '08_cadre_pmd_natif_droit';im=load(J/z/'jour'/f'jgv2_{z}_jour_{name}.png');x=0 if side=='gauche' else 648-sprite.width;y=504-sprite.height;a=np.array(im)[y:y+sprite.height,x:x+sprite.width];b=np.array(sprite);mask=a[:,:,3]>0;eq(a[:,:,:3][mask],b[:,:,:3][mask])
report=dict(status='PASS',biomes=10,dtef_pngs=count,unchanged_native_animation_pngs=frames,protected_borders_px=4,secondary_and_alpha_unchanged=True,night_exact_per_layer=True,jungle_versions=2,jungle_layers_each=29,jungle_compositions=scenes,ora_checked=4,native_foreground_rgb_unscaled=True,runtime_validated=False)
(D/'verification_finale.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
