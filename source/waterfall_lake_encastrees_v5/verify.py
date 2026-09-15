from pathlib import Path
import sys,json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_encastrees_v5';OLD=R/'renders/waterfall_lake_demi_cercle_v4';m=json.loads((O/'manifest.json').read_text());old=json.loads((OLD/'manifest.json').read_text());sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def load(p):return Image.open(p).convert('RGBA')
def eq(a,b):assert np.array_equal(np.array(a),np.array(b))
def merge(ls):
 out=Image.new('RGBA',(504,360))
 for im in ls:out.alpha_composite(im)
 return out
mask=np.array(load(O/'MASQUE_RETOUCHE.png'))[:,:,0]>0
unchanged=[n for n in old['layer_order'] if not n.startswith('07_cascade_')]
for mode in ['jour','nuit']:
 P=O/mode
 for p in range(24):
  def path(base,prefix,n):return base/mode/(f'{prefix}_{mode}_{n}_{p:02}.png' if n in m['animated'] else f'{prefix}_{mode}_{n}.png')
  ls=[load(path(O,'lake5',n)) for n in m['layer_order']];comp=load(P/f'lake5_{mode}_composition_{p:02}.png');eq(merge(ls),comp)
  eq(np.array(comp)[~mask],np.array(load(OLD/mode/f'lake4_{mode}_composition_{p:02}.png'))[~mask])
  for n in unchanged:eq(load(path(O,'lake5',n)),load(path(OLD,'lake4',n)))
  for k in range(1,4):
   fall=np.array(load(path(O,'lake5',f'07_cascade_{k}')))[:,:,3]>0;foam=np.array(load(path(O,'lake5',f'08_ecume_metano_{k}')))[:,:,3]>0
   assert nd.label(fall,np.ones((3,3)))[1]==1;assert (fall&foam).any()
   if p>=4:eq(load(path(O,'lake5',f'07_cascade_{k}')),load(P/f'lake5_{mode}_07_cascade_{k}_{p%4:02}.png'))
  if mode=='nuit':eq(comp,night(load(O/f'jour/lake5_jour_composition_{p:02}.png')))
 with zipfile.ZipFile(P/f'lake5_{mode}.ora') as z:
  nodes=list(ET.fromstring(z.read('stack.xml')).find('stack'));eq(merge([Image.open(io.BytesIO(z.read(n.attrib['src']))).convert('RGBA') for n in reversed(nodes)]),load(P/'COMPOSITION.png'))
report=dict(status='PASS',layers=31,compositions_checked=48,unchanged_V4_layers=len(unchanged),outside_three_original_waterfall_masks_identical_all_frames=True,foam_identical=True,cliff_layers_identical=True,water_four_phases=True,falls_connected_and_attached=True,night_exact=True,ora_checked=2,runtime_validated=False)
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
