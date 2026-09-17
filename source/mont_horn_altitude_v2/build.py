"""Reference-guided Mt Horn redesign. Generated art, independent masks, periodic cloud overlays."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/mont_horn_altitude_v2';OLD=R/'renders/mont_horn_panorama_v1';P=O/'mont_horn';S=O/'sprites';P.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=648,504;N=324;DT=320;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,mask):
 b=a.copy();b[~mask]=0;return Image.fromarray(b)
def merge(layers):
 im=Image.new('RGBA',(W,H))
 for name,l in layers:im.alpha_composite(l)
 return im
# Keep the mountain panorama visible in both outer thirds; narrower foreground ridge.
bg=load(OLD/'bruts/panorama.png').resize((W,H),NN);bg=bg.convert('RGB').quantize(colors=80,method=Image.Quantize.MEDIANCUT).convert('RGBA')
# Separate complete sky and distant mountain cutout. Only the upper distant chains survive.
a=np.array(bg);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
maybe_sky=(r<115)&(b>g+32)
sky_region=nd.binary_propagation(np.indices((H,W))[0]==0,mask=maybe_sky)
mountain=np.zeros_like(a);mountain[:245]=a[:245]
mountain[sky_region]=0
fade=np.clip((245-yy)/70,0,1)
mountain[:,:,3]=np.rint(mountain[:,:,3]*fade*.80).astype('uint8')
mountain[:,:,:3]=np.rint(mountain[:,:,:3]*.62+np.array([189,215,232])*.38).astype('uint8')
mountain[mountain[:,:,3]==0]=0
mountains=Image.fromarray(mountain)
# Opaque sky extends behind every other layer, no mountain silhouettes baked into it.
f=np.clip(yy/330,0,1);f=np.round(f*32)/32
skyarr=np.zeros((H,W,4),dtype='uint8')
skyarr[:,:,:3]=np.rint(np.array([92,179,232])[None,None,:]*(1-f[:,:,None])+np.array([213,231,240])[None,None,:]*f[:,:,None]).astype('uint8');skyarr[:,:,3]=255
sky=Image.fromarray(skyarr)
# Sparse, pale atmospheric banks below the distant horizon, not another foreground range.
mist=np.zeros_like(skyarr);mist[:,:,:3]=[230,241,245]
wave=15*np.sin(xx/89)+7*np.sin(xx/37)
ma=np.clip((yy-195-wave)/230,0,1)*.52
mist[:,:,3]=np.rint(ma*255).astype('uint8');mist[mist[:,:,3]==0]=0
atmosphere=Image.fromarray(mist)
# Opaque altitude haze conceals the side massif's lower termination, leaving the approach readable.
fp=np.clip((np.abs(xx-324)-62)/60,0,1);fp=fp*fp*(3-2*fp)
fstart=250+20*np.sin(xx/57)+80*np.exp(-((xx-324)/125)**2)
fa0=np.clip((yy-fstart)/110,0,1);fa0=fa0*fa0*(3-2*fa0)
fogarr=np.zeros_like(skyarr);fogarr[:,:,:3]=[222,236,243];fogarr[:,:,3]=np.rint(fp*fa0*255).astype('uint8');fogarr[fogarr[:,:,3]==0]=0
fog=Image.fromarray(fogarr)
background=[('01a_ciel',sky),('01b_montagnes_lointaines',mountains),('01c_brume_horizon',atmosphere)]
fg0=key(load(OLD/'bruts/relief_magenta.png')).resize((432,H),NN);fg=Image.new('RGBA',(W,H));fg.alpha_composite(fg0,(108,0));fa=np.array(fg);visible=fa[:,:,3]>0
r,g,b=fa[:,:,:3].astype(float).transpose(2,0,1)
# Recolored warm road keeps its luminance but belongs to the same gray-stone family.
warm=(r>=g*.995)&(g>b*1.025)&visible;lum=(r*.2126+g*.7152+b*.0722)
for j,factor in enumerate([1.01,1.,.97]):fa[:,:,j][warm]=np.clip(lum[warm]*factor,0,255).astype('uint8')
fg=Image.fromarray(fa)
entry=visible&(yy<240)&(np.abs(xx-324)<(114+yy*.13))
path=visible&warm&~entry
# Close tiny cobble-line holes inside the road selection, never outside foreground.
path=nd.binary_fill_holes(nd.binary_closing(path,iterations=1))&visible&~entry
path[-1]=warm[-1]&visible[-1]&~entry[-1]
left=visible&~entry&~path&(xx<324);right=visible&~entry&~path&~left
masks={'03_falaises_gauches':left,'04_falaises_droites':right,'05_chemin_pierre_grise':path,'06_entree_nord_et_marches':entry}
terrain=[(name,cut(fa,mask)) for name,mask in masks.items()]
assert np.array_equal(np.array(merge(terrain)),fa)
# Four separately generated cloud motifs, keyed before resizing; no native-animation claim.
cloudsheet=key(load(OLD/'bruts/nuages_magenta.png'));ca=np.array(cloudsheet);rowcount=(ca[:,:,3]>0).sum(axis=1);active=rowcount>12;spans=nd.find_objects(nd.label(active)[0]);assert len(spans)==4,len(spans)
clouds=[]
for k,(sl,) in enumerate(spans):
 im=cloudsheet.crop((0,sl.start,cloudsheet.width,sl.stop));im=im.crop(im.getbbox());w=[214,244,230,288][k];im=im.resize((w,round(im.height*w/im.width)),NN);im.save(S/f'horn_nuage_motif_{k:02}.png');clouds.append(im)
def strip(placements,opacity):
 im=Image.new('RGBA',(W,H))
 for k,x,y in placements:
  c=clouds[k].copy();aa=np.array(c);aa[:,:,3]=(aa[:,:,3].astype(float)*opacity).astype('uint8');aa[:,:,:3]=np.maximum(aa[:,:,:3],[184,208,219]);aa[aa[:,:,3]==0]=0;c=Image.fromarray(aa)
  for shift in [-W,0,W]:im.alpha_composite(c,(x+shift,y))
 return im
back=strip([(0,34,68),(1,407,98),(2,219,183)],.58);front=strip([(3,-110,302),(3,281,377),(1,469,250)],.27)
back.save(S/'horn_nuages_lointains_texture_wrap.png');front.save(S/'horn_nuages_overlay_texture_wrap.png')
# Overlay passes in front of side cliffs, with continuous spatial fading before the route/door.
protect=np.clip((np.abs(xx-324)-65)/90,0,1);protect=protect*protect*(3-2*protect)
Image.fromarray(np.rint(protect*255).astype('uint8')).save(O/'MASQUE_VISIBILITE_OVERLAY.png')
def cloud_layers(phase):
 far=Image.fromarray(np.roll(np.array(back),2*phase,axis=1));a=np.roll(np.array(front),4*phase,axis=1);a[:,:,3]=np.rint(a[:,:,3]*protect).astype('uint8');a[a[:,:,3]==0]=0
 return [('02_nuages_lointains',far),('07_nuages_overlay',Image.fromarray(a))]
def layers(phase):
 c=cloud_layers(phase);return background+[c[0]]+terrain+[('06b_brume_altitude_pied_masque',fog),c[1]]
for name,im in background+terrain+[('06b_brume_altitude_pied_masque',fog)]:im.save(P/f'horn_{name}.png')
frames=[]
for k in range(N):
 ls=layers(k)
 for name,im in cloud_layers(k):im.save(P/f'horn_{name}_{k:03}.png')
 im=merge(ls);assert np.all(np.array(im)[:,:,3]==255);frames.append(im)
 if k%40==0:im.save(P/f'horn_composition_cle_{k:03}.png')
frames[0].save(P/'COMPOSITION.png');frames[0].save(P/'ANIMATION_WRAP.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True,method=4)
assert all(np.array_equal(np.array(a[1]),np.array(b[1])) for a,b in zip(cloud_layers(0),cloud_layers(N)))
assert np.array_equal(np.roll(np.array(cloud_layers(N-1)[0][1]),2,axis=1),np.array(cloud_layers(0)[0][1]))
# Authored approach guide (not inferred collisions): continuous, unobscured 24px line into the cave.
route=[(324,503),(323,438),(310,388),(323,340),(338,294),(323,263),(324,228),(324,195),(324,164)]
walk=Image.new('L',(W,H));ImageDraw.Draw(walk).line(route,fill=255,width=24,joint='curve');wm=np.array(walk)>0;assert np.all(visible[wm]);assert np.all(protect[wm]==0);walk.save(O/'GUIDE_APPROCHE_24PX.png')
assert visible[:,:108].sum()==0 and visible[:,540:].sum()==0
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'mont_horn_panorama.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(layers(0)))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
m={'size':[W,H],'reference':'Mt_Horn_entrance_Sky.png','source_size':list(load(R/'Mt_Horn_entrance_Sky.png').size),'art_origin':'AI-generated reference-guided redesign, not native sprite recovery','foreground_resize':[432,H],'foreground_origin':[108,0],'static_layers':[n for n,_ in background+terrain+[('06b_brume_altitude_pied_masque',fog)]], 'layer_order':[n for n,_ in layers(0)], 'parent':'mont_horn_panorama_v1', 'mountain_alpha_zero_below_y':245,'animated_groups':['02_nuages_lointains','07_nuages_overlay'],'frames':N,'frame_ms':DT,'loop_ms':N*DT,'wrap_width':W,'shift_pixels_per_frame':[2,4],'velocities_px_second':[6.25,12.5],'overlay_blend':'normal source-over, alpha <=69, spatial fade to zero over path/cave','route_guide':route,'segmentation':'disjoint masks partition generated foreground; independent aligned scene layers, not invented hidden surfaces','runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(im):return 'data:image/png;base64,'+base64.b64encode(png(im)).decode()
assets={n:uri(im) for n,im in background+terrain+[('06b_brume_altitude_pied_masque',fog)]};assets['back']=uri(back);assets['front']=uri(front)
# Live browser uses same periodic textures and mask, stepping at exported animation cadence.
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Mont Horn · route du nord</title><style>body{background:#182631;color:#e5edf1;max-width:1100px;margin:30px auto;padding:0 20px;font:16px system-ui}h1{color:#cce5ef}p{line-height:1.6}canvas,img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#2c3d49 0 25%,#364d59 0 50%) 0/16px 16px}button,select{padding:10px;background:#344e60;color:white;border:1px solid #7b9cae;margin:6px}input{width:200px}</style><h1>Mont Horn · haute altitude · V2</h1><p>Ciel et montagnes lointaines séparés. Reliefs rapprochés retirés du panorama ; le bas se perd dans une brume d’altitude qui masque le pied du massif. Nuages lointains et voile d’altitude en calques indépendants : défilement horizontal avec wrap, boucle de 103,68 secondes. Le chemin et la porte restent dégagés.</p><button id="play">Pause</button><select id="sel"><option value="all">Composition animée</option><option value="clean">Sans nuages</option></select><input id="phase" type="range" min="0" max="323" value="0"><span id="counter"></span><br><canvas id="view" width="648" height="504"></canvas><p>Nouvelle disposition générée à partir de la référence PMD, détourée puis découpée en calques. Ce n’est pas une extraction native de cette nouvelle entrée. PNG, ORA, animation et scripts fournis ; pas de validation dans PMDO.</p><script>const src='''+json.dumps(assets)+''';const names='''+json.dumps([n for n,_ in layers(0)])+''';const ims={};const ctx=view.getContext('2d');ctx.imageSmoothingEnabled=false;let running=true,k=0,last=0;names.forEach(n=>sel.add(new Option(n,n)));function drawCloud(key,dx,overlay){const c=document.createElement('canvas');c.width=648;c.height=504;let x=c.getContext('2d');for(let i=-1;i<=1;i++)x.drawImage(ims[key],dx%648+i*648,0);if(overlay){let d=x.getImageData(0,0,648,504);for(let y=0;y<504;y++)for(let z=0;z<648;z++){let a=Math.max(0,Math.min(1,(Math.abs(z-324)-65)/90));a=a*a*(3-2*a);d.data[(y*648+z)*4+3]=Math.round(d.data[(y*648+z)*4+3]*a)}x.putImageData(d,0,0)}ctx.drawImage(c,0,0)}function render(){ctx.clearRect(0,0,648,504);for(const n of names){if(sel.value!=='all'&&sel.value!=='clean'&&sel.value!==n)continue;if(n==='02_nuages_lointains'){if(sel.value!=='clean')drawCloud('back',k*2,false)}else if(n==='07_nuages_overlay'){if(sel.value!=='clean')drawCloud('front',k*4,true)}else ctx.drawImage(ims[n],0,0)}phase.value=k;counter.textContent=(k*.32).toFixed(2)+' /103,68 s'}Promise.all(Object.entries(src).map(([n,s])=>new Promise(ok=>{let im=new Image;im.onload=()=>{ims[n]=im;ok()};im.src=s}))).then(()=>{render();requestAnimationFrame(tick)});function tick(t){if(running&&t-last>=320){k=(k+Math.floor((t-last)/320))%324;last=t;render()}if(!running)last=t;requestAnimationFrame(tick)}play.onclick=()=>{running=!running;play.textContent=running?'Pause':'Reprendre'};phase.oninput=()=>{running=false;play.textContent='Reprendre';k=+phase.value;render()};sel.onchange=render;</script>'''
(R/'apercu_mont_horn_altitude_v2.html').write_text(html)
print('Built',N,'frames;',N*DT,'ms; 10 layers, 2 independently wrapping cloud layers')
