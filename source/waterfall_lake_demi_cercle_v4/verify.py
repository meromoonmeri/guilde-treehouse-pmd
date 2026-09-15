from pathlib import Path
import sys,json,zipfile,io,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_demi_cercle_v4';OLD=R/'renders/waterfall_lake_trois_v2';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def load(p):return Image.open(p).convert('RGBA')
def ar(p):return np.array(load(p))
def eq(a,b):assert np.array_equal(np.array(a),np.array(b))
def merge(ls,size=(504,360)):
 out=Image.new('RGBA',size)
 for im in ls:out.alpha_composite(im)
 return out
orig=list((O/'origine_decomposee').glob('origine_*.png'));eq(merge([load(p) for p in orig],(456,312)),load(R/m['source']))
assert np.all(sum(ar(p)[:,:,3]>0 for p in orig)==1)
for mode in ['jour','nuit']:
 P=O/mode
 for p in range(24):
  ls=[load(P/(f'lake4_{mode}_{n}_{p:02}.png' if n in m['animated'] else f'lake4_{mode}_{n}.png')) for n in m['layer_order']];comp=load(P/f'lake4_{mode}_composition_{p:02}.png');eq(merge(ls),comp)
  # Approved southern approach and central platform region strictly preserved in all48scenes.
  eq(np.array(comp)[180:],ar(OLD/f'{mode}/lake2_{mode}_composition_{p:02}.png')[180:])
  if mode=='nuit':eq(comp,night(load(O/f'jour/lake4_jour_composition_{p:02}.png')))
  for k,c in enumerate(m['channels']):
   x,y=c['foot'];ref=load(R/f'source/antre_harmonie_v3/references/ecume_native_{p%3}.png');expected=Image.new('RGBA',(504,360));expected.alpha_composite(ref,(x-48,y-14))
   if mode=='nuit':expected=night(expected)
   eq(load(P/f'lake4_{mode}_08_ecume_metano_{k+1}_{p:02}.png'),expected)
   fall=ar(P/f'lake4_{mode}_07_cascade_{k+1}_{p:02}.png')[:,:,3]>0;foam=np.array(expected)[:,:,3]>0
   assert np.any(fall&foam);assert nd.label(fall,np.ones((3,3)))[1]==1
 with zipfile.ZipFile(P/f'lake4_{mode}.ora') as z:
  nodes=list(ET.fromstring(z.read('stack.xml')).find('stack'));eq(merge([Image.open(io.BytesIO(z.read(n.attrib['src']))).convert('RGBA') for n in reversed(nodes)]),load(P/'COMPOSITION.png'))
report=dict(status='PASS',original_layers=9,original_recomposition_exact=True,new_layers=len(m['layer_order']),compositions_checked=48,ora_checked=2,south_y180_plus_identical_to_approved_V2_all_frames=True,foam_exact_native_pixels_all_phases=True,three_connected_falls_attached_to_foam=True,night_exact=True,runtime_validated=False)
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
