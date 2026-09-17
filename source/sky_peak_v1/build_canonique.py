from pathlib import Path
import json,math,colorsys,base64,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;O=R/'renders/sky_peak_canonique_v1';B=R/'renders/sky_peak_plaine_v1/bruts';N=Image.Resampling.NEAREST
import sys
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
S=(504,504)
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def key(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];a[(r>35)&(b>35)&(r>g*1.8)&(b>g*1.8)]=0;return Image.fromarray(a)
def blank():return Image.new('RGBA',S)
refs=[np.array(load(P/f'gif_{i}.png')) for i in range(4)];a=refs[0];y,x=np.mgrid[:504,:504]
# Delimit foreground by the first native grass pixel in each column: no relocation or rescaling.
green=(a[:,:,1]>a[:,:,0].astype(float)*1.1)&(a[:,:,1]>a[:,:,2].astype(float)*1.1)&(y>=120)
top=np.argmax(green,axis=0);fg=y>=top[None,:]
petals=[]
for frame in refs:
 r,g,b=[frame[:,:,i].astype(float) for i in range(3)];petals.append((r>190)&(r>g*1.04)&(r>b*1.08)&fg)
union=np.logical_or.reduce(petals)
# Group petals across all four phases to keep each blossom the same color family.
labels=np.full(S,-1,dtype=int);groups=0
for sy,sx in zip(*np.where(union)):
 if labels[sy,sx]>=0:continue
 stack=[(int(sy),int(sx))];labels[sy,sx]=groups
 while stack:
  yy,xx=stack.pop()
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
   ny,nx=yy+dy,xx+dx
   if 0<=ny<504 and 0<=nx<504 and union[ny,nx] and labels[ny,nx]<0:labels[ny,nx]=groups;stack.append((ny,nx))
 groups+=1
# Fill only removed petals, using available native non-petal observations; otherwise native grass RGB.
clean=a.copy();clean[union]=[135,247,119,255]
for i,frame in enumerate(refs):
 valid=union&(~petals[i]);clean[valid]=frame[valid]
clean[~fg]=0;grass=(clean[:,:,1]>clean[:,:,0].astype(float)*1.05)&(clean[:,:,1]>clean[:,:,2].astype(float)*1.05)&fg
masks={'05_sol_et_rebord_herbeux':grass,'06_paroi_et_rochers':fg&~grass}
terrain={}
for name,mask in masks.items():
 ar=clean.copy();ar[~mask]=0;terrain[name]=Image.fromarray(ar);save(terrain[name],O/'jour'/(name+'.png'));save(night(terrain[name]),O/'nuit'/(name+'.png'))
save(Image.fromarray((union*255).astype('uint8')),O/'masque_fleurs_retirees.png');save(Image.fromarray((fg*255).astype('uint8')),O/'masque_terrain_reference.png')
assert np.array_equal(clean[fg&~union],a[fg&~union])
# Four harmonized hues; shape and positions come from the actual GIF frames.
hues=[.025,.09,.145,.77];keys=[]
for i,frame in enumerate(refs):
 out=np.zeros_like(frame);out[petals[i]]=frame[petals[i]]
 for color in np.unique(frame[petals[i],:3],axis=0):
  _,l,s=colorsys.rgb_to_hls(*(color/255));match=petals[i]&np.all(frame[:,:,:3]==color,axis=2)
  for family,hue in enumerate(hues):
   mm=match&(labels%4==family);rgb=np.round(np.array(colorsys.hls_to_rgb(hue,l,min(s,.72)))*255).astype('uint8');out[mm,:3]=rgb
 im=Image.fromarray(out);keys.append(im);save(im,O/'fleurs/cles'/f'{i:02}.png')
 sheet=None
# Premultiplied crossfade: optional slower 32-step version; original keys also delivered.
def mix(a,b,t):
 a=np.array(a).astype(float)/255;b=np.array(b).astype(float)/255;al=a[:,:,3:]*(1-t)+b[:,:,3:]*t;rgb=a[:,:,:3]*a[:,:,3:]*(1-t)+b[:,:,:3]*b[:,:,3:]*t;rgb=np.divide(rgb,al,out=np.zeros_like(rgb),where=al>0);return Image.fromarray(np.round(np.concatenate([rgb,al],2)*255).clip(0,255).astype('uint8'))
flowers=[]
for f in range(32):
 k=f//8;u=(f%8)/8;u=u*u*(3-2*u);im=mix(keys[k],keys[(k+1)%4],u);flowers.append(im);save(im,O/'fleurs/jour'/f'{f:02}.png');save(night(im),O/'fleurs/nuit'/f'{f:02}.png')
for ims,name,cols in [(keys,'fleurs_4_cles',2),(flowers,'fleurs_32_phases',8)]:
 sheet=Image.new('RGBA',(cols*252,math.ceil(len(ims)/cols)*252))
 for i,im in enumerate(ims):sheet.alpha_composite(im.resize((252,252),N),(i%cols*252,i//cols*252))
 save(sheet,O/'planches'/(name+'.png'))
# Distant panorama and two wrap layers, independent of the flower clock.
mount=key(load(B/'montagnes.png')).resize((504,175),N);mountfull=blank();mountfull.alpha_composite(mount,(0,7))
cloudsheet=key(load(B/'nuages.png'));cw,ch=cloudsheet.size;clouds=[]
for row in range(3):
 im=cloudsheet.crop((0,row*ch//3,cw,(row+1)*ch//3));im=im.crop(im.getbbox());clouds.append(im)
far=blank();near=blank()
for im,width,xy,target in [(clouds[0],310,(0,20),far),(clouds[1],255,(245,43),far),(clouds[2],335,(80,85),near)]:target.alpha_composite(im.resize((width,round(im.height*width/im.width)),N),xy)
manifest={'canvas':list(S),'reference_commit':'8b7e760','layout':'Terrain repris directement du GIF sans deplacement ni redimensionnement. Essais de nouveaux plateaux rejetes.','native_flower_frames':4,'native_duration_ms':[200]*4,'smooth_frames':32,'smooth_frame_ms':50,'smooth_loop_ms':1600,'flower_colors':['corail doux','peche','creme','mauve'],'clouds':{'wrap_x':504,'far_px_s':-2,'near_px_s':-6,'far_period_s':252,'near_period_s':84},'modes':{}}
for mode in ['jour','nuit']:
 dark=mode=='nuit';sky=np.zeros((504,504,4),dtype='uint8');u=np.clip(y/160,0,1)[:,:,None];topc=np.array([20,88,236] if not dark else [8,17,49]);bottom=np.array([204,237,255] if not dark else [54,74,122]);sky[:,:,:3]=topc*(1-u)+bottom*u;sky[:,:,3]=255
 layers={'01_ciel':Image.fromarray(sky)};stars=blank();moon=blank()
 if dark:
  rng=np.random.default_rng(87);d=ImageDraw.Draw(stars)
  for xx,yy in zip(rng.integers(2,502,65),rng.integers(2,108,65)):d.point((int(xx),int(yy)),fill=(227,238,255,205))
  m=load(R/'renders/references_calques_v1/nuit/04_lune_halo.png').crop((650,65,850,265)).resize((66,66),N);moon.alpha_composite(m,(385,10))
 layers['02_etoiles']=stars;layers['03_lune_halo']=moon;layers['04a_nuages_lointains_wrap']=night(far) if dark else far;layers['04b_montagnes']=night(mountfull) if dark else mountfull;layers['04c_nuages_proches_wrap']=night(near) if dark else near
 for name,im in terrain.items():layers[name]=night(im) if dark else im
 layers['07_fleurs']=night(flowers[0]) if dark else flowers[0]
 comp=blank()
 for name,im in layers.items():save(im,O/mode/(name+'.png'));comp.alpha_composite(im)
 save(comp,O/mode/'composition.png');manifest['modes'][mode]=list(layers)
 frames=[]
 for f in range(32):
  comp=blank()
  for name,im in layers.items():comp.alpha_composite((night(flowers[f]) if dark else flowers[f]) if name=='07_fleurs' else im)
  frames.append(comp)
 frames[0].save(O/mode/'fleurs_animation.webp',save_all=True,append_images=frames[1:],duration=50,loop=0,lossless=True)
manifest['note_animation']='Les WebP courts montrent les fleurs avec nuages fixes; la galerie fait defiler les nuages sur leurs horloges longues sans saut a 1,6s.'
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'verification_terrain.json').write_text(json.dumps({'source_size':[504,504],'unchanged_native_pixels_outside_flower_mask':int((fg&~union).sum()),'unchanged_native_pixels_exact':True,'flower_groups':groups,'runtime_validated':False},indent=2));print('Canonical layout retained; flower4/32, harmonized hues and 2 wrap overlays')
