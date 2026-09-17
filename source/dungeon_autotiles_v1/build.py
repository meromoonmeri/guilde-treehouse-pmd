from pathlib import Path
import json,re,colorsys,math,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/dungeon_autotiles_v1';ref=json.loads((O/'reference_manifest.json').read_text());mapping=ref['mapping'];slot_of={m:i for i,m in enumerate(mapping) if m>=0}
THEMES=[('foret_mousse','Forêt mousse','apple_woods',False),('aquatique_lagon','Lagon turquoise','beach_cave',False),('sakura_printemps','Sakura printemps','apple_woods',False),('foret_lucioles','Forêt aux lucioles','apple_woods',True),('aquatique_corail','Récif corallien','beach_cave',True),('sakura_lunaire','Sakura lunaire','apple_woods',True)]
def load(p):return Image.open(p).convert('RGBA')
def grade(im,theme):
 a=np.array(im);rgb=a[:,:,:3];colors,inverse=np.unique(rgb.reshape(-1,3),axis=0,return_inverse=True);new=[]
 for r,g,b in colors:
  h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255);water=b>r*1.06 and b>g*.9;green=g>r*1.03 and g>b*1.08
  if theme=='foret_mousse':h=(h+.025)%1;s*=.85;v*=.93
  elif theme=='aquatique_lagon':
   if water:h=.48;s*=.8;v=min(1,v*1.06)
   else:h=(h+.012)%1;s*=.78;v=min(1,v*1.04)
  elif theme.startswith('sakura'):
   if water:h=.66 if theme=='sakura_lunaire' else .61;s*=.68
   elif green:h=.94;s*=.54;v=min(1,v*1.1)
   else:h=.77 if theme=='sakura_lunaire' else .94;s*=.25;v*=.86 if theme=='sakura_lunaire' else 1
  elif theme=='foret_lucioles':
   if green:h=.39;s*=.75;v*=.64
   elif water:h=.48;s*=.8;v*=.7
   else:h=.34;s*=.52;v*=.64
  elif theme=='aquatique_corail':
   if water:h=.48;s*=.8
   else:h=.79;s*=.38;v=min(1,v*1.05)
  new.append(tuple(round(c*255) for c in colorsys.hsv_to_rgb(h,min(1,s),min(1,v))))
 a[:,:,:3]=np.array(new,dtype='uint8')[inverse].reshape(rgb.shape);return Image.fromarray(a)
# Generated material is injected only into opaque STATIC tile interiors.
# Four-pixel perimeter and all animated overlays retain globally consistent recoloring.
yy,xx=np.mgrid[:24,:24];weight=np.clip(np.minimum.reduce([xx-3,yy-3,20-xx,20-yy])/5,0,1)*.48
manifest={'tile_size':24,'layout':'6x8 par type, Wall/Secondary/Floor,47 cas +1 vide','runtime_validated':False,'themes':[]}
for name,title,source,original in THEMES:
 src=O/'references_dtef'/source;out=O/'dtef'/name;out.mkdir(parents=True,exist_ok=True);
 for old in out.glob('tileset_*.png'):old.unlink()
 samples=[]
 if original:
  gen=load(O/'generation'/(name+'.png'));cw=gen.width//3
  for typ in range(3):
   x=typ*cw+cw//2;y=gen.height//2;crop=gen.crop((x-72,y-72,x+72,y+72)).resize((24,24),Image.Resampling.NEAREST).quantize(colors=24).convert('RGBA');samples.append(np.array(crop)[:,:,:3]);crop.save(out/f'materiau_{typ}.png')
 sheets={};source_info=ref['sources'][source];border_checks=0
 for filename in source_info['files']:
  raw=load(src/filename);changed=grade(raw,name);a=np.array(changed);graded=a.copy()
  if original and '_frame' not in filename:
   for typ in [0,2]:
    for slot,m in enumerate(mapping):
     if m<0:continue
     x=(typ*6+slot%6)*24;y=slot//6*24;cell=a[y:y+24,x:x+24];mask=(cell[:,:,3]==255)*weight
     cell[:,:,:3]=np.rint(cell[:,:,:3]*(1-mask[:,:,None])+samples[typ]*mask[:,:,None]).astype('uint8')
  assert np.array_equal(a[:,:,3],np.array(raw)[:,:,3])
  # Template gasket (including empty slot) cannot drift with a generated sample.
  gy,gx=np.mgrid[:192,:432];border=(gx%24<4)|(gx%24>=20)|(gy%24<4)|(gy%24>=20);assert np.array_equal(a[border],graded[border]);border_checks+=1
  for typ in range(3):assert np.max(a[48:72,(typ*6+5)*24:(typ*6+6)*24,3])==0
  a[a[:,:,3]==0]=0;im=Image.fromarray(a);im.save(out/filename);sheets[filename]=im
 # All source frames, variants and independent per-layer timings remain unchanged.
 entry={'id':name,'title':title,'source':source,'kind':'matière générée sur géométrie native' if original else 'variante chromatique native','animation_layers':source_info['animation_layers'],'files':source_info['files'],'checks':{'alpha_preserved':True,'four_pixel_gaskets_preserved_after_grade':True,'all_source_frames_and_durations_preserved':True,'checked_sheets':border_checks}}
 entry['cycle_game_frames']=math.lcm(*[spec['count']*spec['duration'] for spec in source_info['animation_layers'].values()])
 # Layout stress scene rendered by the same adjacency bit convention as AutoTileAdjacent.
 grid=np.zeros((18,24),dtype='uint8');grid[2:8,2:10]=2;grid[2:8,13:22]=2;grid[11:16,4:20]=2;grid[4:6,8:15]=2;grid[6:14,6:8]=2;grid[6:14,17:19]=2;grid[3:6,3:6]=1;grid[4:7,5:8]=1;grid[12:15,11:17]=1;grid[10:13,12:14]=1
 def code(x,y,t):
  def q(dx,dy):
   nx=x+dx;ny=y+dy;return not(0<=nx<24 and 0<=ny<18) or grid[ny,nx]==t
  dirs=[(0,1),(-1,0),(0,-1),(1,0)];bits=[q(*d) for d in dirs];v=sum((1<<i) for i,b in enumerate(bits) if b)
  for i,diag in enumerate([(-1,1),(-1,-1),(1,-1),(1,1)]):
   if bits[i] and bits[(i+1)%4] and q(*diag):v|=1<<(i+4)
  assert v in slot_of;return v
 def render(frame):
  o=Image.new('RGBA',(576,432))
  for y in range(18):
   for x in range(24):
    typ=int(grid[y,x]);mask=code(x,y,typ) if typ!=2 else 255;slot=slot_of[mask];sx=(typ*6+slot%6)*24;sy=slot//6*24;box=(sx,sy,sx+24,sy+24)
    choices=[vi for vi in range(3) if sheets[f'tileset_{vi}.png'].crop(box).getbbox()];vi=choices[(x*13+y*7)%len(choices)] if choices else 0;o.alpha_composite(sheets[f'tileset_{vi}.png'].crop(box),(x*24,y*24))
    for key,spec in source_info['animation_layers'].items():
     var,layer=map(int,key.split(':'))
     if var!=vi:continue
     fi=frame//spec['duration']%spec['count'];fn=f'tileset_{var}_frame{layer}_{fi}.{spec["duration"]}.png';o.alpha_composite(sheets[fn].crop(box),(x*24,y*24))
  return o
 entry['demo_tiles']=[]
 for y in range(18):
  for x in range(24):
   typ=int(grid[y,x]);mask=code(x,y,typ) if typ!=2 else 255;slot=slot_of[mask];sx=(typ*6+slot%6)*24;sy=slot//6*24;box=(sx,sy,sx+24,sy+24)
   choices=[vi for vi in range(3) if sheets[f'tileset_{vi}.png'].crop(box).getbbox()];vi=choices[(x*13+y*7)%len(choices)] if choices else 0
   entry['demo_tiles'].append([x*24,y*24,sx,sy,vi])
 preview=O/'apercus'/name;preview.mkdir(parents=True,exist_ok=True);render(0).save(preview/'scene.png')
 # Short preview only, browser animates all independent source frames on full DTEF sheet.
 frames=[render(t) for t in range(0,120,6)];frames[0].save(preview/'extrait.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=True)
 composed=sheets['tileset_0.png'].copy()
 for key,spec in source_info['animation_layers'].items():
  var,layer=map(int,key.split(':'))
  if var==0:composed.alpha_composite(sheets[f'tileset_{var}_frame{layer}_0.{spec["duration"]}.png'])
 composed.save(preview/'planche.png');entry['preview_timing_note']='Extrait2s, pas la boucle complète ; le navigateur conserve les cadences indépendantes sur la planche.';manifest['themes'].append(entry)
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('6 DTEF prototypes;204 sheets; complete native animation stacks preserved')
