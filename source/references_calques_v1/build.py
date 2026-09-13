"""Reproducible layers from retained generator originals. python + Pillow + numpy."""
from pathlib import Path
import sys,json,random,math,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
OUT=ROOT/'renders/references_calques_v1'; RAW=OUT/'bruts'; SIZE=(960,600); N=Image.Resampling.NEAREST

def load(n):return Image.open(RAW/(n+'.png')).convert('RGBA')
def key(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];mask=(r>150)&(b>130)&(g<110)&(r>g*1.6)&(b>g*1.6);a[mask]=0
 return Image.fromarray(a)
def blank():return Image.new('RGBA',SIZE)
def put(im,size,xy):
 o=blank();o.alpha_composite(im.resize(size,N),xy);return o
cloud=key(load('nuages')); cw,ch=cloud.size
clouds=[]
for row in range(3):
 pair=[]
 for col in range(2):
  c=cloud.crop((col*cw//2,row*ch//3,(col+1)*cw//2,(row+1)*ch//3));pair.append(c.crop(c.getbbox()))
 clouds.append(pair)
moon=key(load('lune'));moon=moon.crop(moon.getbbox());a=np.array(moon);h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];rad=np.sqrt(((xx-w/2)/(w/2))**2+((yy-h/2)/(h/2))**2);a[:,:,3]=(a[:,:,3]*np.clip((1-rad)/.27,0,1)).astype('uint8');a[a[:,:,3]==0]=0;moon=Image.fromarray(a)
manifest={'canvas':list(SIZE),'frames':64,'frame_ms':80,'cycle_ms':5120,'animation':'Reconstruction, géométrie fixe et modulation cyclique douce du reflet; pas animation originale récupérée.','scenes':{}}
for mode in ['coucher','nuit','guilde']:
 p=OUT/mode;p.mkdir(parents=True,exist_ok=True);layers={};dark=mode!='coucher';layers['01_ciel']=put(load('ciel_nuit' if dark else 'ciel_coucher'),SIZE,(0,0))
 stars=blank();d=ImageDraw.Draw(stars);rng=random.Random(41)
 for i in range(105 if dark else 25):
  x=rng.randrange(960);y=rng.randrange(10,270 if dark else 130);s=2 if i%7==0 else 1;d.rectangle((x,y,x+s,y+s),fill=(218,232,255,210 if dark else 125))
 layers['02_etoiles']=stars
 c=blank();row={'coucher':0,'nuit':1,'guilde':2}[mode]
 for im,xy,width in zip(clouds[row],[(590,190),(765,235)] if mode!='guilde' else [(30,140),(680,155)],[135,150]):
  c.alpha_composite(im.resize((width,round(im.height*width/im.width)),N),xy)
 layers['03_nuages']=c
 if mode=='nuit':layers['04_lune_halo']=put(moon,(180,180),(660,75))
 if mode=='coucher':
  sun=blank();d=ImageDraw.Draw(sun);d.ellipse((732,255,768,291),fill=(255,229,151,255));layers['04_soleil']=sun
 if mode=='guilde':layers['05_montagnes_foret']=put(key(load('fond_guilde')),SIZE,(0,0))
 else:layers['05_mer']=put(load('mer_'+mode),(960,320),(0,280))
 if mode!='guilde':
  # Fixed irregular strips; only their brightness/opacity cycles, no translating texture.
  rng=random.Random(75);strips=[]
  for y in range(283,493,3):
   t=(y-283)/210;half=62*(1-t)+7;offset=rng.uniform(-12,12);strips.append((y,750+offset-half*rng.uniform(.5,1),750+offset+half*rng.uniform(.5,1),rng.random()*math.tau))
  ap=p/'reflet';ap.mkdir(exist_ok=True)
  for f in range(64):
   im=blank();d=ImageDraw.Draw(im)
   for y,x0,x1,phase in strips:
    alpha=round(155+65*math.sin(math.tau*f/64+phase));color=(255,222,142,alpha) if mode=='coucher' else (213,223,255,alpha);d.rectangle((round(x0),y,round(x1),y+1),fill=color)
   im.save(ap/f'{f:02}.png')
   if f==0:layers['06_reflet']=im
 terrain=key(load('plateau_guilde' if mode=='guilde' else 'promontoire'))
 if dark:terrain=night(terrain)
 layers['07_falaise']=put(terrain,(940,450),(10,170)) if mode=='guilde' else put(terrain,(820,490),(0,215))
 scene=blank()
 for name,im in layers.items():
  ar=np.array(im);ar[ar[:,:,3]==0]=0;im=Image.fromarray(ar);layers[name]=im;im.save(p/(name+'.png'));scene.alpha_composite(im)
 scene.save(p/'composition.png');manifest['scenes'][mode]={'layers':[n+'.png' for n in layers],'reference':{'coucher':'IMG_4899.jpeg','nuit':'IMG_4889.png','guilde':'IMG_4900.gif'}[mode]}
 if mode!='guilde':
  frames=[]
  for f in range(64):
   comp=blank()
   for name,im in layers.items():comp.alpha_composite(Image.open(p/'reflet'/f'{f:02}.png').convert('RGBA') if name=='06_reflet' else im)
   frames.append(comp.convert('RGB'))
  frames[0].save(p/'animation.webp',save_all=True,append_images=frames[1:],duration=80,loop=0,lossless=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Independently reopen exported PNGs and verify their actual recomposition.
checks=[]
for mode,spec in manifest['scenes'].items():
 comp=blank()
 for name in spec['layers']:
  im=Image.open(OUT/mode/name).convert('RGBA');assert im.size==SIZE;comp.alpha_composite(im)
 assert np.array_equal(np.array(comp),np.array(Image.open(OUT/mode/'composition.png')))
 checks.append(mode+': dimensions et recomposition exacte des exports OK')
for p in OUT.glob('*/reflet/*.png'):assert Image.open(p).size==SIZE
(OUT/'verification.json').write_text(json.dumps({'checks':checks,'reflection_frames':128,'note':'Recomposition vérifiée contre les nouvelles compositions, pas contre les générations perdues. Pas de validation PMDO.'},ensure_ascii=False,indent=2))
print('\n'.join(checks))
