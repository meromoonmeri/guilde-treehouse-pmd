from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/cote_cendres_passage_v2';P=O/'cote_cendres_passage';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=648,504;NN=Image.Resampling.NEAREST;N=64;DT=120

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def composite(layers):
 c=Image.new('RGBA',(W,H))
 for name,im in layers:c.alpha_composite(im)
 return c
terrain=key(load(O/'bruts/chemin_magenta_corrige.png').resize((W,H),NN));a=np.array(terrain);mask=a[:,:,3]>0
# Desaturate magenta edge contamination and unify ash gray; alpha has already been cleaned.
lum=np.rint(a[:,:,:3]@np.array([.2126,.7152,.0722])).astype('uint8')
for j in range(3):a[:,:,j]=np.clip(lum.astype(int)+[0,0,3][j],0,255)
a[~mask]=0
# Visible-surface partition, not a claim to reconstruct complete movable rocks.
dist=nd.distance_transform_edt(mask);edge=mask&(dist<17);rock=mask&~edge&(lum<69);floor=mask&~edge&~rock
static=[('03_sol_chemin',part(a,floor)),('04_rebords_rocheux',part(a,edge)),('05_reliefs_sombres',part(a,rock))]
# Verify a broad connected north/south interior, not simply one connected diagonal pixel.
interior=dist>=12;labels,_=nd.label(interior);assert set(labels[0])&set(labels[-1])-{0}
for name,im in static:im.save(P/f'cendres_v2_{name}.png')
Image.fromarray((interior*255).astype('uint8')).save(O/'masque_passage_interieur.png')
# Four independent generated geyser poses, crop without removing detached rising sparks.
sheet=key(load(O/'bruts/colonnes_flammes_magenta.png'));sprites=[]
for i in range(4):
 im=sheet.crop((i*sheet.width//4,0,(i+1)*sheet.width//4,sheet.height));im=im.crop(im.getbbox());im=im.resize((max(12,round(im.width*88/im.height)),88),NN);im.save(O/f'colonne_pose_{i:02}.png');sprites.append(im)
# Uneven vent placements: several on the path, others close to its borders. Distinct clocks.
vents=[(291,66,0,77),(379,127,9,100),(251,199,23,74),(186,270,36,92),(344,296,17,109),(282,360,43,81),(416,414,31,98),(343,474,53,86)]
ventlayer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ventlayer)
for x,y,_,_ in vents:
 assert mask[y,x],(x,y)
 d.ellipse((x-10,y-4,x+10,y+4),fill=(29,20,24),outline=(103,51,28));d.ellipse((x-5,y-2,x+5,y+2),fill=(220,64,7));d.line((x-3,y,x+3,y),fill=(255,163,25),width=2)
static.append(('06_events_volcaniques',ventlayer));ventlayer.save(P/'cendres_v2_06_events_volcaniques.png')
# New procedural lava, NOT a recolored water sequence. Sample a turbulent noise field with periodic local advection.
rng=np.random.default_rng(819);hh,ww=H//2,W//2;yy,xx=np.mgrid[:hh,:ww];noise=np.zeros((hh,ww))
for sigma,weight in [(13,1),(5,.38),(1.5,.09)]:
 f=nd.gaussian_filter(rng.normal(size=(hh,ww)),sigma,mode='wrap');noise+=f/f.std()*weight
noise=(noise-noise.min())/(noise.max()-noise.min());palette=np.array([[44,12,12],[83,17,8],[128,25,5],[177,37,4],[222,57,4],[250,93,7],[255,148,20],[255,196,49]],dtype='uint8')
shore=nd.distance_transform_edt(~mask);lavaframes=[];glows=[];flamegroups=[[] for _ in vents];frames=[]
for i in range(N):
 t=2*np.pi*i/N
 dx=9*np.sin(t+yy/29)+5*np.cos(t+xx/37+yy/41);dy=7*np.cos(t+xx/39)+3*np.sin(2*t+yy/31)
 f=nd.map_coordinates(noise,[yy+dy,xx+dx],order=1,mode='grid-wrap');idx=np.digitize(f,[.20,.31,.42,.53,.64,.74,.84]);rgb=palette[idx];lava=Image.fromarray(rgb).resize((W,H),NN).convert('RGBA');lavaframes.append(lava)
 lava.save(P/f'cendres_v2_01_lave_visqueuse_{i:03}.png')
 g=np.zeros((H,W,4),dtype='uint8');g[:,:,:3]=[255,111,12];g[:,:,3]=np.rint(np.clip((6-shore)/6,0,1)*(~mask)*(65+15*np.sin(t+np.arange(H)[:,None]/29))).astype('uint8');g[g[:,:,3]==0]=0;glow=Image.fromarray(g);glows.append(glow);glow.save(P/f'cendres_v2_02_lueur_rives_{i:03}.png')
 flames=[]
 for k,(x,y,offset,height) in enumerate(vents):
  phase=(i+offset)%N;angle=2*np.pi*phase/N
  envelope=.35+.65*((1+np.sin(angle*(1+k%2)+k*.7))/2)**1.3
  pose=sprites[((phase//2)+k)%4];fh=max(16,round(height*envelope));fw=max(9,round(pose.width*(.65+.35*envelope)));im=pose.resize((fw,fh),NN)
  # Small upward-moving sparks are part of the pose; bases stay firmly attached to vents.
  layer=Image.new('RGBA',(W,H));layer.alpha_composite(im,(x-fw//2,y-fh+1));flamegroups[k].append(layer);layer.save(P/f'cendres_v2_07_colonne_{k:02}_{i:03}.png');flames.append((f'07_colonne_{k:02}',layer))
 layers=[('01_lave_visqueuse',lava),('02_lueur_rives',glow)]+static+flames;c=composite(layers);assert np.all(np.array(c)[:,:,3]==255);frames.append(c);c.save(P/f'cendres_v2_scene_{i:03}.png')
 if i==0:
  first=layers;c.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,lossless=True,loop=0)
# Layered phase-zero OpenRaster, with a PNG sequence for every animated layer.
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'cote_cendres_passage.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for i,(name,im) in reversed(list(enumerate(first))):
  fn=f'data/{i}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'cote_cendres_passage.ora') as z:
 stack=ET.fromstring(z.read('stack.xml')).find('stack');re=composite([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(stack)]);assert np.array_equal(np.array(re),np.array(frames[0]))
# Compare wrap to regular motion; all transitions are periodic, including the final/first pair.
deltas=[float(np.mean(np.abs(np.array(lavaframes[(i+1)%N]).astype(float)-np.array(lavaframes[i])))) for i in range(N)]
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'vents':[{'position':[x,y],'phase_offset':p,'max_height':h} for x,y,p,h in vents],'static_layers':[n for n,_ in static],'animation_groups':['01_lave_visqueuse','02_lueur_rives']+[f'07_colonne_{i:02}' for i in range(len(vents))],'origin':'Generated gray terrain and flame poses keyed from magenta; new periodic advected-noise lava, no native water frames reused.','tests':{'north_south_connected_24px_interior':True,'all_compositions_opaque':True,'ora_recomposition_exact':True,'lava_mean_step':float(np.mean(deltas)),'lava_wrap_step':deltas[-1]},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Standalone visual review, including animated groups and a frame-by-frame scrubber.
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition complète','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for name,ims in [('Lave visqueuse',lavaframes),('Lueur des rives',glows)]+[(f'Colonne {i+1}',g) for i,g in enumerate(flamegroups)]:
 b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=DT,lossless=True,loop=0);items.append({'name':name,'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Cendres — passage sud / nord</title><style>body{background:#181719;color:#eee1d3;font:16px system-ui;max-width:1100px;margin:28px auto;padding:0 20px}h1{color:#ffb254}p{line-height:1.6;max-width:900px}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#28282b 0 25%,#343437 0 50%) 0/16px 16px}button,select{padding:10px;background:#342a27;color:#ffe1b2;border:1px solid #96603e;margin:8px}input{width:300px}</style><h1>Cendres · passage sud → nord</h1><p>Chemin traversant ouvert aux deux extrémités. Lave lente à remous irréguliers, croûtes sombres et huit colonnes de flammes aux rythmes décalés. Calques indépendants. Nouvelle animation reconstruite, et non le cycle de vagues recoloré. Pas de validation PMDO/collisions.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="63" value="0"><span id="label">64 phases · 120 ms · boucle 7,68 s</span><br><img id="view" alt="Passage volcanique sud nord"><script>const items='''+json.dumps(items)+',frames='+json.dumps([uri(png(f)) for f in frames])+''';items.forEach((v,i)=>sel.add(new Option(v.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 64'};</script>'''
(R/'apercu_cote_cendres_passage_v2.html').write_text(html)
print(json.dumps(manifest['tests'],indent=2))
