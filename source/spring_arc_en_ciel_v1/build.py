from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];O=R/'renders/spring_arc_en_ciel_v1';V=R/'renders/soleil_spring_v1/spring';N=Image.Resampling.NEAREST;S=(600,600)
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def shift(im,xy):
 out=Image.new('RGBA',S);out.alpha_composite(im,xy);return out
def sheet(ims,path):
 out=Image.new('RGBA',(8*240,5*240))
 for i,im in enumerate(ims):out.alpha_composite(im.resize((240,240),N),(i%8*240,i//8*240))
 save(out,path)
y,x=np.mgrid[:600,:600];radius=((x-300)/112)**2+((y-200)/87)**2
pool=(radius<=1)&(y>=112);beam=(x>=275)&(x<325)&(y<201);beam&=~pool
mask=pool|beam
base=load(V/'01_decor.png');ba=np.array(base)
# Background completion only under the extracted glow. Keep the native shoreline intact.
water=np.zeros_like(ba);water[:]=[8,105,102,255]
water[pool,:3]=np.stack([np.full(pool.sum(),12),np.full(pool.sum(),112),np.full(pool.sum(),106)],axis=1)
for yy in range(112):water[yy,275:325]=ba[yy,250:275].repeat(2,axis=0)
clean=ba.copy();clean[mask]=water[mask];clean=Image.fromarray(clean)
# Native 3/13 shapes and timing retained; rainbow coloring is intentionally new.
lights=[];beams=[];falls=[]
for f in range(39):
 src=load(V/'frames'/f'{f:02}.png');a=np.array(src);rgb=a[:,:,:3].astype(float);lum=np.max(rgb,axis=2)
 phase=f/39;hue=(x/260+y/850-phase)%1
 # Smooth spectral colors, no flashing. Luminance/white core remain legible.
 spectral=np.stack([.5+.5*np.cos(2*math.pi*(hue-j/3)) for j in range(3)],axis=2)
 spectral=.3+.7*spectral
 spectrum=spectral*(lum[:,:,None]*.92+18)
 weight=np.where(pool,.76*np.clip((1-radius)*3,0,1),.72)
 white=np.clip((lum-200)/55,0,1)*.82;weight*=1-white
 colored=np.clip(rgb*(1-weight[:,:,None])+spectrum*weight[:,:,None],0,255).astype('uint8')
 for m,arr,name in [(pool,lights,'halo_bassin'),(beam,beams,'faisceau')]:
  b=np.zeros_like(a);b[m,:3]=colored[m];b[m,3]=255;im=Image.fromarray(b);arr.append(im);save(im,Path('commun')/name/f'{f:02}.png')
 overlay=Image.alpha_composite(load(V/'02_cycle_3'/f'{f%3:02}.png'),load(V/'03_cycle_13'/f'{f%13:02}.png'));ar=np.array(overlay);ar[mask]=0;im=Image.fromarray(ar);falls.append(im);save(im,Path('commun/eau_cascades')/f'{f:02}.png')
sheet(lights,Path('planches/halo_bassin_39.png'));sheet(beams,Path('planches/faisceau_39.png'));sheet(falls,Path('planches/eau_cascades_39.png'))
protected=Image.new('L',S);pd=ImageDraw.Draw(protected);pd.polygon([(155,0),(445,0),(465,150),(470,285),(405,340),(195,340),(130,285),(135,150)],fill=255);soft=protected.filter(ImageFilter.GaussianBlur(18));sa=np.array(soft);sa[mask]=255;soft=Image.fromarray(sa)
layouts=[('01_source_centrale','Source centrale',(0,0)),('02_source_gauche','Source décalée à gauche',(-64,0)),('03_source_droite','Source décalée à droite',(64,0)),('04_grande_clairiere','Grande clairière',(0,-32))]
manifest={'canvas':[600,600],'frames':39,'ticks_per_frame':10,'engine_hz':60,'period_ms':6500,'light':'Nouvelle coloration spectrale cyclique, pixels clairs préservés, cycle 39 phases. Ni coloration native Halcyon ni animation originale inchangée.','layouts':[]}
board=Image.new('RGB',(1200,1260),'#172b30');d=ImageDraw.Draw(board)
for j,(slug,title,xy) in enumerate(layouts):
 if j==0:decor=clean.copy()
 else:
  generated=load(O/'bruts'/f'{slug}.png').resize(S,N);orig=shift(clean,xy);m=Image.new('L',S);m.paste(soft,xy);decor=Image.composite(orig,generated,m)
 save(decor,Path(slug)/'01_decor_sans_lumiere.png')
 frames=[]
 for f in range(39):
  comp=decor.copy()
  for im in [falls[f],lights[f],beams[f]]:comp.alpha_composite(shift(im,xy))
  frames.append(comp)
  if f==0:save(comp,Path(slug)/'composition.png')
 # Per-layout first-frame layer stack; all other frames are common + translation.
 for name,arr in [('02_eau_cascades',falls),('03_halo_arc_en_ciel',lights),('04_faisceau_arc_en_ciel',beams)]:save(shift(arr[0],xy),Path(slug)/(name+'.png'))
 frames[0].save(O/slug/'animation.webp',save_all=True,append_images=frames[1:],duration=[167,167,166]*13,loop=0,lossless=True)
 board.paste(frames[8].convert('RGB'),((j%2)*600,(j//2)*630+30));d.text(((j%2)*600+12,(j//2)*630+8),title,fill='white')
 manifest['layouts'].append({'id':slug,'title':title,'offset':list(xy),'layers':['01_decor_sans_lumiere.png','02_eau_cascades.png','03_halo_arc_en_ciel.png','04_faisceau_arc_en_ciel.png']})
save(board,Path('PLANCHE_4_LAYOUTS.png'));(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('4 layouts / 39 rainbow phases / separate beam, pool halo and water')
