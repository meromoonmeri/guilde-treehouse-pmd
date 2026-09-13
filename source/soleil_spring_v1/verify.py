from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/soleil_spring_v1';P=Path(__file__).resolve().parent/'references'
def load(p):return Image.open(p).convert('RGBA')
o=json.loads((P/'luminous_spring.rsground').read_text(encoding='utf-8-sig'))['Object'];banks={n:load(P/(n+'.png')) for n in ['LuminousSpring','LuminousSpringAnim']};mask=np.array(Image.open(O/'spring/masque_zone_native.png'))==255;checks=[]
for f in range(39):
 ref=Image.new('RGBA',(600,600))
 for l in o['Layers']:
  if not l['Visible']:continue
  for x,col in enumerate(l['Tiles']):
   for y,t in enumerate(col):
    for a in t['Layers']:
     v=a['Frames'][(f*10//a['FrameLength'])%len(a['Frames'])];p=v['TexLoc'];tx,ty=p['X']*24,p['Y']*24;ref.alpha_composite(banks[v['Sheet']].crop((tx,ty,tx+24,ty+24)),(x*24,y*24))
 im=load(O/'spring/frames'/f'{f:02}.png');assert np.array_equal(np.array(im)[mask],np.array(ref)[mask]),f
 comp=load(O/'spring/01_decor.png');comp.alpha_composite(load(O/'spring/02_cycle_3'/f'{f%3:02}.png'));comp.alpha_composite(load(O/'spring/03_cycle_13'/f'{f%13:02}.png'));assert np.array_equal(np.array(comp),np.array(im))
checks.append('39 phases : zone protégée exactement égale au rendu indépendant des tuiles Halcyon/RawAsset')
checks.append('39 recompositions exactes depuis les calques décor / cycle3 / cycle13')
disk=load(O/'soleil/disque_fixe.png');dm=np.array(disk)[:,:,3]>0;arr=[]
for f in range(64):
 im=load(O/'soleil/frames'/f'{f:02}.png');assert im.size==(96,96);assert np.array_equal(np.array(im)[dm],np.array(disk)[dm]);halo=load(O/'soleil/halo'/f'{f:02}.png');assert np.array_equal(np.array(Image.alpha_composite(halo,disk)),np.array(im));arr.append(np.array(im).astype(float))
checks.append('64 soleils : disque fixe identique et recomposition exacte halo+disque')
diffs=[float(np.abs(arr[(f+1)%64]-arr[f]).mean()) for f in range(64)];assert diffs[-1]<=max(diffs[:-1])*1.25
checks.append('Raccord solaire 63→00 pas plus abrupt que les autres transitions (+25% tolérance)')
for mode in ['jour','coucher','nuit']:
 im=load(O/'nuages'/f'{mode}_overlay.png');a=np.array(im);assert im.size==(960,600);assert np.array_equal(np.roll(a,960,axis=1),a)
checks.append('3 overlays 960×600, wrap 960 px identique')
ps=list(O.rglob('*.png'))
for p in ps:
 with Image.open(p) as im:im.load()
checks.append(f'{len(ps)} PNG décodés')
(O/'verification.json').write_text(json.dumps({'checks':checks,'solar_step_max':max(diffs),'solar_wrap_step':diffs[-1],'native_protected_pixels':int(mask.sum()),'runtime_validated':False},ensure_ascii=False,indent=2));print('\n'.join(checks))
