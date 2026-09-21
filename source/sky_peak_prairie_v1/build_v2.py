"""V2 (user correction): forest sea + mountains in Sky Peak rendering; sky GENERATED,
stars/moon and clouds on separate generated layers. Everything generated, magenta keyed,
uniform nearest resize only, no recolor. Terrain plateau unchanged from V1.
"""
from pathlib import Path
import json, hashlib, io, zipfile, math
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, _webp
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/sky_peak_prairie_v1';V=O/'v2'
P='SkyPeakPrairieV2';W,H=960,864;N=Image.Resampling.NEAREST
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def png(im):b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def key(im,fringe=1):
    a=np.array(im);c=a[:,:,:3].astype(int);m=(c[:,:,0]>c[:,:,1]+40)&(c[:,:,2]>c[:,:,1]+40)
    grow=ndimage.binary_dilation(m,iterations=fringe)&(c[:,:,0]>c[:,:,1]+15)&(c[:,:,2]>c[:,:,1]+15)
    a[m|grow]=0;return Image.fromarray(a)
def fit(im,w):return im.resize((w,round(im.height*w/im.width)),N)
def canvas(im,x,y):out=Image.new('RGBA',(W,H));out.alpha_composite(im,(x,y));return out
(V/'calques').mkdir(parents=True,exist_ok=True)

# 01 generated sky gradient, fitted uniformly then cropped to canvas
sky=load(O/'bruts/ciel_nuit_genere.png');sky=fit(sky,W);sky=sky.crop((0,0,W,min(H,sky.height)))
if sky.height<H:  # extend by repeating the last row (flat gradient end) rather than stretching
    ext=Image.new('RGBA',(W,H));ext.paste(sky,(0,0));ext.paste(sky.crop((0,sky.height-1,W,sky.height)).resize((W,H-sky.height),N),(0,sky.height));sky=ext
# 02 stars + 03 moon from the generated sheet (1:1, no resize; moon isolated as biggest yellow blob)
sheet=key(load(O/'bruts/etoiles_lune_generees.png'));sheet=sheet.resize((sheet.width//2,sheet.height//2),N);sa=np.array(sheet)
yellow=(sa[:,:,3]>0)&(sa[:,:,0]>150)&(sa[:,:,1]>130)&(sa[:,:,2]<200)&(sa[:,:,0]>sa[:,:,2].astype(int)+20)
lab,n=ndimage.label(ndimage.binary_dilation(yellow,iterations=2));sizes=ndimage.sum(yellow,lab,range(1,n+1));mm=lab==(int(np.argmax(sizes))+1)
mm=ndimage.binary_fill_holes(mm)&(sa[:,:,3]>0)
moon_sprite=Image.fromarray(np.where(mm[:,:,None],sa,0).astype('uint8'));mb=moon_sprite.getbbox();moon_sprite=moon_sprite.crop(mb)
stars_sheet=np.where(mm[:,:,None],0,sa).astype('uint8')
# generator drew a halo arc around the moon: clear a disc of 1.4x moon radius around its centre
ys,xs=np.where(mm);cy,cx=ys.mean(),xs.mean();rad=(xs.max()-xs.min())/2*1.5;yy,xx=np.mgrid[:sa.shape[0],:sa.shape[1]];stars_sheet[(yy-cy)**2+(xx-cx)**2<rad*rad]=0
# keep only small star blobs (drop any stray halo/arc artefacts around the moon)
sl,sn=ndimage.label(stars_sheet[:,:,3]>0);ssz=ndimage.sum(np.ones_like(sl),sl,range(1,sn+1))
for i,sz in enumerate(ssz,1):
    if sz>40 or (sz>3 and not (stars_sheet[sl==i][:,:3].min()>150)):stars_sheet[sl==i]=0  # keep only clean bright star pixels
stars_sheet=Image.fromarray(stars_sheet)
# Stars: tile the generated field (1376 wide) across the sky band without resizing; moon placed at right like the reference
stars=Image.new('RGBA',(W,H));stars.alpha_composite(stars_sheet,(0,0));stars.alpha_composite(stars_sheet,(stars_sheet.width,0))
sa2=np.array(stars);sa2[300:]=0;stars=Image.fromarray(sa2)
moon_pos=(W-180-moon_sprite.width//2,48);moon=canvas(moon_sprite,*moon_pos)
# 04/06 clouds: cut the five generated sprites, build a 1440 wrap strip at 1:1
cl=key(load(O/'bruts/nuages_generes.png'));cl=cl.resize((cl.width//2,cl.height//2),N);ca=np.array(cl);lab,n=ndimage.label(ndimage.binary_dilation(ca[:,:,3]>0,iterations=3));sprites=[]
for i in range(1,n+1):
    ys,xs=np.where(lab==i)
    if len(ys)<100:continue
    box=(xs.min(),ys.min(),xs.max()+1,ys.max()+1);sp=Image.fromarray(np.where((lab==i)[:,:,None],ca,0).astype('uint8')).crop(box);sprites.append(sp)
sprites.sort(key=lambda s:-s.width)
strip=Image.new('RGBA',(1440,120));slots=[(60,10),(520,30),(1000,6)]
for sp,(x,y) in zip(sprites[:3],slots):strip.alpha_composite(sp,(x,y))
near_strip=Image.new('RGBA',(1440,100))
for sp,(x,y) in zip(sprites[3:],[(200,20),(760,10),(1200,35)]):near_strip.alpha_composite(sp,(x,y))
_unused=[]
def cloud_layer(offset,y,alpha,src=None):
    src=src if src is not None else strip;im=Image.new('RGBA',(W,H))
    for x in range(-(int(offset)%1440),W,1440):im.alpha_composite(src,(x,y))
    a=np.array(im);a[:,:,3]=(a[:,:,3].astype(int)*alpha//100).astype('uint8');return Image.fromarray(a)
# 05 panorama Sky Peak-style (generated), uniform resize 1584→1200, centred crop 960, bottom aligned
pan=key(load(O/'bruts/panorama_skypeak_v3.png'));pan=fit(pan,1200);pan=pan.crop((120,0,1080,pan.height));pan_y=H-pan.height;panorama=canvas(pan,0,pan_y)
# 07/08 terrain: same generated plateau as V1 (unchanged geometry)
terr=key(load(O/'bruts/terrain_prairie_v2.png'),2);box=terr.getbbox();terr=terr.crop((0,box[1],terr.width,terr.height));terr=fit(terr,672);terr_y=H-terr.height+150;terr_x=(W-terr.width)//2
terrain=canvas(terr,terr_x,terr_y);ta=np.array(terrain);c=ta[:,:,:3].astype(int);grass=(c[:,:,1]>c[:,:,0]+20)&(c[:,:,1]>c[:,:,2]+10)&(ta[:,:,3]>0);grass=ndimage.binary_closing(grass,iterations=2)&(ta[:,:,3]>0)
g=ta.copy();g[~grass]=0;rk=ta.copy();rk[grass]=0
FAR=dict(y=30,speed=-2,alpha=80);NEAR=dict(y=300,speed=-6,alpha=100)
layers=[('01_ciel_genere',sky),('02_etoiles_generees',stars),('03_lune_generee',moon),('04_nuages_lointains',cloud_layer(0,FAR['y'],FAR['alpha'])),('05_panorama_skypeak_foret_montagnes',panorama),('06_nuages_overlay',cloud_layer(700,NEAR['y'],NEAR['alpha'],near_strip)),('07_plateau_herbe',Image.fromarray(g)),('08_paroi_rocheuse',Image.fromarray(rk))]
for name,im in layers:im.save(V/'calques'/f'{P}_{name}.png')
strip.save(V/'calques'/f'{P}_bande_nuages_lointains_1440.png');near_strip.save(V/'calques'/f'{P}_bande_nuages_overlay_1440.png');moon_sprite.save(V/'calques'/f'{P}_lune_sprite.png');terrain.save(V/'calques'/f'{P}_terrain_complet.png')
def compose(t=0.0):
    out=sky.copy()
    for name,im in layers[1:]:
        if name=='04_nuages_lointains':im=cloud_layer(FAR['speed']*t,FAR['y'],FAR['alpha'])
        if name=='06_nuages_overlay':im=cloud_layer(700+NEAR['speed']*t,NEAR['y'],NEAR['alpha'],near_strip)
        out.alpha_composite(im)
    return out
comp=compose();comp.save(V/f'{P}_composition_nuit.png')
root=ET.Element('image',w=str(W),h=str(H),version='0.0.3');stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(V/f'{P}_editable.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(name,im) in enumerate(reversed(layers)):ET.SubElement(stack,'layer',name=name,src=f'data/{i}.png',x='0',y='0',opacity='1.0',visibility='visible');z.writestr(f'data/{i}.png',png(im))
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(comp))
enc=_webp.WebPAnimEncoder((W,H),0,0,False,9,17,False,False)
for i in range(240):enc.add(compose(i/10).getim(),i*100,True,80,100,4)
enc.add(None,24000,True,80,100,0);(V/f'{P}_extrait_nuages_24s.webp').write_bytes(enc.assemble('','',''))
meta=dict(size=[W,H],layers=[n for n,_ in layers],terrain_offset=[terr_x,terr_y],panorama_offset=[0,pan_y],moon_position=list(moon_pos),moon_sprite_size=list(moon_sprite.size),clouds=dict(far=FAR,overlay=NEAR,wrap_px=1440,sprites=len(sprites)),generated=dict(sky='bruts/ciel_nuit_genere.png',stars_moon='bruts/etoiles_lune_generees.png',clouds='bruts/nuages_generes.png',panorama='bruts/panorama_skypeak_v3.png',terrain='bruts/terrain_prairie_v2.png',guides=['references/skypeak_horizon_native.png','references/skypeak_gif_frame0.png','references/reference_lune_nuages_utilisateur.png'],fit='uniform nearest resizes only (sky→960 wide; panorama 1584→1200 then centred crop; terrain 1024→672); stars/moon/cloud sheets halved uniformly (generator drew at 2× pixel scale); magenta keyed; no recolor'),bruts_sha256={p.name:sha(p) for p in sorted((O/'bruts').glob('*.png'))},all_pixels_generated=True,runtime_validated=False)
(V/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('OK v2; panorama at',pan_y,'terrain at',(terr_x,terr_y),'moon',moon_pos,moon_sprite.size,'clouds',len(sprites))
