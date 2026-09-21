"""Sky Peak summit meadow over a sea of forest and distant mountains, night moon and cloud overlay.
Terrain/panorama: generated art guided by the native Sky Peak GIF (not native tiles).
Sky, stars, crescent moon, clouds: approved native climate sources (ciels_valides, c16efe12), unscaled.
"""
from pathlib import Path
import sys, json, hashlib, io, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, _webp
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/sky_peak_prairie_v1'
sys.path.insert(0,str(R/'source'));import ciels_valides as climate
P='SkyPeakPrairieV1';W,H=960,864;N=Image.Resampling.NEAREST
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def png(im):b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def key(im,fringe=1):
    a=np.array(im);c=a[:,:,:3].astype(int);m=(c[:,:,0]>c[:,:,1]+40)&(c[:,:,2]>c[:,:,1]+40)
    # remove magenta fringe: also drop pixels adjacent to the key whose red/blue exceed green strongly
    from scipy import ndimage
    grow=ndimage.binary_dilation(m,iterations=fringe)&(c[:,:,0]>c[:,:,1]+15)&(c[:,:,2]>c[:,:,1]+15)
    a[m|grow]=0;return Image.fromarray(a)
def nearest_fit(im,w):return im.resize((w,round(im.height*w/im.width)),N)

layers=[];meta={}
# 1 sky + 2 stars (native night sky mirrored repeat, native star/moon sheet with moon block at right)
sky=climate.sky((W,H),'nuit');stars=climate.stars((W,H),'nuit',moon=True)
# Separate the crescent moon (yellow) from the stars so moon is its own layer.
sa=np.array(stars);yellow=(sa[:,:,0]>150)&(sa[:,:,1]>130)&(sa[:,:,2]<160)&(sa[:,:,3]>0)
from scipy import ndimage
lab,n=ndimage.label(ndimage.binary_dilation(yellow,iterations=3));sizes=ndimage.sum(yellow,lab,range(1,n+1));moon_mask=lab==(int(np.argmax(sizes))+1)
moon=np.zeros_like(sa);moon[moon_mask]=sa[moon_mask];star_only=sa.copy();star_only[moon_mask]=0
moon_box=[int(v) for v in (np.where(moon_mask)[1].min(),np.where(moon_mask)[0].min(),np.where(moon_mask)[1].max()+1,np.where(moon_mask)[0].max()+1)]
# 4 panorama (generated): mountains + sea of forest, fitted by width only, no vertical distortion
pan=key(load(O/'bruts/panorama_foret_montagnes_v2.png'));pan=nearest_fit(pan,1200).crop((120,0,1080,pan.height*1200//pan.width));pan_y=H-pan.height;panorama=Image.new('RGBA',(W,H));panorama.alpha_composite(pan,(0,pan_y))  # forest sea reaches the bottom edge;panorama=Image.new('RGBA',(W,H));panorama.alpha_composite(pan,(0,pan_y))
# 5 terrain (generated plateau on magenta)
terr=key(load(O/'bruts/terrain_prairie_v2.png'),2);box=terr.getbbox();terr=terr.crop((0,box[1],terr.width,terr.height))
terr=nearest_fit(terr,672);terr_y=H-terr.height+150;terr_x=(W-terr.width)//2;terrain=Image.new('RGBA',(W,H));terrain.alpha_composite(terr,(terr_x,terr_y))
# Partition terrain into grass plateau vs rock face (visible pixels only).
ta=np.array(terrain);c=ta[:,:,:3].astype(int);grass=(c[:,:,1]>c[:,:,0]+20)&(c[:,:,1]>c[:,:,2]+10)&(ta[:,:,3]>0)
grass=ndimage.binary_closing(grass,iterations=2)&(ta[:,:,3]>0)
g=ta.copy();g[~grass]=0;rk=ta.copy();rk[grass]=0
# 6 clouds overlay: native cloud strip, wrap, graded night as in the approved helper; two speeds.
strip=climate.clouds('nuit')
def cloud_layer(offset,y,alpha):
    im=climate.wrap(strip,(W,H),offset);a=np.array(im);a[:,:,3]=(a[:,:,3].astype(int)*alpha//100).astype('uint8');im=Image.fromarray(a)
    out=Image.new('RGBA',(W,H));out.alpha_composite(im,(0,y));return out
far=cloud_layer(0,24,70);near=cloud_layer(700,120,100)  # near clouds drift over the forest sea as an overlay
comp_layers=[('01_ciel_natif',sky),('02_etoiles_natives',Image.fromarray(star_only)),('03_lune_native',Image.fromarray(moon)),('04_nuages_lointains',far),('05_panorama_montagnes_foret',panorama),('06_nuages_overlay',near),('07_plateau_herbe',Image.fromarray(g)),('08_paroi_rocheuse',Image.fromarray(rk))]
L=O/'calques';L.mkdir(parents=True,exist_ok=True)
for name,im in comp_layers:im.save(L/f'{P}_{name}.png')
(O/'calques'/f'{P}_terrain_complet.png').write_bytes(png(terrain))
strip.save(L/f'{P}_bande_nuages_native_1440.png')
def compose(t=0.0):
    out=sky.copy()
    for name,im in comp_layers[1:]:
        if name=='04_nuages_lointains':im=cloud_layer(-2*t,24,70)
        if name=='06_nuages_overlay':im=cloud_layer(700-6*t,120,100)
        out.alpha_composite(im)
    return out
comp=compose();comp.save(O/f'{P}_composition_nuit.png')
# ORA
root=ET.Element('image',w=str(W),h=str(H),version='0.0.3');stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(O/f'{P}_editable.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(name,im) in enumerate(reversed(comp_layers)):
        ET.SubElement(stack,'layer',name=name,src=f'data/{i}.png',x='0',y='0',opacity='1.0',visibility='visible');z.writestr(f'data/{i}.png',png(im))
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(comp))
# Animated preview: 24 s excerpt at 10 fps (clouds only move; full wrap period 720 s / 240 s not looped here)
enc=_webp.WebPAnimEncoder((W,H),0,0,False,9,17,False,False)
for i in range(240):enc.add(compose(i/10).getim(),i*100,True,80,100,4)
enc.add(None,24000,True,80,100,0);(O/f'{P}_extrait_nuages_24s.webp').write_bytes(enc.assemble('','',''))
# Board + manifest
board=Image.new('RGB',(W,H+40),'#10202a');board.paste(comp,(0,40));ImageDraw.Draw(board).text((12,12),'Sky Peak — prairie du sommet, nuit · terrain/panorama générés, ciel/lune/nuages natifs',fill='white');board.save(O/f'{P}_planche.png')
meta=dict(size=[W,H],layers=[n for n,_ in comp_layers],terrain_offset=[terr_x,terr_y],panorama_offset=[0,pan_y],moon_box=moon_box,clouds=dict(far=dict(y=24,speed_px_s=-2,alpha_pct=70),overlay=dict(y=120,speed_px_s=-6,alpha_pct=100),wrap_px=1440,strip='calques/'+P+'_bande_nuages_native_1440.png'),climate=climate.provenance(),generated=dict(terrain='bruts/terrain_prairie_v2.png',terrain_rejected='bruts/terrain_prairie.png',panorama='bruts/panorama_foret_montagnes_v2.png',panorama_rejected='bruts/panorama_foret_montagnes.png (ledge and stump in foreground)',guides=['source/sky_peak_prairie_v1/references/skypeak_gif_frame0.png','source/sky_peak_prairie_v1/references/reference_lune_nuages_utilisateur.png'],fit='uniform nearest resize (terrain 1024→672 wide; panorama 1376→1200 wide then centred crop 960), no distortion, magenta keyed, no recolor'),sources={str(p.relative_to(R)):sha(p) for p in sorted((S/'references').glob('*.png'))},runtime_validated=False)
(O/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('OK',W,H,'terrain at',terr_y,'panorama at',pan_y,'moon',moon_box)
