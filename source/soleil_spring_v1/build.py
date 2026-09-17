from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/soleil_spring_v1';B=O/'bruts';N=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def key(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];a[(r>145)&(b>125)&(g<120)&(r>g*1.6)&(b>g*1.6)]=0;return Image.fromarray(a)
def sheet(ims,cols,p):
 w,h=ims[0].size;out=Image.new('RGBA',(cols*w,math.ceil(len(ims)/cols)*h))
 for i,im in enumerate(ims):out.alpha_composite(im,((i%cols)*w,(i//cols)*h))
 save(out,p)
def mix(a,b,t):
 a=np.array(a).astype(float)/255;b=np.array(b).astype(float)/255;alpha=a[:,:,3:]*(1-t)+b[:,:,3:]*t;rgb=a[:,:,:3]*a[:,:,3:]*(1-t)+b[:,:,:3]*b[:,:,3:]*t;rgb=np.divide(rgb,alpha,out=np.zeros_like(rgb),where=alpha>0);return Image.fromarray(np.round(np.concatenate([rgb,alpha],2)*255).clip(0,255).astype('uint8'))
raw=key(load(B/'soleil_8_cles.png'));w,h=raw.size;keys=[]
for i in range(8):
 im=raw.crop((i%4*w//4,i//4*h//2,(i%4+1)*w//4,(i//4+1)*h//2));im=im.crop(im.getbbox()).resize((96,96),N);a=np.array(im);yy,xx=np.mgrid[:96,:96];rad=np.sqrt((xx-47.5)**2+(yy-47.5)**2);a[:,:,3]=(a[:,:,3]*np.clip((48-rad)/12,0,1)).astype('uint8');im=Image.fromarray(a);keys.append(im);save(im,Path('soleil/cles')/f'{i:02}.png')
# Locked central disk, only subtle 22% variation around it.
a=np.array(keys[0]);yy,xx=np.mgrid[:96,:96];diskmask=(xx-47.5)**2+(yy-47.5)**2<23**2;disk=a.copy();disk[~diskmask]=0;save(Image.fromarray(disk),Path('soleil/disque_fixe.png'));suns=[];halos=[]
for f in range(64):
 k=f//8;u=f%8/8;u=u*u*(3-2*u);im=mix(keys[0],mix(keys[k],keys[(k+1)%8],u),.22);ar=np.array(im);ar[diskmask]=disk[diskmask];im=Image.fromarray(ar);suns.append(im);ha=ar.copy();ha[diskmask]=0;halos.append(Image.fromarray(ha));save(im,Path('soleil/frames')/f'{f:02}.png');save(halos[-1],Path('soleil/halo')/f'{f:02}.png')
sheet(keys,4,Path('planches/soleil_8_cles.png'));sheet(suns,8,Path('planches/soleil_64.png'));sheet(halos,8,Path('planches/soleil_halo_64.png'))
raw=key(load(B/'grands_nuages.png'));w,h=raw.size
for row,mode in enumerate(['jour','coucher','nuit']):
 im=raw.crop((0,row*h//3,w,(row+1)*h//3));im=im.crop(im.getbbox());save(im,Path('nuages')/f'{mode}_sprite.png');im=im.resize((690,round(im.height*690/im.width)),N);overlay=Image.new('RGBA',(960,600));overlay.alpha_composite(im,(80,132));save(overlay,Path('nuages')/f'{mode}_overlay.png')
# Native map and animation phases read directly, not simulated from a screenshot.
o=json.loads((P/'luminous_spring.rsground').read_text(encoding='utf-8-sig'))['Object'];banks={n:load(P/(n+'.png')) for n in ['LuminousSpring','LuminousSpringAnim']}
base=load(P/'halcyon_layer_0.png');generated=load(B/'luminous_spring_variante.png').resize((600,600),N)
protected=Image.new('L',(600,600));d=ImageDraw.Draw(protected);d.polygon([(175,0),(425,0),(470,160),(480,320),(420,354),(180,354),(120,320),(130,160)],fill=255)
for l in o['Layers']:
 for x,col in enumerate(l['Tiles']):
  for y,t in enumerate(col):
   if any(len(a['Frames'])>1 for a in t['Layers']):d.rectangle((x*24-24,y*24-24,(x+1)*24+24,(y+1)*24+24),fill=255)
# Feather OUTSIDE protected pixels only; all original pool/animation cells stay exact.
pa=np.array(protected);soft=np.maximum(pa,np.array(protected.filter(ImageFilter.GaussianBlur(9))));static=Image.composite(base,generated,Image.fromarray(soft));save(static,Path('spring/01_decor.png'));save(protected,Path('spring/masque_zone_native.png'))
groups={3:[],13:[]}
for count in groups:
 for f in range(count):
  overlay=Image.new('RGBA',(600,600))
  for l in o['Layers']:
   if not l['Visible']:continue
   for x,col in enumerate(l['Tiles']):
    for y,t in enumerate(col):
     for a in t['Layers']:
      if len(a['Frames'])!=count:continue
      v=a['Frames'][f];p=v['TexLoc'];tx,ty=p['X']*24,p['Y']*24;overlay.alpha_composite(banks[v['Sheet']].crop((tx,ty,tx+24,ty+24)),(x*24,y*24))
  groups[count].append(overlay);save(overlay,Path('spring')/('02_cycle_3' if count==3 else '03_cycle_13')/f'{f:02}.png')
 sheet([im.resize((300,300),N) for im in groups[count]],count if count==3 else 4,Path('planches')/f'spring_cycle_{count}.png')
frames=[]
for f in range(39):
 im=static.copy();im.alpha_composite(groups[3][f%3]);im.alpha_composite(groups[13][f%13]);frames.append(im);save(im,Path('spring/frames')/f'{f:02}.png')
save(frames[0],Path('spring/composition.png'));frames[0].save(O/'spring/animation.webp',save_all=True,append_images=frames[1:],duration=[167,167,166]*13,loop=0,lossless=True)
provenance={'halcyon_commit':(P/'commit.txt').read_text().strip(),'halcyon_repo':'Palikadude/Halcyon','assets_commit':(P/'rawasset_commit.txt').read_text().strip(),'assets_repo':'PMDCollab/RawAsset','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.iterdir() if p.suffix in ['.png','.rsground','.lua']},'note':'Carte Halcyon, graphismes de base PMDO RawAsset ; cela ne signifie pas que tous les graphismes sont créés par Palika ni libres de droits.'}
(P/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
manifest={'sun':{'size':[96,96],'position':[702,212],'keyframes':8,'frames':64,'frame_ms':80,'period_ms':5120,'method':'Génération 8 clés puis recalage, disque verrouillé, variation 22%, interpolation alpha prémultiplié'},'clouds':{'canvas':[960,600],'wrap_x':960,'speed_px_s':-8,'period_s':120,'draw_order':'APRÈS soleil/lune, AVANT mer et falaise','modes':['jour','coucher','nuit']},'spring':{'size':[600,600],'cell_px':24,'cycles':[3,13],'frame_ticks':10,'engine_hz':60,'joint_frames':39,'period_ms':6500,'layout':'Carte Halcyon conservée ; variante générée du pourtour. Bassin et toutes cellules animées natifs conservés.','runtime_validated':False}}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Build complete: sun64 + clouds3 + spring39 native-timed phases')
