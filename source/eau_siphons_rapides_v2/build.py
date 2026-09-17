"""Fast inward water, palette cycling, wet rock borders and a south approach. No PMDO simulation."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/eau_siphons_rapides_v2';P=O/'eau_siphons_rapides';P.mkdir(parents=True,exist_ok=True)
OLD=R/'renders/corrections_eau_canopy_v1/eau_integrale_rochers_gris'
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=456,384;N=48;DT=40;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def rgba(rgb,alpha):
 a=np.zeros((H,W,4),dtype='uint8');a[:,:,:3]=rgb;a[:,:,3]=alpha;a[a[:,:,3]==0]=0;return Image.fromarray(a)
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im)
 return c
# Three original rock layers remain aligned, now in wet slate-blue tones.
static=[]
for name in ['04_rochers_arriere','05_rochers_avant','06_galet_decale']:
 a=np.array(load(OLD/f'eau_integrale_rochers_gris_{name}.png'));lum=a[:,:,:3]@np.array([.2126,.7152,.0722])
 for j,(mul,off) in enumerate([(.69,2),(.84,9),(.94,15)]):a[:,:,j]=np.clip(lum*mul+off,0,255).astype('uint8')
 a[a[:,:,3]==0]=0;static.append((name,Image.fromarray(a)))
# Isolated generated causeway is fitted to the south entrance and the principal whirlpool rim.
q=key(load(O/'bruts/chaussee_magenta.png'));q=q.crop(q.getbbox()).resize((94,208),NN)
bridge=Image.new('RGBA',(W,H));bridge.alpha_composite(q,(184,176));a=np.array(bridge);bm=a[:,:,3]>0
# Keep colors sober and close to the existing blue-gray rock palette.
lum=a[:,:,:3]@np.array([.2126,.7152,.0722])
for j,(mul,off) in enumerate([(.74,0),(.88,6),(.98,11)]):a[:,:,j]=np.clip(lum*mul+off,0,255).astype('uint8')
a[~bm]=0;bd=nd.distance_transform_edt(bm);static += [('07_chaussee_surface',part(a,bd>=8)),('08_chaussee_rebords',part(a,bm&(bd<8)))]
walk=bd>=12;labels,_=nd.label(walk);south=set(labels[-1])-{0};target=walk&(yy<205);assert any(np.any((labels==lab)&target) for lab in south)
Image.fromarray((walk*255).astype('uint8')).save(O/'masque_approche_sud_palier.png')
solid=np.maximum.reduce([np.array(im)[:,:,3] for _,im in static])>0
for name,im in static:im.save(P/f'siphons_v2_{name}.png')
source=[load(OLD/f'eau_integrale_rochers_gris_02_siphons_{i:03}.png') for i in range(6)];wet=np.array(source[0])[:,:,3]>0
labs,_=nd.label(wet);centers=[(272,20,46),(128,68,46),(231,144,77),(332,163,19),(80,197,46),(400,197,30),(156,184,11),(292,224,11)]
# Coordinate fields centered on each source basin. The principal basin is the walking destination.
fields=[]
for cx,cy,rad in centers:
 dx=xx-cx;dy=(yy-cy)/.78;rho=np.hypot(dx,dy);theta=np.arctan2(dy,dx);fields.append((rho,theta))
dominant=np.argmin(np.stack([f[0]/(r**.65) for f,(_,_,r) in zip(fields,centers)]),axis=0)
rho=np.choose(dominant,[f[0] for f in fields]);theta=np.choose(dominant,[f[1] for f in fields])
# Fixed-index wave field, with its blue-cyan palette rotated every frame (true LUT palette cycling).
index=np.floor((rho*.035-theta*.25)%1*24).astype(int)
palette=[]
for j in range(24):
 bright=(1+np.cos(2*np.pi*j/24))/2
 palette.append([13+int(8*bright),94+int(19*bright),135+int(21*bright)])
palette=np.array(palette,dtype='uint8')
# Seeded spiral streamlets travel inwards; each respawns invisibly at zero opacity on a periodic trajectory.
rng=np.random.default_rng(228);particles=[]
for k,(cx,cy,rad) in enumerate(centers):
 count=135 if k==2 else (42 if rad>35 else 12)
 for _ in range(count):
  particles.append((k,float(rng.uniform(0,2*np.pi)),float(rng.uniform(0,1)),float(rng.uniform(rad*1.5,rad*(4.2 if k==2 else 3))),int(rng.choice([1,2,3]))))
shore=nd.distance_transform_edt(~solid);inner=nd.distance_transform_edt(solid);border=(shore>0)&(shore<5)&~solid;reflection=solid&(inner<6)
# Water layers are below all rocks and the dry causeway. Wet reflections affect only their rims.
shadow=rgba([7,35,62],np.rint(np.clip((8-shore)/8,0,1)*(~solid)*75).astype('uint8'));shadow.save(P/'siphons_v2_03_ombres_contact.png')
static=[('03_ombres_contact',shadow)]+static
names=['01_eau_palette_cycling','02_courants_aspiration','03_spirales_siphons','04_ecume_bordures','09_reflets_rochers']
groups={n:[] for n in names};frames=[];frame_layers=[]
for i in range(N):
 t=i/N
 water=Image.fromarray(palette[(index+2*i)%24]).convert('RGBA')
 streams=Image.new('RGBA',(W,H));d=ImageDraw.Draw(streams)
 for k,ang,offset,reach,speed in particles:
  p=(t*speed+offset)%1
  if p<.04 or p>.96:continue
  cx,cy,rad=centers[k];points=[]
  for z in np.linspace(max(0,p-.032),p,4):
   r=reach*(1-z)**.68;th=ang+5*z+2*z*z;points.append((round(cx+r*np.cos(th)),round(cy+.78*r*np.sin(th))))
  alpha=round(155*max(0,min(1,(p-.04)*10,(.96-p)*10)));d.line(points,fill=(95,210,228,alpha),width=1 if k!=2 else 2)
 # The basin cone shading is retained, but a directional rotating/inward spiral is added to the native six poses.
 basin=np.array(source[i%6]);col=basin[:,:,:3].astype(float)
 spiral=np.zeros((H,W),float)
 for k,(rr,th) in enumerate(fields,1):
  band=(np.cos(3*th-.29*rr-2*np.pi*8*t)+1)/2
  spiral[labs==k]=band[labs==k]
 strength=np.clip((spiral-.74)/.26,0,1)*.57
 col=col*(1-strength[:,:,None])+np.array([167,251,251])*strength[:,:,None]
 basin[:,:,:3]=np.rint(col).astype('uint8');basin[basin[:,:,3]==0]=0;siphon=Image.fromarray(basin)
 # Foam pulses and travels along the contact contour; unlike the first version there is no static pale outline.
 wave=(np.sin(xx*.22+yy*.31-2*np.pi*8*t)+1)/2
 alpha=np.rint(border*(.25+.75*wave)*np.clip((5-shore)/4,0,1)*220).astype('uint8');foam=rgba([139,232,245],alpha)
 ra=np.rint(reflection*np.clip((6-inner)/5,0,1)*(20+65*wave)).astype('uint8');ref=rgba([44,162,201],ra)
 ims=[water,streams,siphon,foam,ref]
 for name,im in zip(names,ims):groups[name].append(im);im.save(P/f'siphons_v2_{name}_{i:03}.png')
 ls=list(zip(names[:4],ims[:4]))+static+[(names[4],ref)];c=compose(ls);assert np.all(np.array(c)[:,:,3]==255);c.save(P/f'siphons_v2_scene_{i:03}.png');frames.append(c)
 if i==0:frame_layers=ls;c.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,lossless=True,loop=0)
# OpenRaster preserves all layers at frame zero.
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'eau_siphons_rapides.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(frame_layers))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'eau_siphons_rapides.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');c=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(c),np.array(frames[0]))
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'static_layers':[n for n,_ in static],'animation_groups':names,'render_order':names[:4]+[n for n,_ in static]+[names[4]],'destination':{'main_whirlpool_center':[231,144],'landing_top_y':176,'safe_approach_mask':'masque_approche_sud_palier.png'},'motion':{'clockwise_inward_streamlets':len(particles),'particle_periods_ms':[1920,960,640],'spiral_period_ms':240,'native_six_pose_cycle_accelerated_ms':240,'palette_entries':24,'palette_shift_per_frame':2,'wet_foam_period_ms':240},'tests':{'opaque_all_frames':True,'ora_exact':True,'south_to_landing_connected_24px_interior':True,'water_hidden_beneath_dry_causeway':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Viewer: separately inspect animated water, inward trails, spiral, shoreline, rock reflections and static layers.
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for name,ims in groups.items():
 b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=DT,lossless=True,loop=0);items.append({'name':name,'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Siphons — courants rapides et passage</title><style>body{background:#0d202b;color:#d4edf1;font:16px system-ui;max-width:1000px;margin:28px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;width:684px;background:repeating-conic-gradient(#25404b 0 25%,#355563 0 50%) 0/16px 16px}select,button{padding:10px;background:#163f50;color:white;border:1px solid #4991aa;margin:8px}input{width:220px}</style><h1>Siphons · aspiration rapide & chaussée sud</h1><p>Courants spiralés vers les centres, palette cycling bleu–cyan, écume mobile autour des rochers et reflets de rive. Une chaussée sèche mène du sud au palier du grand siphon. 48 phases à 40 ms ; effets visuels reconstruits, pas de collisions ou physique PMDO configurées.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="47" value="0"><span id="label">Boucle 1,92 s</span><br><img id="view" alt="Courants rapides vers les siphons et passage rocheux"><script>const items='''+json.dumps(items)+',frames='+json.dumps([uri(png(f)) for f in frames])+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 48'};</script>'''
(R/'apercu_eau_siphons_rapides_v2.html').write_text(html)
print(json.dumps(manifest['tests'],indent=2))
