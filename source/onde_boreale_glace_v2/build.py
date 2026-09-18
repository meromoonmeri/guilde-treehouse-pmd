"""Nouvelle onde générée seule, puis couleurs mobiles + ondulation ±2 px.
Les terrains et le climat validés de V1 ne sont jamais régénérés.
"""
from pathlib import Path
import sys,json,hashlib,shutil,colorsys,io,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
OUT=ROOT/'renders/onde_boreale_glace_v2';V1=ROOT/'renders/entrees_glace_v1'
sys.path.insert(0,str(ROOT/'source'));import ciels_valides as climate
SIZE=(768,640);W,H=SIZE;N=32;MS=125
RAW=OUT/'bruts/onde_pmd_magenta.png'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def blank():return Image.new('RGBA',SIZE)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def webp(frames,p,loop=0):
 p.parent.mkdir(parents=True,exist_ok=True)
 frames[0].save(p,format='WEBP',save_all=True,append_images=frames[1:],duration=MS,loop=loop,lossless=True,exact=True,method=4)
def ora(p,layers):
 root=ET.Element('image',w=str(W),h=str(H),name=p.stem,version='0.0.3');stack=ET.SubElement(root,'stack');merged=blank()
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers.items()):z.writestr(f'data/layer{i}.png',png(im));merged.alpha_composite(im)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):ET.SubElement(stack,'layer',name=name,src=f'data/layer{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'));z.writestr('mergedimage.png',png(merged))
  thumb=merged.copy();thumb.thumbnail((256,256),Image.Resampling.NEAREST);z.writestr('Thumbnails/thumbnail.png',png(thumb))

def extract():
 rgb=np.array(load(RAW))[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1)
 # The prompt deliberately bans pure magenta IN the ribbon. Remove key pixels
 # also from internal gaps, not only edge-connected background.
 key=(r>g*1.35)&(b>g*1.35)&(r>120)&(b>130)
 labels,_=ndimage.label(~key);counts=np.bincount(labels.ravel());ids=np.flatnonzero((counts>=30)&(np.arange(len(counts))!=0))
 keep=np.isin(labels,ids)
 lum=rgb@np.array([.2126,.7152,.0722])
 alpha=np.rint(np.clip((lum-34)/180,0,1)**1.2*220).astype('uint8');alpha[~keep]=0
 # Fade the hard generated ends, without changing positions or painting sky.
 ys,xs=np.where(alpha>0);xmin,xmax=xs.min(),xs.max()
 edge=np.clip(np.minimum(np.arange(rgb.shape[1])-xmin,xmax-np.arange(rgb.shape[1]))/60,0,1)
 alpha=np.rint(alpha*edge[None,:]).astype('uint8')
 a=np.dstack([rgb,alpha]).astype('uint8');a[a[:,:,3]==0]=0
 effect=Image.fromarray(a);box=effect.getbbox();crop=effect.crop(box);before=crop.size
 crop.thumbnail((672,168),Image.Resampling.NEAREST)
 out=blank();xy=((W-crop.width)//2,14);out.paste(crop,xy)
 return out,{'source_size':list(effect.size),'crop_xyxy':box,'crop_size':list(before),'normalized_size':list(crop.size),'offset_xy':list(xy),'method':'Recadrage de l’effet, normalisation uniforme nearest vers maximum672×168, alpha dérivé de luminance ; ciel jamais peint.'}

def shift_for(frame):
 t=(frame%N)/N;x=np.arange(W)
 envelope=np.minimum(1,np.minimum(x/64,(W-1-x)/64))
 return np.rint(envelope*(1.5*np.sin(2*np.pi*(x/448-t))+.5*np.sin(2*np.pi*(x/176+t)))).astype(int)

def render(index,alpha,palettes,frame):
 rgb=np.array(palettes[frame%N],dtype='uint8')[index]
 a=np.dstack([rgb,alpha]);a[alpha==0]=0;out=np.zeros_like(a)
 for x,dy in enumerate(shift_for(frame)):
  if dy>0:out[dy:,x]=a[:-dy,x]
  elif dy<0:out[:dy,x]=a[-dy:,x]
  else:out[:,x]=a[:,x]
 out[out[:,:,3]==0]=0
 return Image.fromarray(out)

def build():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'aurore').mkdir(exist_ok=True)
 master,norm=extract();save(master,OUT/'aurore/GLACE_BOREALE_V2_dessin_detoure.png')
 a=np.array(master);alpha=a[:,:,3];mask=alpha>0
 # 32 texture colors × 8 spatial phase bands = 256 fixed indices.
 pixels=Image.fromarray(a[:,:,:3][mask][None,:,:]);q=pixels.quantize(colors=32,method=Image.Quantize.MEDIANCUT)
 palette=np.array(q.getpalette(),dtype='uint8').reshape(-1,3)[:32]
 fixed=Image.fromarray(a[:,:,:3]).quantize(palette=q,dither=Image.Dither.NONE)
 base_idx=np.array(fixed);phase_band=(np.arange(W)*8//W).clip(0,7)
 index=(base_idx.astype(int)+phase_band[None,:]*32).astype('uint8');index[~mask]=0
 palettes=[]
 for f in range(N):
  lut=[]
  for band in range(8):
   wave=np.sin(2*np.pi*(f/N-band/8))
   for color in palette:
    h,s,v=colorsys.rgb_to_hsv(*(color.astype(float)/255))
    # A traveling cyan/green/blue-violet hue shift, no global luminance flash.
    h=(h+.115*wave)%1
    c=colorsys.hsv_to_rgb(h,s,v)
    lut.append([int(round(255*channel)) for channel in c])
  palettes.append(lut)
 indexed=Image.fromarray(index).convert('P');indexed.putpalette(np.array(palettes[0]).ravel().tolist())
 save(indexed,OUT/'aurore/GLACE_BOREALE_V2_indices.png');save(Image.fromarray(alpha),OUT/'aurore/GLACE_BOREALE_V2_alpha.png')
 (OUT/'aurore/GLACE_BOREALE_V2_palettes.json').write_text(json.dumps({'frame_ms':MS,'frames':palettes,'index_rule':'couleur_base0..31 + 32*bande_de_phase0..7','hue_variation_turns':.115,'value_and_saturation':'fixed per original color','wave_displacement_px':[shift_for(f).tolist() for f in range(N)]},ensure_ascii=False)+'\n')
 frames=[render(index,alpha,palettes,f) for f in range(N)]
 frame_paths=[]
 for f,im in enumerate(frames):
  p=OUT/'aurore'/f'GLACE_BOREALE_V2_onde_{f:02d}.png';save(im,p);frame_paths.append(str(p.relative_to(OUT)))
 webp(frames,OUT/'aurore/GLACE_BOREALE_V2_onde_transparente.webp')
 prior=json.loads((V1/'manifest.json').read_text());pins=[];shared={}
 def copy(src,dest):
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  pins.append({'source':str(src.relative_to(ROOT)),'output':str(dest.relative_to(OUT)),'sha256':sha(src)})
 for key,rel in prior['shared'].items():
  src=V1/rel;dst=OUT/'climat'/src.name;copy(src,dst);shared[key]=str(dst.relative_to(OUT))
 night_sky=load(OUT/shared['nuit_ciel']);stars=load(OUT/shared['nuit_etoiles']);cloudstrip=load(OUT/shared['nuit_nuages_bande'])
 cloud0=climate.wrap(cloudstrip,SIZE)
 skyframes=[]
 for f in frames:
  scene=night_sky.copy();scene.alpha_composite(stars);scene.alpha_composite(f);skyframes.append(scene)
 webp(skyframes,OUT/'GLACE_BOREALE_V2_sur_ciel_nuit.webp')
 save(skyframes[0],OUT/'GLACE_BOREALE_V2_sur_ciel_nuit.png')
 zones=[]
 for old in prior['zones']:
  slug=old['id'];folder=OUT/slug;folder.mkdir(exist_ok=True);prefix='GLACE_BOREALE_V2_'+slug
  planes={}
  for mode in ['jour','nuit']:
   planes[mode]={}
   for name,rel in old['layers'][mode].items():
    dest=folder/f'{prefix}_{name}_{mode}.png';copy(V1/rel,dest);planes[mode][name]=str(dest.relative_to(OUT))
  day=folder/f'{prefix}_scene_jour.png';copy(V1/old['files']['scene_jour'],day)
  nightplanes=[load(OUT/p) for p in planes['nuit'].values()]
  terrain=blank()
  for plane in nightplanes:terrain.alpha_composite(plane)
  scenes=[];paths=[]
  for f,skyframe in enumerate(skyframes):
   s=skyframe.copy();s.alpha_composite(terrain);s.alpha_composite(cloud0);scenes.append(s)
   p=folder/'frames_nuit'/f'{prefix}_scene_{f:02d}.png';save(s,p);paths.append(str(p.relative_to(OUT)))
  webp(scenes,folder/f'{prefix}_boucle_onde.webp')
  save(scenes[0],folder/f'{prefix}_scene_nuit.png')
  # A real-time excerpt plays ONCE: native cloud speed without a false short loop.
  clip=[]
  for k in range(N*2):
   s=skyframes[k%N].copy();s.alpha_composite(terrain)
   s.alpha_composite(climate.wrap(cloudstrip,SIZE,offset=int(k*MS*4/1000)));clip.append(s)
  webp(clip,folder/f'{prefix}_nuages_wrap_extrait_8s.webp',loop=1)
  layers={'00_ciel_nuit_valide':night_sky,'00b_etoiles':stars,'00c_nouvelle_onde_couleur_ondulation':frames[0]}
  layers.update({name:im for name,im in zip(planes['nuit'],nightplanes)})
  layers['06_nuages_wrap_overlay']=cloud0
  ora(folder/f'{prefix}_nuit.ora',layers)
  zones.append({'id':slug,'title':old['title'],'size':list(SIZE),'layers':planes,'scene_jour':str(day.relative_to(OUT)),'scene_nuit':f'{slug}/{prefix}_scene_nuit.png','webp_loop':f'{slug}/{prefix}_boucle_onde.webp','webp_cloud_excerpt':f'{slug}/{prefix}_nuages_wrap_extrait_8s.webp','ora_nuit':f'{slug}/{prefix}_nuit.ora','frames_nuit':paths,'route_centerline':old['route_centerline'],'threshold_xy':old['threshold_xy']})
 manifest={'title':'Onde boréale générée — couleurs et légère ondulation','date':'2026-09-18','canvas':list(SIZE),'raw':str(RAW.relative_to(OUT)),'raw_sha256':sha(RAW),'references':[{'path':'aurorepmdsky.png','sha256':sha(ROOT/'aurorepmdsky.png')}],'master_normalization':norm,'shared':shared,'preserved_files':pins,'aurora':{'frames':frame_paths,'frame_ms':MS,'period_ms':N*MS,'colors':'LUT de 256 entrées, 32 teintes du dessin × 8 groupes de phase spatiale ; rotation douce de teinte ±0,115 tour, HSV valeur/saturation fixes.','wave':'dy(x,t)=round(enveloppe*(1,5 sin(2π(x/448−t/32))+0,5 sin(2π(x/176+t/32))))','displacement_max_px':2,'horizontal_translation_px':0,'generated_drawings_used':1,'transparent_webp':'aurore/GLACE_BOREALE_V2_onde_transparente.webp','on_approved_sky_webp':'GLACE_BOREALE_V2_sur_ciel_nuit.webp'},'clouds':{'strip_width':1440,'speed_px_s':-4,'period_ms':360000,'loop_webps':'Nuages fixes phase0 : seules couleur et onde bouclent sur4s.','excerpt_webps':'64frames×125ms=8s, nuages en vrai wrap à−4px/s, une seule lecture ; pas de saut de raccord masqué.','viewer':'Wrap continu 360s indépendant de l’aurore4s, tous deux bouclent exactement en360s.'},'zones':zones,'limits':['Nouveau dessin généré référencé PMD, pas texture native ni cycle officiel extrait.','Les trois layouts et leurs dix plans terrain jour/nuit sont copiés byte-identiques de V1.','Ciels, étoiles et six familles de nuages validés copiés byte-identiques ; aucun ciel V3/Caps.','32 frames animées issues d’un seul dessin ; pas32dessins générés.','Pas de collisions/warp/Ground/rendu moteur nouveau.']}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 board=Image.new('RGB',(1560,1190),'#101d2b');d=ImageDraw.Draw(board)
 font=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
 d.text((24,16),'UNE ONDE / COULEURS + ONDULATION LÉGÈRE',font=font(27),fill='#e7f0ee')
 d.text((24,57),'Ciel nocturne validé · terrains V1 conservés · 32 frames / 4 secondes',font=font(18),fill='#acc5d3')
 for j,f in enumerate([0,8,16,24]):
  im=skyframes[f].crop((0,0,W,224));im.thumbnail((368,180),Image.Resampling.NEAREST)
  board.paste(im,(24+j*384,110));d.text((24+j*384,89),f'Phase {f:02d}',font=font(14),fill='white')
 for i,z in enumerate(zones):
  im=load(OUT/z['scene_nuit']);im.thumbnail((488,420),Image.Resampling.NEAREST)
  x=24+i*514;board.paste(im,(x,375));d.text((x,339),z['title'],font=font(20),fill='#e7f0ee')
 # Effect only, checker background, actual pixels at1×.
 y=870
 for cy in range(224):
  for cx in range(0,768,16):
   shade='#273443' if ((cy//16)+(cx//16))%2 else '#344653'
   d.line((24+cx,y+cy,24+cx+15,y+cy),fill=shade)
 overlay=frames[0].crop((0,0,W,224));board.paste(overlay,(24,y),overlay)
 d.text((830,880),'Onde seule : alpha réel, aucun ciel',font=font(20),fill='#e7f0ee')
 d.text((830,919),'Déplacement vertical : maximum ±2 px',font=font(17),fill='#acc5d3')
 d.text((830,956),'Pas de scroll ni de wrap de l’aurore',font=font(17),fill='#acc5d3')
 d.text((24,1140),'Dessin généré référencé PMD. Pas le cycle officiel du jeu ; validation artistique et moteur à faire.',font=font(18),fill='#acc5d3')
 save(board,OUT/'PLANCHE_ONDE_ET_TROIS_ZONES.png')
 print('Nouvelle onde32frames + trois compositions PNG/WebP, terrains et ciel conservés.')

if __name__=='__main__':build()
