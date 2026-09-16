"""Deterministic layered VFX prototype. No fabricated PMDO binary/API."""
from pathlib import Path
import math, colorsys, json, random, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]; SRC=Path(__file__).parent
OUT=ROOT/'renders/mega_evolution_v1'; OUT.mkdir(parents=True,exist_ok=True)
N=144; W=256; H=256; ground=(128,194); rng=random.Random(564)
def rainbow(h,a=255): return tuple(round(c*255) for c in colorsys.hsv_to_rgb(h%1,.55,1))+(int(a),)
def blank(): return Image.new('RGBA',(W,H))
# Position each frame by its own native white ground marker, not bounding-box bottom.
characters=[]; bounds=[]
for name in ['charizard','mega_charizard_x']:
 p=SRC/'references'/name
 node=next(a for a in ET.parse(p/'AnimData.xml').findall('.//Anim') if a.findtext('Name')=='Idle')
 w,h=int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'))
 sheet=Image.open(p/'Idle-Anim.png').convert('RGBA'); shadows=Image.open(p/'Idle-Shadow.png').convert('RGBA'); frames=[]
 for direction in range(8):
  row=[]
  for f in range(sheet.width//w):
   box=(f*w,direction*h,(f+1)*w,(direction+1)*h); im=sheet.crop(box); sh=np.array(shadows.crop(box)); yy,xx=np.where(np.all(sh[:,:,:3]==255,axis=2)&(sh[:,:,3]>0))
   assert len(xx)==1, 'unique white native anchor required'
   anchor=(int(xx[0]),int(yy[0])); c=blank(); c.alpha_composite(im,(ground[0]-anchor[0],ground[1]-anchor[1])); row.append(c); bounds.append(c.getbbox())
  frames.append(row)
 characters.append(frames)
# Circumscribe every opaque pixel from both forms / all directions / all Idle frames.
x0=min(b[0] for b in bounds);y0=min(b[1] for b in bounds);x1=max(b[2] for b in bounds);y1=max(b[3] for b in bounds)
cx=ground[0];cy=round((y0+y1)/2);radius=math.ceil(max(math.hypot(x-cx,y-cy) for x,y in [(x0,y0),(x1,y1),(x0,y1),(x1,y0)]))+5
particles=[(rng.random()*math.tau,rng.uniform(.5,1),rng.randint(0,11)) for _ in range(80)]
layernames=['ground','rear_lightning','shell','front_lightning','fragments','emblem']; atlases={n:Image.new('RGBA',(W*12,H*12)) for n in layernames}
previews=[[] for _ in range(8)]; checks=[]
for f in range(N):
 layers={n:blank() for n in layernames}; d={n:ImageDraw.Draw(im) for n,im in layers.items()}
 strength=min(1,f/24)*max(0,min(1,(116-f)/24))
 # Ground rings remain on one immutable world anchor.
 for ring in range(3):
  r=int(radius*(.7+ring*.22)+3*math.sin(f*.16+ring)); a=int(150*strength)
  d['ground'].ellipse((cx-r,ground[1]-r*.28,cx+r,ground[1]+r*.28),outline=rainbow(f/100+ring/3,a),width=2)
 # Six tall bolts, rear/front sorted by projected ground depth; impact sparks at feet.
 if 5<=f<76:
  for k in range(6):
   angle=k*math.tau/6+f*.022; bx=round(cx+math.cos(angle)*(radius+10)); by=round(ground[1]+math.sin(angle)*radius*.3)
   layer='rear_lightning' if math.sin(angle)<0 else 'front_lightning'; dr=d[layer]; rr=random.Random(k*1000+f//2)
   height=round((70+25*math.sin(k+f*.12))*min(1,(f-4)/12)*min(1,(76-f)/12))
   points=[(bx,by)]+[(bx+rr.randint(-11,11),by-int(height*j/7)) for j in range(1,8)]
   color=rainbow(k/6+f*.008,220);dr.line(points,fill=color,width=5);dr.line(points,fill=(245,255,255,255),width=1)
   d['ground'].ellipse((bx-7,by-3,bx+7,by+3),fill=color)
   for j in range(3):
    dx=rr.randint(-12,12);d['ground'].line((bx,by,bx+dx,by-rr.randint(2,8)),fill=color,width=1)
 # Discrete pixel sphere with quantized volume shading and full opaque phase.
 if 26<=f<91:
  grow=min(1,(f-25)/20); r=radius*grow; alpha=255 if f>=48 else round(255*(f-25)/23)
  yy,xx=np.mgrid[:H,:W]; nx=(xx-cx)/max(r,1);ny=(yy-cy)/max(r,1); mask=nx*nx+ny*ny<=1
  z=np.sqrt(np.maximum(0,1-nx*nx-ny*ny)); shade=np.clip(np.floor((.42+.50*z-.15*nx-.1*ny)*5)/5,.2,1)
  arr=np.zeros((H,W,4),dtype=np.uint8)
  for band in range(12):
   m=mask & ((np.floor((np.arctan2(ny,nx)/math.tau+1+f*.002)*12).astype(int)%12)==band)
   rgb=np.array(rainbow(band/12)[:3]);arr[m,:3]=(shade[m,None]*rgb).astype(np.uint8)
  arr[mask,3]=alpha; layers['shell']=Image.fromarray(arr); ds=ImageDraw.Draw(layers['shell'])
  if r>4: ds.arc((cx-r+4,cy-r+4,cx+r-4,cy+r-4),195,275,fill=(245,255,255,alpha),width=3)
  if f>=76:
   for k in range(7):
    angle=k*math.tau/7; pts=[(cx,cy)]
    for j in range(1,min(6,(f-74)//2)):
     a=angle+.13*math.sin(j*7+k);pts.append((cx+math.cos(a)*radius*j/5,cy+math.sin(a)*radius*j/5))
    if len(pts)>1:ds.line(pts,fill=(255,255,255,255),width=2)
 # Shell shards separate then shrink/fade into sparkles.
 if 91<=f<134:
  t=(f-91)/43
  for i,(angle,speed,delay) in enumerate(particles):
   travel=t*(32+speed*30); x=cx+math.cos(angle)*(radius+travel);y=cy+math.sin(angle)*(radius+travel*.7)+t*t*14
   size=max(1,round((6 if i<24 else 2)*(1-t)));color=rainbow(i/20,round(255*(1-t)**1.5))
   if i<24:d['fragments'].polygon([(x-size,y-size),(x+size,y),(x,y+size*2)],fill=color)
   else:d['fragments'].line((x-size,y,x+size,y),fill=color,width=1)
 # Original stylized double-helix flame sigil. NOT claimed to be exact official emblem.
 if 43<=f<140:
  opacity=min(1,(f-43)/15)*min(1,(140-f)/22); ey=cy-radius-25
  for strand in range(2):
   pts=[]
   for j in range(31):
    x=cx+math.sin(j/30*math.tau+strand*math.pi)*8;y=ey-15+j
    pts.append((x,y))
   for j in range(30):d['emblem'].line((*pts[j],*pts[j+1]),fill=rainbow(j/35+strand*.3,255*opacity),width=4)
  for j in range(5):
   x=cx-12+j*6; y=ey+9-int(5*math.sin(f*.25+j));d['emblem'].line((x,ey+15,x,y),fill=rainbow(j/5,180*opacity),width=2)
 for name in layernames: atlases[name].paste(layers[name],((f%12)*W,(f//12)*H))
 if 60<=f<=70:
  mask=np.array(layers['shell'])[:,:,3]
  for form in characters:
   for row in form:
    for sprite in row: assert np.all(mask[np.array(sprite)[:,:,3]>0]==255)
 for direction in range(8):
  scene=Image.new('RGBA',(W,H),(18,25,39,255));sd=ImageDraw.Draw(scene)
  for x in range(-W,W,24):sd.line((x,144,x+W,224),fill=(28,39,53))
  for x in range(0,W*2,24):sd.line((x,144,x-W,224),fill=(28,39,53))
  for name in ['ground','rear_lightning']:scene.alpha_composite(layers[name])
  form=0 if f<66 else 1;scene.alpha_composite(characters[form][direction][(f//7)%4])
  for name in ['shell','front_lightning','fragments','emblem']:scene.alpha_composite(layers[name])
  previews[direction].append(scene.convert('RGB'))
for n,a in atlases.items(): a.save(OUT/f'MEGA_V1_{n}.png')
for direction,frames in enumerate(previews):
 frames[0].save(OUT/f'preview_{direction}.webp',save_all=True,append_images=frames[1:],duration=33,loop=0,lossless=True)
contact=Image.new('RGB',(W*4,H*2))
for i,f in enumerate([0,20,42,60,80,94,108,140]):contact.paste(previews[0][f],((i%4)*W,(i//4)*H))
contact.save(OUT/'storyboard.png')
manifest={'status':'visual_prototype_not_PMDO_runtime_validated','frames':N,'ticks_per_frame':2,'fps':30,'cell':[W,H],'atlas_grid':[12,12],'ground_anchor':ground,'sphere_center':[cx,cy],'sphere_radius':radius,'measured_bounds': [x0,y0,x1,y1],'form_switch_frame':66,'fully_opaque_frames':[48,90],'layers':layernames,'directions':['D','DR','R','UR','U','UL','L','DL'],'coverage_test':'PASS: both forms, eight directions, all four Idle frames covered at frames 60–70','emblem':'original stylized double helix, official silhouette still needs correction','runtime_test':'NOT RUN','universal_fit':'Envelope algorithm demonstrated on Charizard/X only; no all-species roster validation'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
