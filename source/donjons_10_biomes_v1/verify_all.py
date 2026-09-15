from pathlib import Path
import sys,json,zipfile,io,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
O=R/'renders/donjons_10_biomes_v1'
def load(p):return Image.open(p).convert('RGBA')
def eq(a,b):assert np.array_equal(np.array(a),np.array(b))
def merge(ls,size):
 im=Image.new('RGBA',size)
 for l in ls:im.alpha_composite(l)
 return im
def checkora(p):
 with zipfile.ZipFile(p) as z:
  root=ET.fromstring(z.read('stack.xml'));nodes=list(root.find('stack'));size=(int(root.attrib['w']),int(root.attrib['h']));ims=[load(io.BytesIO(z.read(n.attrib['src']))) for n in reversed(nodes)];eq(merge(ims,size),load(io.BytesIO(z.read('mergedimage.png'))))
count=0
for info in json.loads((O/'manifest.json').read_text()):
 P=O/info['biome'];name=info['biome']
 for mode in ['jour','nuit']:
  D=P/mode
  for p in range(4):
   ims=[load(D/f'd10_{name}_{mode}_{n}.png') for n in ['01_sol','02_murs']]+[load(D/f'd10_{name}_{mode}_03_terrain_anime_{p}.png'),load(D/f'd10_{name}_{mode}_04_obstacles.png')];eq(merge(ims,(576,432)),load(D/f'd10_{name}_{mode}_demo_{p}.png'));count+=1
  checkora(D/f'd10_{name}_{mode}.ora')
  for file in D.glob('d10_*.png'):
   im=load(file);assert im.width%8==im.height%8==0
  sheet=load(D/f'd10_{name}_{mode}_murs_47x2.png')
  for i in range(94):assert sheet.crop(((i%8)*24,(i//8)*24,(i%8+1)*24,(i//8+1)*24)).getbbox()
 for f in (P/'jour').glob('d10_*.png'):eq(night(load(f)),load(P/'nuit'/f.name.replace('_jour_','_nuit_')))
layout=json.loads((O/'layout_demo.json').read_text());walk=np.array(layout['walkable'],bool)&~np.array(layout['hazards'],bool);assert nd.label(walk)[1]==1
# Local generator repair.
V=R/'renders/waterfall_lake_generateur_v6';OLD=R/'renders/waterfall_lake_encastrees_v5';m=json.loads((V/'manifest.json').read_text());om=json.loads((OLD/'manifest.json').read_text());mask=np.array(load(V/'MASQUE_RETOUCHE.png'))[:,:,0]>0
preserved=[n for n in om['layer_order'] if n not in ['07_cascade_1','07_cascade_3','07b_levres_rocheuses','07c_ombres_encastrement']]
for mode in ['jour','nuit']:
 for p in range(24):
  def path(root,prefix,n):return root/mode/(f'{prefix}_{mode}_{n}_{p:02}.png' if n in m['animated'] else f'{prefix}_{mode}_{n}.png')
  comp=load(V/mode/f'lake6_{mode}_composition_{p:02}.png');eq(merge([load(path(V,'lake6',n)) for n in m['layer_order']],(504,360)),comp);eq(np.array(comp)[~mask],np.array(load(OLD/mode/f'lake5_{mode}_composition_{p:02}.png'))[~mask])
  for n in preserved:eq(load(path(V,'lake6',n)),load(path(OLD,'lake5',n)))
  for k in [1,3]:
   fall=np.array(load(path(V,'lake6',f'07_cascade_{k}')))[:,:,3]>0;foam=np.array(load(path(V,'lake6',f'08_ecume_metano_{k}')))[:,:,3]>0;assert nd.label(fall,np.ones((3,3)))[1]==1;assert (fall&foam).any()
  if mode=='nuit':eq(comp,night(load(V/'jour'/f'lake6_jour_composition_{p:02}.png')))
 checkora(V/mode/f'lake6_{mode}.ora')
# Steam original background exact, layers recompose, night exact per layer (translucent vapor).
S=R/'renders/steam_cave_geysers_v1';m=json.loads((S/'manifest.json').read_text())
eq(merge([load(S/'jour'/f'steam1_jour_{n}.png') for n in ['01_sol_original','02_parois_originales']],(648,624)),load(R/m['source']))
for mode in ['jour','nuit']:
 for p in range(12):
  ims=[load(S/mode/(f'steam1_{mode}_{n}_{p:02}.png' if n in m['animated'] else f'steam1_{mode}_{n}.png')) for n in m['layer_order']];eq(merge(ims,(648,624)),load(S/mode/f'steam1_{mode}_composition_{p:02}.png'))
 checkora(S/mode/f'steam1_{mode}.ora')
for f in (S/'jour').glob('steam1_jour_*.png'):
 if 'composition' not in f.name:eq(night(load(f)),load(S/'nuit'/f.name.replace('_jour_','_nuit_')))
# Check both wall styles against an independent random neighborhood grid, including all47cases.
rng=np.random.default_rng(947);grid=rng.random((80,80))<.6;ms=json.loads((O/'connectivite_47.json').read_text())['canonical_masks'];seen=set()
def mid(y,x):
 m=0
 for bit,dy,dx in [(1,-1,0),(2,0,1),(4,1,0),(8,0,-1),(16,-1,1),(32,1,1),(64,1,-1),(128,-1,-1)]:
  iy,ix=y+dy,x+dx
  if not(0<=iy<80 and 0<=ix<80) or grid[iy,ix]:m|=bit
 for bit,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(m&a and m&b):m&=~bit
 seen.add(m);return ms.index(m)
for info in json.loads((O/'manifest.json').read_text()):
 name=info['biome'];a=np.array(load(O/name/'jour'/f'd10_{name}_jour_murs_47x2.png'))[:,:,3]>0
 for style in range(2):
  tiles=[a[(i//8)*24:(i//8+1)*24,(i%8)*24:(i%8+1)*24] for i in range(style*47,(style+1)*47)]
  for y,x in zip(*np.where(grid)):
   t=tiles[mid(y,x)]
   if x<79 and grid[y,x+1]:eq(t[:,-1],tiles[mid(y,x+1)][:,0])
   if y<79 and grid[y+1,x]:eq(t[-1],tiles[mid(y+1,x)][0])
assert seen==set(ms)
report=dict(status='PASS',biomes=10,biome_compositions=80,wall_cases_per_biome=47,wall_styles=2,wall_shared_alpha_edges_verified_all47cases_both_styles=True,biome_ora=20,walkable_demo_connected=True,waterfall_compositions=48,waterfall_unchanged_layers=len(preserved),waterfall_outside_repair_identical=True,steam_compositions=24,steam_background_exact=True,night_filter_exact_per_layer=True,runtime_validated=False)
(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
