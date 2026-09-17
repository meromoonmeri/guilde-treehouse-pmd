from pathlib import Path
import sys,json,math,random,zipfile,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/references_calques_v2';B=O/'bruts';V=R/'renders/references_calques_v1';sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
N=Image.Resampling.NEAREST; SZ=(960,600)
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def key(im):
 a=np.array(im.convert('RGBA'));r,g,b=[a[:,:,i].astype(int) for i in range(3)];a[(r>145)&(b>125)&(g<120)&(r>g*1.6)&(b>g*1.6)]=0;return Image.fromarray(a)
def load(p):return Image.open(p).convert('RGBA')
def blank(sz=SZ):return Image.new('RGBA',sz)
def place(im,size,xy):
 o=blank();o.alpha_composite(im.resize(size,N),xy);return o
def sheet(ims,cols,p):
 w,h=ims[0].size;o=blank((w*cols,h*math.ceil(len(ims)/cols)))
 for i,im in enumerate(ims):o.alpha_composite(im,((i%cols)*w,(i//cols)*h))
 save(o,p)
manifest={'canvas':list(SZ),'phases':64,'frame_ms':80,'cycle_ms':5120,'clouds':{'wrap_x':True,'speed_px_s':-4,'period_s':240,'layer':'overlay transparent, placement avant astres selon ordre manifeste'},'terrains':[],'backgrounds':{}}
# Exact old ZIP source; no guessed replacement of the coastal gradient.
zpath=R/'cote_metano_v2_wrap_palette.zip';member='sprites/cote_v2/01_promontoire/COTEV2_01_00_CIEL_SANS_NUAGES.png'
with zipfile.ZipFile(zpath) as z:
 import io
 sky=Image.open(io.BytesIO(z.read(member))).convert('RGBA');source_hash=hashlib.sha256(z.read(member)).hexdigest()
sky=sky.crop(sky.getbbox());sky=sky.resize((960,280),N)
# Preserve the existing gradient's band spacing for sunset, deriving hue only.
a=np.array(sky);lum=a[:,:,:3].mean(axis=2);t=(lum-lum.min())/max(1,lum.max()-lum.min());top=np.array([112,103,168]);bottom=np.array([255,184,112]);a[:,:,:3]=(top[None,None,:]*(1-t[:,:,None])+bottom[None,None,:]*t[:,:,None]).astype('uint8');sunset=Image.fromarray(a)
for mode,s in [('jour',sky),('coucher',sunset),('nuit',night(sky))]:
 full=blank();full.alpha_composite(s,(0,0));full.alpha_composite(s.crop((0,279,960,280)).resize((960,320),N),(0,280));save(full,Path('fonds')/mode/'01_ciel.png')
 save(load(V/('nuit' if mode=='nuit' else 'coucher')/'05_mer.png'),Path('fonds')/mode/'05_mer.png')
 clouds=load(V/('nuit' if mode=='nuit' else 'coucher')/'03_nuages.png');save(clouds,Path('fonds')/mode/'03_nuages_wrap.png')
 if mode!='nuit':save(load(V/'coucher/04_soleil.png'),Path('fonds')/mode/'04_soleil.png')
 manifest['backgrounds'][mode]={'sky':'fonds/'+mode+'/01_ciel.png','sea':'fonds/'+mode+'/05_mer.png','clouds':'fonds/'+mode+'/03_nuages_wrap.png'}
manifest['sky_source']={'zip':zpath.name,'member':member,'sha256':source_hash,'day':'RGB source conservé, ajustement nearest au ciel 960×280','sunset':'mêmes paliers, teintes coucher dérivées','night':'filtre Abyss exact appliqué au ciel source'}
# Isolate moon disk from halo: disjoint masks recompose the V1 moon pixel-exactly.
moon=load(V/'nuit/04_lune_halo.png');a=np.array(moon);diskmask=(a[:,:,0]>125)&(a[:,:,1]>120)&(a[:,:,2]<a[:,:,0]*1.2)&(a[:,:,3]>0);disk=a.copy();disk[~diskmask]=0;halo=a.copy();halo[diskmask]=0;save(Image.fromarray(disk),Path('astres/lune.png'))
assert np.array_equal(np.array(Image.alpha_composite(Image.fromarray(halo),Image.fromarray(disk))),a)
rng=random.Random(41);stars=[(rng.randrange(8,952),rng.randrange(8,268),rng.randrange(2,4),rng.random()*math.tau) for i in range(95)]
starframes=[];haloframes=[]
for f in range(64):
 im=blank();d=ImageDraw.Draw(im)
 for i,(x,y,s,p) in enumerate(stars):
  power=(math.sin(math.tau*f/64+p)+1)/2;alpha=round(75+180*power);d.rectangle((x,y,x+1,y+1),fill=(224,237,255,alpha))
  if i%7==0:
   d.line((x-s,y,x+s+1,y),fill=(185,212,255,round(alpha*.45)));d.line((x,y-s,x,y+s+1),fill=(185,212,255,round(alpha*.45)))
 save(im,Path('etoiles')/f'{f:02}.png');starframes.append(im.resize((240,150),N))
 ha=halo.copy();ha[:,:,3]=(ha[:,:,3]*(.78+.22*math.cos(math.tau*f/64))).astype('uint8');h=Image.fromarray(ha);save(h,Path('astres/halo')/f'{f:02}.png');haloframes.append(h.crop((640,55,860,275)))
sheet(starframes,8,Path('planches/etoiles_64.png'));sheet(haloframes,8,Path('planches/halo_64.png'))
# Generated 4x2 reflection sheets -> registered keyframes. Each is centered on same anchor.
for kind in ['lune','soleil']:
 raw=key(load(B/f'reflet_{kind}_8frames.png'));w,h=raw.size;keys=[]
 for i in range(8):
  cell=raw.crop((i%4*w//4,i//4*h//2,(i%4+1)*w//4,(i//4+1)*h//2));cell=cell.crop(cell.getbbox());cell=cell.resize((152,218),N);keys.append(cell);save(cell,Path('reflets')/kind/'cles'/f'{i:02}.png')
 sheet(keys,4,Path('planches')/f'reflet_{kind}_8_cles.png')
 frames=[]
 for f in range(64):
  k=f//8;u=(f%8)/8;u=u*u*(3-2*u)
  # Premultiplied interpolation avoids colored fringes around transparent pixels.
  aa=np.array(keys[k]).astype(float)/255;bb=np.array(keys[(k+1)%8]).astype(float)/255
  alpha=aa[:,:,3:]*(1-u)+bb[:,:,3:]*u;rgb=aa[:,:,:3]*aa[:,:,3:]*(1-u)+bb[:,:,:3]*bb[:,:,3:]*u
  rgb=np.divide(rgb,alpha,out=np.zeros_like(rgb),where=alpha>0);out=np.concatenate([rgb,alpha],axis=2);im=Image.fromarray(np.round(out*255).clip(0,255).astype('uint8'))
  save(im,Path('reflets')/kind/'frames'/f'{f:02}.png');frames.append(im)
 sheet(frames,8,Path('planches')/f'reflet_{kind}_64.png')
# Ten independent cliffs; retain all original generator images.
raws={}
for name,ids in [('falaises_01_02.png',[1,2]),('falaises_03_04.png',[3,4])]:
 im=key(load(B/name));w,h=im.size
 for row,i in enumerate(ids):
  c=im.crop((0,row*h//2,w,(row+1)*h//2));raws[i]=c.crop(c.getbbox())
for i in range(5,11):raws[i]=key(load(B/f'falaise_{i:02}.png'))
# Replace generated tan dirt marks on 05/07 with canonical grass, preserving cliff.
grass=load(R/'source/falaises_metano/patches/herbe.png');ga=np.array(grass)
for i,im in raws.items():
 if i in (5,7):
  ar=np.array(im);rr,gg,bb=[ar[:,:,j].astype(int) for j in range(3)];mask=(rr>180)&(gg>125)&(bb>75)&(rr>gg*1.08)&(bb>gg*.48)&(ar[:,:,3]>0);yy,xx=np.indices(mask.shape);mask&=yy<im.height*.55;ar[mask,:3]=ga[yy[mask]%grass.height,xx[mask]%grass.width,:3];im=Image.fromarray(ar)
 save(im,Path('falaises')/f'{i:02}'/'terrain.png');save(night(im),Path('falaises')/f'{i:02}'/'terrain_nuit.png')
 # Proportional fit, pin requested side; never stretch generated terrain.
 scale=820/im.width;size=(round(im.width*scale),round(im.height*scale));side='gauche' if i in [1,3,5,7,9] else 'droite';x=0 if side=='gauche' else 960-size[0];y=215
 # Cropping at viewport edges intentional: these cliffs are foreground, not floating islands.
 for mode,src in [('jour',im),('nuit',night(im))]:
  layer=place(src,size,(x,y))
  if y+size[1]<600:
   # Extend only the terminal wall downward; exported original remains intact.
   stripe=layer.crop((0,y+size[1]-24,960,y+size[1]))
   for sy in range(y+size[1],600,24):layer.alpha_composite(stripe,(0,sy))
  save(layer,Path('falaises')/f'{i:02}'/f'calque_{mode}.png')
 note='Texture guidée par le promontoire; validation utilisateur requise.'
 if i==9:note='Réserve : blocs et contour plus gros que le promontoire approuvé.'
 if i in [2,3,4]:note='Réserve : silhouette générée plus isolée/rectiligne; montage recadré au premier plan.'
 manifest['terrains'].append({'id':f'{i:02}','side':side,'native_size':list(im.size),'position':[x,y],'display_size':list(size),'audit':note})
# Static compositions and compact animated samples.
def composition(i,mode,f=0,cloud_x=0):
 p=O/'fonds'/mode;out=load(p/'01_ciel.png')
 if mode!='jour':out.alpha_composite(load(O/'etoiles'/f'{f:02}.png'))
 cloud=load(p/'03_nuages_wrap.png');xx=round(cloud_x)%960;out.alpha_composite(cloud,(xx,0));out.alpha_composite(cloud,(xx-960,0))
 if mode=='nuit':
  out.alpha_composite(load(O/'astres/halo'/f'{f:02}.png'));out.alpha_composite(load(O/'astres/lune.png'))
 else:out.alpha_composite(load(p/'04_soleil.png'))
 out.alpha_composite(load(p/'05_mer.png'));out.alpha_composite(load(O/'reflets'/('lune' if mode=='nuit' else 'soleil')/'frames'/f'{f:02}.png'),(674,281));
 if i in [2,4,6,8,10]:out=out.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 out.alpha_composite(load(O/'falaises'/f'{i:02}'/('calque_nuit.png' if mode=='nuit' else 'calque_jour.png')));return out
board=Image.new('RGB',(1600,1200),'#172338');d=ImageDraw.Draw(board)
for i in range(1,11):
 for mode in ['jour','coucher','nuit']:save(composition(i,mode),Path('falaises')/f'{i:02}'/f'scene_{mode}.png')
 im=composition(i,'coucher').resize((400,250),N);x=(i-1)%4*400;y=(i-1)//4*400;board.paste(im,(x,y+28));d.text((x+8,y+8),f'{i:02} | '+manifest['terrains'][i-1]['side'],fill='white')
 d.text((x+8,y+285),manifest['terrains'][i-1]['audit'][:51],fill='#ffdd99')
save(board,Path('PLANCHE_10_FALAISES.png'))
for mode in ['coucher','nuit']:
 ims=[composition(1,mode,f).resize((480,300),N) for f in range(64)];save(ims[0],Path('apercus')/f'{mode}_fixe.png');p=O/'apercus'/f'{mode}_animation.webp';ims[0].save(p,save_all=True,append_images=ims[1:],duration=80,loop=0,lossless=True)
manifest['animation_method']='8 phases générées par reflet, recalées puis interpolation alpha prémultipliée vers 64 phases. Étoiles/halo paramétriques indépendants; wrap nuages indépendant de la boucle 5,12s.'
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Build complete')
