"""Inspected generated keys -> registered PMDO-importable component animation sources."""
from pathlib import Path
import math,json
import numpy as np
import cv2
from scipy.ndimage import label
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent;OUT=ROOT/'exports/transformations_v1'
for n in ['components','review','gifs','views','baked_dir0']:(OUT/n).mkdir(parents=True,exist_ok=True)

def transparent(size):return Image.new('RGBA',size)
def opacity(im,a):
 im=im.copy();im.putalpha(im.getchannel('A').point(lambda p:round(p*max(0,min(1,a)))));return im

def key(im):
 a=np.array(im.convert('RGBA'));r,g,b=[a[:,:,j].astype(float) for j in range(3)]
 m=(r>150)&(b>150)&(r>g*1.7)&(b>g*1.7)
 a[m]=0;return Image.fromarray(a)

def regular_keys(name,size=(160,224),crop=False):
 im=Image.open(SRC/'generation'/f'{name}.png');w,h=im.width//4,im.height//2;out=[]
 for i in range(8):
  c=key(im.crop((i%4*w+3,i//4*h+3,(i%4+1)*w-3,(i//4+1)*h-3)))
  if crop:c=c.crop(c.getbbox())
  c=c.resize(size,Image.Resampling.NEAREST);out.append(c)
 return out

def tween(a,b,t,ab,ba):
 aa=np.array(a).astype(np.float32)/255;bb=np.array(b).astype(np.float32)/255
 aa[:,:,:3]*=aa[:,:,3,None];bb[:,:,:3]*=bb[:,:,3,None]
 yy,xx=np.mgrid[:a.height,:a.width].astype(np.float32)
 x=cv2.remap(aa,xx-ab[:,:,0]*t,yy-ab[:,:,1]*t,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
 y=cv2.remap(bb,xx-ba[:,:,0]*(1-t),yy-ba[:,:,1]*(1-t),cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
 c=x*(1-t)+y*t;c[:,:,:3]/=np.maximum(c[:,:,3,None],1/255)
 return Image.fromarray(np.uint8(np.clip(np.rint(c*255),0,255)))

def cycle(keys,sub=6,loop=True):
 out=[]
 for i in range(len(keys) if loop else len(keys)-1):
  a,b=keys[i],keys[(i+1)%len(keys)]
  ga=cv2.cvtColor(np.array(a)[:,:,:3],cv2.COLOR_RGB2GRAY);gb=cv2.cvtColor(np.array(b)[:,:,:3],cv2.COLOR_RGB2GRAY)
  ab=cv2.calcOpticalFlowFarneback(ga,gb,None,.5,3,15,3,5,1.2,0);ba=cv2.calcOpticalFlowFarneback(gb,ga,None,.5,3,15,3,5,1.2,0)
  for j in range(sub):out.append(a if j==0 else tween(a,b,j/sub,ab,ba))
 if not loop:out.append(keys[-1])
 return out

def atlas(frames,path,cols=8):
 w,h=frames[0].size;rows=math.ceil(len(frames)/cols);im=transparent((w*cols,h*rows))
 for i,f in enumerate(frames):im.paste(f,(i%cols*w,i//cols*h))
 im.save(path);return {'file':str(path.relative_to(OUT)),'cell':[w,h],'grid':[cols,rows],'logical_frames':len(frames),'padding_frames':cols*rows-len(frames)}

def gif(frames,path,durations=None):
 w,h=frames[0].size;samples=frames[::max(1,len(frames)//24)];mont=Image.new('RGB',(w*len(samples),h))
 for i,f in enumerate(samples):mont.paste(f.convert('RGB'),(i*w,0))
 pal=mont.quantize(colors=128,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 fs=[f.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
 dur=durations or ([30,30,40]*math.ceil(len(fs)/3))[:len(fs)]
 fs[0].save(path,save_all=True,append_images=fs[1:],duration=dur,loop=0,optimize=True,disposal=1)

def crown_views(kind):
 im=Image.open(SRC/'generation'/f'crown_{kind}_views.png')
 if kind=='fire':
  # The generator returned nine irregular views, NOT its requested4x2 layout.
  boxes=[(0,0,412,335),(416,0,685,335),(690,0,925,335),(480,337,870,575),(50,572,408,851),(485,573,865,851),(0,849,450,1145),(530,847,928,1145)]
 else:
  w,h=im.width//3,im.height//3
  boxes=[(i%3*w+2,i//3*h+2,(i%3+1)*w-2,(i//3+1)*h-2) for i in [0,1,2,3,4,5,6,8]]
 result=[]
 for direction,box in enumerate(boxes):
  c=key(im.crop(box));a=np.array(c);lab,n=label(a[:,:,3]>0)
  if n:
   counts=np.bincount(lab.ravel());counts[0]=0;main=lab==int(counts.argmax());yy,xx=np.where(main)
   # Reject neighboring cell debris; retain disconnected tips within the main object bounds.
   rect=np.zeros_like(main);rect[max(0,yy.min()-2):min(c.height,yy.max()+3),max(0,xx.min()-2):min(c.width,xx.max()+3)]=True
   a[~rect]=0;c=Image.fromarray(a)
  # Retain all jewel/flame pieces; don't discard disconnected flame tips.
  box2=c.getbbox();c=c.crop(box2);c.thumbnail((42,48),Image.Resampling.NEAREST)
  base=transparent((64,64));base.alpha_composite(c,((64-c.width)//2,57-c.height))
  from crown_attachment.clean import remove_face
  result.append(remove_face(base,kind,direction))
 return result

def load_assets():
 k={
  'column':regular_keys('dynamax_column'),
  'lightning':regular_keys('red_lightning'),
  'cloud':regular_keys('dynamax_clouds',(64,28),True),
  'giga':regular_keys('gigantamax_column_corrected',(192,224)),
  'growth':regular_keys('tera_crystal_growth',(128,144)),
  'prism':regular_keys('tera_crystal_cycle',(128,144))}
 a={n:cycle(v[1:7] if n=='giga' else v,8 if n=='giga' else 6,n!='growth') for n,v in k.items()}
 a['growth_keys']=k['growth'];a['crowns']={n:crown_views(n) for n in ['fire','water']}
 manifest={}
 for n in ['column','lightning','cloud','giga','growth','prism']:
  fs=a[n];rows=math.ceil(len(fs)/8);path=OUT/'components'/f'TR_V1_{n}.8x{rows}.png';manifest[n]=atlas(fs,path)
  bg=[]
  for f in fs:
   c=Image.new('RGBA',f.size,(19,27,42,255));c.alpha_composite(f);bg.append(c)
  gif(bg,OUT/'gifs'/f'component_{n}.gif')
 for name,views in a['crowns'].items():
  # One static frame, eight rows, square cells. Actual DirSheet suffix interpreted by engine.
  sheet=transparent((64,512))
  for d,im in enumerate(views):sheet.paste(im,(0,d*64))
  sheet.save(OUT/'components'/f'TR_V1_crown_{name}.Dir8.png')
 manifest['crown_view_status']='Fire/Water approximate generated angle models, with canonical references; geometry and orientation need approval. Normal generation failed. No other crowns exported.'
 (OUT/'component_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 return a
