"""Generated magma keyframes + causally ordered bubble eruptions, on lava only."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
import cv2
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/cendres_grotte_eruptions_v3';P=O/'cendres_grotte';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=648,504;N=64;DT=100;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im)
 return c
# Stable terrain for all complete frames: south road leads INTO the existing-style cave.
a=np.array(key(load(O/'bruts/terrain_grotte_magenta.png').resize((W,H),NN)));solid=a[:,:,3]>0;lum=np.rint(a[:,:,:3]@np.array([.2126,.7152,.0722])).astype('uint8')
for j in range(3):a[:,:,j]=np.clip(lum.astype(int)+[0,0,2][j],0,255)
a[~solid]=0;dist=nd.distance_transform_edt(solid)
cave=solid&(xx>197)&(xx<300)&(yy>95)&(yy<175)&(lum<43)
wall=solid&~cave&(yy<190);rim=solid&~cave&~wall&(dist<14);floor=solid&~cave&~wall&~rim
static=[('03_sol_chemin',part(a,floor)),('04_rebords_rocheux',part(a,rim)),('05_parois_grotte',part(a,wall)),('06_profondeur_grotte',part(a,cave))]
for name,im in static:im.save(P/f'grotte_v3_{name}.png')
walk=Image.new('L',(W,H));ImageDraw.Draw(walk).line([(254,160),(255,218),(293,275),(346,343),(365,422),(355,503)],fill=255,width=32);wm=np.array(walk)>0;assert np.all(solid[wm]),'Approach leaves terrain'
walk.save(O/'masque_approche_grotte.png')
# Four generated, aligned lava keyframes, not the old procedural wave/noise animation.
sheet=load(O/'bruts/magma_quatre_phases_affine.png').convert('RGB');keys=[]
for k in range(4):
 x=(k%2)*sheet.width//2;y=(k//2)*sheet.height//2
 im=sheet.crop((x,y,x+sheet.width//2,y+sheet.height//2)).resize((324,252),NN)
 # Mirror extensions avoid a tile seam; the vertical join lies under the approach.
 canvas=Image.new('RGB',(W,H));canvas.paste(im,(0,0));canvas.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(324,0));canvas.paste(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(0,252));canvas.paste(im.transpose(Image.Transpose.ROTATE_180),(324,252));canvas.save(O/f'magma_cle_{k:02}.png');keys.append(canvas)
# Estimate local displacement between generated poses, then interpolate slowly through each pair.
small=[np.array(im.resize((324,252),NN)) for im in keys];flows=[]
for k in range(4):
 ga=cv2.cvtColor(small[k],cv2.COLOR_RGB2GRAY);gb=cv2.cvtColor(small[(k+1)%4],cv2.COLOR_RGB2GRAY)
 f=cv2.calcOpticalFlowFarneback(ga,gb,None,.5,3,25,5,5,1.2,0);b=cv2.calcOpticalFlowFarneback(gb,ga,None,.5,3,25,5,5,1.2,0);flows.append((f,b))
# Quantization to a shared generated palette keeps inbetweens pixel-art, not a blurred dissolve.
pal=keys[0].quantize(colors=24);gy,gx=np.mgrid[:252,:324].astype('float32');magma=[]
for i in range(N):
 k=i//16;t=(i%16)/16;f,b=flows[k]
 left=cv2.remap(small[k],gx-f[:,:,0]*t,gy-f[:,:,1]*t,cv2.INTER_NEAREST,borderMode=cv2.BORDER_REFLECT)
 right=cv2.remap(small[(k+1)%4],gx-b[:,:,0]*(1-t),gy-b[:,:,1]*(1-t),cv2.INTER_NEAREST,borderMode=cv2.BORDER_REFLECT)
 im=Image.fromarray(np.rint(left*(1-t)+right*t).astype('uint8')).quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA').resize((W,H),NN);magma.append(im)
# Eight generated eruption stages, common scale and ground anchor. Never normalize each pose's height.
sheet=key(load(O/'bruts/bulle_eruption_huit_phases.png'));sprites=[]
for k in range(8):
 x=(k%4)*sheet.width//4;y=(k//4)*sheet.height//2;im=sheet.crop((x,y,x+sheet.width//4,y+sheet.height//2));im=im.crop(im.getbbox());im=im.resize((max(1,round(im.width*.20)),max(1,round(im.height*.20))),NN);im.save(O/f'eruption_pose_{k:02}.png');sprites.append(im)
stages=['bulle_basse','gonflement','bulle_fissuree','eclatement','jet_naissant','colonne','retombee','residu']
def event_state(phase):
 for stage,(lo,hi) in enumerate([(0,4),(4,8),(8,12),(12,14),(14,18),(18,24),(24,29),(29,35)]):
  if lo<=phase<hi:return stage,(phase-lo)/(hi-lo)
 return None,0
# Find molten, clear anchor areas near uneven requested positions, always outside ALL solid terrain.
requests=[(68,350,0,.85),(539,323,11,1.05),(136,407,24,1.0),(578,427,38,.90),(52,478,47,1.1),(510,485,56,.95)]
keys_rgb=np.stack([np.array(im) for im in keys]);hot=np.mean((keys_rgb[:,:,:,0]>120)&(keys_rgb[:,:,:,1]>15),axis=0)
vents=[]
for x0,y0,offset,scale in requests:
 candidates=[]
 for y in range(max(100,y0-40),min(H-7,y0+41),3):
  for x in range(max(42,x0-40),min(W-42,x0+41),3):
   # Full tallest-sprite bounding rectangle is water/lava; no clipping flames against the road.
   if np.any(solid[y-96:y+4,x-39:x+40]):continue
   heat=float(hot[y-2:y+3,x-18:x+19].mean())
   if heat<.35:continue
   score=heat*70-np.hypot(x-x0,y-y0)
   candidates.append((score,x,y,heat))
 assert candidates,(x0,y0)
 _,x,y,heat=max(candidates);vents.append({'anchor':[x,y],'offset':offset,'scale':scale,'molten_anchor_fraction':heat})
anim_names=['01_magma_genere','02_chaleur_rives']+[f'07_eruption_{k:02}' for k in range(len(vents))]
groups={n:[] for n in anim_names};frames=[];events_timeline=[];shore=nd.distance_transform_edt(~solid)
for i in range(N):
 phase=2*np.pi*i/N;g=np.zeros((H,W,4),dtype='uint8');g[:,:,:3]=[244,80,8];g[:,:,3]=np.rint((~solid)*np.clip((6-shore)/6,0,1)*(37+12*np.sin(phase+yy/31))).astype('uint8');g[g[:,:,3]==0]=0;glow=Image.fromarray(g)
 ims=[magma[i],glow];states=[]
 for k,v in enumerate(vents):
  x,y=v['anchor'];local=(i+v['offset'])%N;stage,u=event_state(local);layer=Image.new('RGBA',(W,H))
  if stage is not None:
   sprite=sprites[stage];scale=v['scale'];stretch=1+.045*np.sin(u*2*np.pi) if stage in [4,5,6] else 1
   im=sprite.resize((round(sprite.width*scale),round(sprite.height*scale*stretch)),NN)
   if stage==7:
    ar=np.array(im);ar[:,:,3]=np.rint(ar[:,:,3]*(1-u)).astype('uint8');ar[ar[:,:,3]==0]=0;im=Image.fromarray(ar)
   layer.alpha_composite(im,(x-im.width//2,y-im.height+1))
  assert not np.any(np.array(layer)[:,:,3][solid]),'An eruption overlaps the path or cave'
  ims.append(layer);states.append('repos' if stage is None else stages[stage])
 for name,im in zip(anim_names,ims):groups[name].append(im);im.save(P/f'grotte_v3_{name}_{i:03}.png')
 ls=list(zip(anim_names[:2],ims[:2]))+static+list(zip(anim_names[2:],ims[2:]));c=compose(ls);assert np.all(np.array(c)[:,:,3]==255);frames.append(c);c.save(P/f'grotte_v3_scene_{i:03}.png');events_timeline.append(states)
 if i==0:first=ls;c.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'cendres_grotte.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'cendres_grotte.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');im=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(im),np.array(frames[0]))
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'static_layers':[n for n,_ in static],'animation_groups':anim_names,'render_order':anim_names[:2]+[n for n,_ in static]+anim_names[2:],'vents':vents,'event_stages':stages,'timeline':events_timeline,'origin':{'terrain':'generated on magenta, gray cave destination and continuous south approach','magma':'4 generated keyframes with optical-flow-guided quantized inbetweens; not previous procedural noise or recolored water','eruptions':'8 generated chronological stages; six staggered sites, all on lava'},'tests':{'south_to_cave_32px_corridor_on_terrain':True,'all_eruption_pixels_outside_terrain_all_frames':True,'opaque_compositions':True,'ora_recomposition_exact':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Chronology sheet helps inspect the causal sequence without relying on playback.
board=Image.new('RGB',(8*120,132),(42,23,25));d=ImageDraw.Draw(board)
for k,im in enumerate(sprites):
 board.paste(im,(k*120+60-im.width//2,100-im.height),im);d.text((k*120+5,110),f'{k+1}. '+stages[k],fill=(255,198,122))
board.save(O/'SEQUENCE_BULLE_FLAMME.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for name,seq in groups.items():
 b=io.BytesIO();seq[0].save(b,format='WEBP',save_all=True,append_images=seq[1:],duration=DT,loop=0,lossless=True);items.append({'name':name,'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
# Individual stills stored in lossless WebP inside HTML; full PNGs remain in the pack.
stills=[]
for im in frames:
 b=io.BytesIO();im.save(b,format='WEBP',lossless=True);stills.append(uri(b.getvalue(),'image/webp'))
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Grotte cendrée — bulles et éruptions latérales</title><style>body{background:#1b181a;color:#ebded0;font:16px system-ui;max-width:1080px;margin:28px auto;padding:0 20px}h1{color:#ffc078}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#31282a 0 25%,#493538 0 50%) 0/16px 16px}select,button{padding:10px;margin:8px;background:#392b27;color:#ffd5a7;border:1px solid #895f43}input{width:230px}</style><h1>Grotte cendrée · bulles → éclatement → flammes</h1><p>Le chemin venant du sud mène à la grotte. Toutes les éruptions sont dans la lave latérale : aucun jet sur le passage. Magma en 4 images clés générées, séquence d’éruption en 8 poses générées, assemblage en 64 frames. Pas de test PMDO/collisions.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="63" value="0"><span id="label">64 phases · 100 ms · 6,4 s</span><br><img id="view" alt="Chemin vers la grotte, lave et éruptions sur les côtés"><h2>Ordre des événements</h2><img alt="Bulle basse, gonflement, fissures, éclatement, jet, colonne, retombée, résidu" src="'''+uri(png(board))+'''"><p>Chaque site suit cet ordre, puis reste au repos avant un nouveau gonflement. Les sites sont décalés dans le temps. L’aperçu peut commencer au milieu du cycle d’un site.</p><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 64'};</script>'''
(R/'apercu_cendres_grotte_eruptions_v3.html').write_text(html)
print(json.dumps(manifest['tests'],indent=2));print(vents)
