from pathlib import Path
import sys,json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_10_biomes_v1';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
T=24;NN=Image.Resampling.NEAREST
BIOMES=['foret','jungle','marais','roche','cristal','glace','volcan','desert','ruines','vapeur']
COLORS=[(40,117,161),(23,125,132),(78,110,63),(33,101,146),(108,67,179),(77,159,203),(213,68,23),(170,135,70),(42,135,130),(64,157,180)]
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def merge(ls,size):
 im=Image.new('RGBA',size)
 for n,l in ls:im.alpha_composite(l)
 return im
def ora(path,ls,size):
 root=ET.Element('image',w=str(size[0]),h=str(size[1]));stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(n,l) in reversed(list(enumerate(ls))):
   src=f'data/{i}.png';z.writestr(src,png(l));ET.SubElement(stack,'layer',name=n,src=src,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(merge(ls,size)))
def canonical(m):
 for diag,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(m&a and m&b):m&=~diag
 return m
MASKS=sorted(set(canonical(m) for m in range(256)));assert len(MASKS)==47

def shape(m,variant=0):
 a=np.ones((24,24),bool);yy,xx=np.mgrid[:24,:24]
 for horizontal,vertical,diag,qx,qy in [(8,1,128,0,0),(2,1,16,1,0),(8,4,64,0,1),(2,4,32,1,1)]:
  u=xx if qx==0 else 23-xx;v=yy if qy==0 else 23-yy;q=(u<12)&(v<12);h=bool(m&horizontal);vside=bool(m&vertical)
  if h and vside:inside=((u*u+v*v)>=(2+variant)**2) if not m&diag else np.ones_like(a)
  elif not h and not vside:inside=((u-12)**2+(v-12)**2<=(11-variant)**2)
  elif not h:inside=u>=2+variant
  else:inside=v>=2+variant
  a[q]=inside[q]
 return a

def neighbors(grid,y,x):
 h,w=grid.shape;m=0
 for bit,dy,dx in [(1,-1,0),(2,0,1),(4,1,0),(8,0,-1),(16,-1,1),(32,1,1),(64,1,-1),(128,-1,-1)]:
  iy,ix=y+dy,x+dx
  if (0<=iy<h and 0<=ix<w and grid[iy,ix]) or not(0<=iy<h and 0<=ix<w):m|=bit
 return canonical(m)

def vent(size=48):
 im=Image.new('RGBA',(size,size));d=ImageDraw.Draw(im);cx=size//2;cy=size*2//3
 d.ellipse((4,cy-8,size-4,cy+10),fill=(88,65,45,255));d.ellipse((6,cy-10,size-6,cy+6),fill=(147,118,84,255));d.ellipse((13,cy-5,size-13,cy+2),fill=(42,47,45,255))
 for i in range(7):
  x=int(cx+17*np.cos(i*2*np.pi/7));y=int(cy+7*np.sin(i*2*np.pi/7));d.rectangle((x-3,y-2,x+3,y+1),fill=(180,153,111,255))
 return im

def materials(name):
 if name=='vapeur':
  src=Image.open(R/'Steam_Cave_Peak_TDS.png').convert('RGBA');return [src.crop((280,360,376,456)),src.crop((16,128,112,224)),src.crop((32,256,128,352))],vent()
 im=Image.open(O/f'bruts/{name}.png').convert('RGBA');w,h=im.size
 mats=[im.crop(box).resize((96,96),NN) for box in [(0,0,w//2,h//2),(w//2,0,w,h//2),(0,h//2,w//2,h)]]
 deco=key(im.crop((w//2,h//2,w,h)));bbox=deco.getbbox();deco=deco.crop(bbox);deco.thumbnail((44,44),NN);p=Image.new('RGBA',(48,48));p.alpha_composite(deco,((48-deco.width)//2,48-deco.height));return mats,p

def sheet(tiles,cols=8,size=24):
 out=Image.new('RGBA',(cols*size,((len(tiles)+cols-1)//cols)*size))
 for i,im in enumerate(tiles):out.alpha_composite(im,((i%cols)*size,(i//cols)*size))
 return out

def patch(im,x,y):
 a=np.array(im);ys=(np.arange(24)+y)%96;xs=(np.arange(24)+x)%96;return Image.fromarray(a[ys[:,None],xs[None,:]])

# Four connected rooms + two-tile corridors. Same test layout for honest biome comparison.
walk=np.zeros((18,24),bool)
for x1,y1,x2,y2 in [(2,2,10,7),(14,2,22,8),(3,11,11,16),(15,11,22,16)]:walk[y1:y2,x1:x2]=True
walk[4:6,8:17]=True;walk[4:14,6:8]=True;walk[12:14,6:19]=True;walk[5:14,18:20]=True;walk[13:18,11:13]=True;walk[13:15,7:17]=True
walls=~walk;liquid=np.zeros_like(walk);liquid[3:5,3:5]=True;liquid[12:14,16:18]=True
assert nd.label(walk&~liquid)[1]==1
catalog=[]
for bi,name in enumerate(BIOMES):
 P=O/name;P.mkdir(exist_ok=True);mats,deco=materials(name)
 for n,im in zip(['sol','sommet','face'],mats):im.save(P/f'd10_{name}_matiere_{n}.png')
 floors=[patch(mats[0],(i%4)*24,(i//4)*24) for i in range(12)]
 walltiles=[]
 for variant in range(2):
  for m in MASKS:
   a=np.array(patch(mats[1],variant*24,24));mask=shape(m,variant)
   if not m&4:a[15:]=np.array(patch(mats[2],variant*24,0))[15:]
   a[~mask]=0;walltiles.append(Image.fromarray(a))
 liquidsets=[]
 for phase in range(4):
  yy,xx=np.mgrid[:24,:24];base=np.array(COLORS[bi]);wave=np.sin((xx+phase*3)*2*np.pi/24+(yy-phase*2)*2*np.pi/12);rip=(wave>.86)&((yy+phase)%6<2)
  rgb=np.clip(base+np.rint(wave[:,:,None]*8)+rip[:,:,None]*np.array([28,42,40]),0,255).astype('uint8');tex=np.dstack([rgb,np.full((24,24),255,dtype='uint8')]);ts=[]
  for m in MASKS:
   a=tex.copy();mask=shape(m);edge=mask&~nd.binary_erosion(mask,border_value=1);a[edge,:3]=np.clip(base*.7,0,255);a[~mask]=0;ts.append(Image.fromarray(a))
  liquidsets.append(ts)
 frames={}
 for mode in ['jour','nuit']:
  D=P/mode;D.mkdir(exist_ok=True);transform=night if mode=='nuit' else lambda x:x
  for n,im in [('sols_12',sheet(floors)),('murs_47x2',sheet(walltiles)),('obstacles',sheet([deco,deco.transpose(Image.Transpose.FLIP_LEFT_RIGHT)],2,48))]:transform(im).save(D/f'd10_{name}_{mode}_{n}.png')
  for phase,ts in enumerate(liquidsets):transform(sheet(ts)).save(D/f'd10_{name}_{mode}_terrain_anime_{phase}.png')
  floor=Image.new('RGBA',(576,432));wl=Image.new('RGBA',floor.size);ob=Image.new('RGBA',floor.size)
  for y in range(18):
   for x in range(24):
    xy=(x*24,y*24);floor.alpha_composite(floors[(x+3*y)%12],xy)
    if walls[y,x]:wl.alpha_composite(walltiles[MASKS.index(neighbors(walls,y,x))],xy)
  for x,y in [(8,2),(20,6),(3,14),(20,14)]:ob.alpha_composite(deco,(x*24,y*24-24))
  frames[mode]=[]
  for phase in range(4):
   wat=Image.new('RGBA',floor.size)
   for y,x in zip(*np.where(liquid)):wat.alpha_composite(liquidsets[phase][MASKS.index(neighbors(liquid,y,x))],(x*24,y*24))
   ls=[(n,transform(im)) for n,im in [('01_sol',floor),('02_murs',wl),('03_terrain_anime',wat),('04_obstacles',ob)]]
   for n,im in ls:
    if phase==0 or n=='03_terrain_anime':im.save(D/(f'd10_{name}_{mode}_{n}_{phase}.png' if n=='03_terrain_anime' else f'd10_{name}_{mode}_{n}.png'))
   comp=merge(ls,floor.size);frames[mode].append(comp);comp.save(D/f'd10_{name}_{mode}_demo_{phase}.png')
   if phase==0:ora(D/f'd10_{name}_{mode}.ora',ls,floor.size)
  frames[mode][0].save(D/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=200,loop=0,lossless=True)
  frames[mode][0].save(D/'COMPOSITION.png')
 info=dict(biome=name,cell_px=24,import_tile_px=8,floors=12,wall_connectivity_cases=47,wall_styles=2,animated_terrain_cases=47,animated_phases=4,obstacle_variants=2,source='generated PMD-inspired material' if name!='vapeur' else 'native Steam Cave Peak screenshot crops; vent drawn separately',native_tileset=False,runtime_validated=False)
 (P/'manifest.json').write_text(json.dumps(info,indent=2));catalog.append(info)
 # Night equivalence tested for every exported PNG that has a day/night counterpart.
 for f in (P/'jour').glob('d10_*.png'):
  counterpart=P/'nuit'/f.name.replace('_jour_','_nuit_');assert np.array_equal(np.array(night(Image.open(f).convert('RGBA'))),np.array(Image.open(counterpart).convert('RGBA')))
(P.parent/'connectivite_47.json').write_text(json.dumps(dict(bits=dict(N=1,E=2,S=4,W=8,NE=16,SE=32,SW=64,NW=128),canonical_masks=MASKS,indexing='row-major8columns; wall style1 starts at index47; each24px cell is3x3 import tiles8px'),indent=2))
(O/'layout_demo.json').write_text(json.dumps(dict(walkable=walk.astype(int).tolist(),hazards=liquid.astype(int).tolist(),start=[12,17],room_centers=[[6,4],[18,4],[7,13],[19,13]],note='Proposed logical grid, not PMDO collision integration'),indent=2))
(O/'manifest.json').write_text(json.dumps(catalog,indent=2));print('Built ten biomes,47cases x2wall styles,day/night')
