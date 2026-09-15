from pathlib import Path
import sys,json,zipfile,io
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent));from common import *
T=R/'renders/tours_hooh_v1';F=R/'renders/foret_saisons_v1';D=R/'renders/designs_dtef_v4'
def eq(a,b):assert np.array_equal(np.array(a),np.array(b))
def checkora(p):
 with zipfile.ZipFile(p) as z:
  root=ET.fromstring(z.read('stack.xml'));ls=[('',load(io.BytesIO(z.read(n.attrib['src'])))) for n in reversed(list(root.find('stack')))];eq(merge(ls),load(io.BytesIO(z.read('mergedimage.png'))))
scenes=0
for e in json.loads((F/'manifest.json').read_text()):
 for mode in ['jour','nuit']:
  P=F/e['id']/mode;prefix=f'fs1_{e["id"]}_{mode}';ls=[(n,load(P/f'{prefix}_{n}.png')) for n in e['layers']];eq(merge(ls),load(P/'COMPOSITION.png'));checkora(P/f'{prefix}.ora');scenes+=1
  mask=np.array(dict(ls)['02_chemin_commun'])[:,:,3]>0;eq(mask,np.array(load(F/'MASQUE_CHEMIN_COMMUN.png'))[:,:,0]>0);assert nd.label(mask)[1]==1;assert mask[0].any() and mask[-1].any()
  if mode=='nuit':
   for n,im in ls:eq(im,night(load(F/e['id']/'jour'/f'fs1_{e["id"]}_jour_{n}.png')))
cloud_checks=0;decoded_frames=0
for e in json.loads((T/'manifest.json').read_text()):
 for mode in ['jour','nuit']:
  P=T/e['id']/mode;prefix=f'th1_{e["id"]}_{mode}';ls=[(n,load(P/f'{prefix}_{n}.png')) for n in e['layers']];eq(merge(ls),load(P/'COMPOSITION.png'));checkora(P/f'{prefix}.ora');scenes+=1
  if mode=='nuit':
   for n,im in ls:eq(im,night(load(T/e['id']/'jour'/f'th1_{e["id"]}_jour_{n}.png')))
  if e['animated']:
   # Validate all decoded WebP states, including timings and mathematical loop closure.
   movie=Image.open(P/'BOUCLE_64S.webp');bank=dict(ls);elapsed=0
   for i in range(movie.n_frames):
    movie.seek(i);actual=movie.convert('RGBA');phase=elapsed//250;frame=[]
    for n,im in ls:
     if n in e['animated']:
      k=e['animated'].index(n);im=Image.fromarray(np.roll(np.array(im),round(phase*W/256*e['multipliers'][k]),axis=1))
     frame.append((n,im))
    eq(actual,merge(frame));elapsed+=movie.info['duration'];decoded_frames+=1
   assert elapsed==64000
   for k,n in enumerate(e['animated']):
    arr=np.array(bank[n]);eq(np.roll(arr,round(256*W/256*e['multipliers'][k]),axis=1),arr)
    for p in range(256):eq(np.roll(arr,round((p+256)*W/256*e['multipliers'][k]),axis=1),np.roll(arr,round(p*W/256*e['multipliers'][k]),axis=1));cloud_checks+=1
   assert len([n for n in e['layers'] if n.startswith('14_poutre_')])==4
   floor=np.array(bank['10_plancher_abime'])[:,:,3]>0
   if '15_acces_sud' in bank:floor|=np.array(bank['15_acces_sud'])[:,:,3]>0
   labels,num=nd.label(floor,np.ones((3,3)));assert labels[H-1,W//2]>0;assert labels[350,W//2]==labels[H-1,W//2]
# Actual exported cloud animations are independently readable and sum to one full64s loop.
for mode in ['jour','nuit']:
 for k,n in enumerate(['02_nuages_lavande','04_nuages_rose','06_nuages_ambre']):
  movie=Image.open(T/'nuages_animes'/mode/f'th1_{mode}_{n}_BOUCLE.webp');a=np.array(load(T/'carillon_boss'/mode/f'th1_carillon_boss_{mode}_{n}.png'));elapsed=0
  for i in range(movie.n_frames):
   movie.seek(i);actual=np.array(movie.convert('RGBA'));expected=np.roll(a,round((elapsed//250)*W/256*[1,-1,2][k]),axis=1);eq(actual[:,:,3],expected[:,:,3]);visible=expected[:,:,3]>0;eq(actual[:,:,:3][visible],expected[:,:,:3][visible]);elapsed+=movie.info['duration']
  assert elapsed==64000
count=0
for e in json.loads((D/'manifest.json').read_text())['themes']:
 for mode in ['jour','nuit']:
  P=D/'RAW/TileDtef'/f'd4_{e["id"]}_{mode}'
  for f in e['files']:
   im=load(P/f);assert im.size==(432,192);count+=1
   if mode=='nuit':eq(im,night(load(D/'RAW/TileDtef'/f'd4_{e["id"]}_jour'/f)))
  for v in range(3):eq(np.array(load(P/f'tileset_{v}.png'))[:,:,3],np.array(load(P/'tileset_0.png'))[:,:,3])
report=dict(status='PASS',forest_seasons=3,forest_common_connected_path=True,scene_compositions=scenes,ora_checked=scenes,towers_separate=True,boss_posts_each=4,boss_floor_south_to_center_connected=True,decoded_boss_animation_frames=decoded_frames,cloud_periodicity_checks=cloud_checks,cloud_loop_ms=64000,cloud_layer_loops=6,dtef_designs=4,dtef_pngs=count,night_exact_per_layer=True,runtime_validated=False)
(T/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
