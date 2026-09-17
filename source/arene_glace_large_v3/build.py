"""Fresh wide render, separately generated sky, and spatially/temporally periodic aurora.
Generated terrain is never built from cropped map pieces. Previous versions preserved.
"""
from pathlib import Path
import sys,json,math,hashlib,base64,io,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_glace_large_v3';W,H=768,512;PERIOD=792;STEP=4;N=198;TICKS=8;DURATION_MS=26400
sys.path.insert(0,str(R))
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mag=(r>70)&(b>65)&(r>g*1.5)&(b>g*1.5);a[mag]=0;a[~mag,3]=255;return Image.fromarray(a)
def masked(im,m):
 a=np.array(im);a[~m]=0;return Image.fromarray(a)
def split_stars(im):
 a=np.array(im);median=np.array(im.convert('RGB').filter(ImageFilter.MedianFilter(9)));bright=(a[:,:,:3].astype(int)-median.astype(int)).max(axis=2)>25
 mask=np.array(Image.fromarray(np.uint8(bright)*255).filter(ImageFilter.MaxFilter(3)))>0
 stars=a.copy();stars[~mask]=0;sky=a.copy();sky[mask,:3]=median[mask];return Image.fromarray(sky),Image.fromarray(stars)

def load(p):return Image.open(p).convert('RGBA')
def blank(size=(W,H)):return Image.new('RGBA',size)
def fit(im,opaque=False):
 # Uniform scale ONLY, then center-pad; never stretch a portrait or change pixel aspect.
 scale=min(W/im.width,H/im.height);size=(round(im.width*scale),round(im.height*scale));small=im.resize(size,Image.Resampling.NEAREST);x=(W-size[0])//2;y=H-size[1];out=blank();out.alpha_composite(small,(x,y))
 if opaque:
  a=np.array(out)
  for row in range(H):
   ry=min(max(row-y,0),size[1]-1);a[row,:x]=np.array(small)[ry,0];a[row,x+size[0]:]=np.array(small)[ry,-1]
  if y: a[:y]=a[y]
  out=Image.fromarray(a)
 return out,{'input_size':list(im.size),'uniform_scale':scale,'resized_size':list(size),'placement':[x,y],'method':'uniform nearest-neighbor fit; tiny margins padded, not aspect-ratio stretching'}
def poly(points):
 im=Image.new('L',(W,H));ImageDraw.Draw(im).polygon([(round(x*W),round(y*H)) for x,y in points],fill=255);return np.array(im)>0

def aurora_tile():
 """Canonical artwork in three offset poses; all joins fade to exact transparency.
 Alpha edge treatment is authored. No mirrored or stretched aurora RGB pixels.
 """
 tile=blank((PERIOD,240));sources=[]
 for i,frame in enumerate([0,16,32]):
  p=R/'exports/ice_arena_aurora_v1/aurora_frames'/f'IceAuroraV1_Ribbons_{frame:02}.png';im=load(p);a=np.array(im);h,w=a.shape[:2];x=np.arange(w);y=np.arange(h)
  horizontal=np.sin(np.clip(np.minimum(x,w-1-x)/24,0,1)*math.pi/2)**2
  bottom=np.clip((h-1-y)/20,0,1);factor=bottom[:,None]*horizontal[None,:]
  a[:,:,3]=np.rint(a[:,:,3]*factor).astype('uint8');a[a[:,:,3]==0]=0
  tile.alpha_composite(Image.fromarray(a),(i*264,[8,0,16][i]));sources.append({'file':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'position':[i*264,[8,0,16][i]]})
 return tile,sources

def overlay(tile,step):
 a=np.array(tile);cols=(np.arange(W)+(step%N)*STEP)%PERIOD;return Image.fromarray(a[:,cols])

def ora(path,layers):
 root=ET.Element('image',w=str(W),h=str(H),name='Arène large V3');stack=ET.SubElement(root,'stack');merged=blank()
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):
   fn=f'data/layer{i}.png';ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'});b=io.BytesIO();im.save(b,format='PNG');z.writestr(fn,b.getvalue())
  for im in layers.values():merged.alpha_composite(im)
  b=io.BytesIO();merged.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue());z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True))

def build():
 for name in ['calques','masques','animation/frames','review']:(O/name).mkdir(parents=True,exist_ok=True)
 terrain,tm=fit(key(load(O/'bruts/terrain_magenta.png')));floor,fm=fit(key(load(O/'bruts/sol_complet.png')));sky,sm=fit(load(O/'bruts/ciel.png'),True)
 sky,stars=split_stars(sky)
 a=np.array(terrain);valid=a[:,:,3]>0;yy,xx=np.mgrid[:H,:W]
 ground=poly([(.27,.365),(.43,.313),(.55,.313),(.687,.365),(.824,.449),(.85,.522),(.824,.602),(.79,.66),(.756,.743),(.641,.824),(.659,.886),(.723,1),(.281,1),(.397,.864),(.378,.799),(.277,.756),(.211,.69),(.175,.627),(.147,.543),(.153,.494),(.196,.42)])&valid
 objects=(poly([(.38,.445),(.408,.439),(.433,.49),(.397,.502),(.37,.484)])|poly([(.601,.34),(.633,.335),(.659,.383),(.61,.402)]))&ground
 path=ground&(yy>H*.79)&~objects;visible=ground&~objects&~path
 left=poly([(0,.30),(.062,.305),(.131,.381),(.147,.543),(.211,.69),(.277,.756),(.378,.799),(.397,.864),(.281,1),(0,1)])
 right=poly([(1,.29),(.933,.322),(.881,.451),(.85,.522),(.79,.66),(.756,.743),(.641,.824),(.659,.886),(.723,1),(1,1)])
 structure=valid&~ground;left&=structure;right&=structure&~left;rear=structure&~left&~right
 masks={'02_sol_visible':visible,'03_acces_sud':path,'04_reliefs_arriere':rear,'05_reliefs_avant_gauche':left,'06_reliefs_avant_droit':right,'07_petits_reliefs':objects}
 layers={'01_sol_complet':masked(floor,valid)}
 for name,m in masks.items():layers[name]=masked(terrain,m);Image.fromarray(np.uint8(m)*255).save(O/'masques'/f'{name}.png')
 sky.save(O/'calques/AreneLargeV3_00_ciel_genere.png');stars.save(O/'calques/AreneLargeV3_00b_etoiles.png')
 for name,im in layers.items():im.save(O/'calques'/f'AreneLargeV3_{name}.png')
 terrain.save(O/'review/terrain_detoure.png');tile,origins=aurora_tile();tile.save(O/'animation/AreneLargeV3_Aurore_Wrap792.png')
 def scene(f):
  im=sky.copy();im.alpha_composite(stars);im.alpha_composite(overlay(tile,f),(0,0))
  for layer in layers.values():im.alpha_composite(layer)
  return im
 samples=[0,49,99,148,197]
 for f in range(N):
  overlay(tile,f).save(O/'animation/frames'/f'AreneLargeV3_Aurore_{f:03}.png')
  if f in samples:scene(f).save(O/'review'/f'scene_{f:03}.png')
 # Streaming GIF frames; unchanged terrain uses delta rectangles. Global palette includes the whole strip.
 palboard=Image.new('RGB',(W,H+240));palboard.paste(scene(0).convert('RGB'),(0,0));palboard.paste(tile.convert('RGB').crop((0,0,W,240)),(0,H));palette=palboard.quantize(colors=256)
 def gif_frame(f):return scene(f).convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE)
 durations=[130,130,140]*(N//3)
 gif_frame(0).save(O/'review/animation.gif',save_all=True,append_images=(gif_frame(f) for f in range(1,N)),duration=durations,loop=0,disposal=1,optimize=False)
 frames=[Image.open(O/'animation/frames'/f'AreneLargeV3_Aurore_{f:03}.png') for f in range(N)]
 try:frames[0].save(O/'animation/AreneLargeV3_Aurore_Loop.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True,method=4)
 finally:
  for frame in frames:frame.close()
 phase=blank();phase.alpha_composite(overlay(tile,0),(0,0));ora(O/'arene_large_editable.ora',{'00_ciel_genere':sky,'00b_etoiles':stars,'00c_aurore_phase0':phase,**layers})
 sources=[{'file':str((O/'bruts'/name).relative_to(R)),'sha256':hashlib.sha256((O/'bruts'/name).read_bytes()).hexdigest()} for name in ['terrain_magenta.png','sol_complet.png','ciel.png']]
 manifest={'size':[W,H],'previous_size':[512,640],'layout':'New landscape generation, broad oval arena and short south approach; not a stretched old portrait.','terrain_method':'Full generated terrain on magenta, generated full floor, disjoint aligned depth layers. No source-map chunk assembly.','sky':'New separately generated sky; stars extracted into their own static overlay using local median cleanup. Recomposition restores generated sky exactly. No aurora baked in.','normalization':{'terrain':tm,'floor':fm,'sky':sm},'sources':sources,'layers':[{'id':n,'file':'calques/AreneLargeV3_'+n+'.png'} for n in layers],'sky_file':'calques/AreneLargeV3_00_ciel_genere.png','stars_file':'calques/AreneLargeV3_00b_etoiles.png','aurora':{'tile':'animation/AreneLargeV3_Aurore_Wrap792.png','period_width':PERIOD,'height':240,'viewport_width':W,'step_pixels':STEP,'frames':N,'frame_ticks':TICKS,'duration_ms':DURATION_MS,'speed_pixels_per_second':30,'direction':'left','repeat_x':True,'formula':'viewport(x,y,f)=tile((x+4*(f mod198)) mod792,y)','sources':origins,'edge_treatment':'24px cosine alpha fade on native motif edges,20px fade at their lower edges. First/last tile columns exactly transparent.','origin':'Canonical aurora drawing in previously authored poses, newly arranged/alpha-feathered for wrap. Not an extracted official game cycle.'},'loop_assertion':'Frame198 equals frame0 exactly; frame197→0 advances exactly4px like every other preview step. Continuous viewer clock wraps at26.4seconds.','runtime_PMDO':'NOT TESTED','art_approved':False,'other_zones_complete':False,'layer_limit':'Terrain depth partitions; hidden floor generated, hidden cliff backfaces not reconstructed.'}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (O/'placement_recipe.json').write_text(json.dumps({'type':'descriptive_recipe_not_native_engine_file','canvas':[W,H],'order':['sky','stars','aurora_wrap']+list(layers),'aurora_texture':[792,240],'repeat_x':True,'position':[0,0],'velocity_px_per_second':[-30,0],'loop_seconds':26.4,'preview_frame_ticks':8,'preview_frames':198,'formula':'source_x = (screen_x + floor(elapsed_seconds *30)) %792','note':'Convert timing/movement units for target engine and test parallax/import. Static sky and terrain do not scroll.'},indent=2)+'\n')
 gallery(layers,sky,tile,manifest)
 print('Wide arena768x512, separate new sky, wrap792px,198overlay frames,26.4s seamless loop.')

def gallery(layers,sky,tile,manifest):
 def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 data={'sky':uri(O/manifest['sky_file']),'stars':uri(O/manifest['stars_file']),'tile':uri(O/manifest['aurora']['tile']),'layers':[{'id':n,'uri':uri(O/'calques'/f'AreneLargeV3_{n}.png')} for n in layers]}
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Arène large · ciel séparé et aurore wrap</title><style>body{font:16px system-ui;background:#0b1728;color:#e6edf4;margin:32px auto;max-width:1280px;padding:20px}h1{font-size:36px}p{line-height:1.6;color:#baccda}canvas{max-width:100%;image-rendering:pixelated;background:#322d42}.row{display:flex;gap:24px;flex-wrap:wrap}aside{max-width:360px}label{display:block;margin:10px 0}button{background:#c2e1ea;border:0;border-radius:6px;padding:10px 16px;margin:4px}input[type=range]{width:100%}.tag{color:#f1d69d}details{margin:15px 0}</style><h1>Arène élargie · aurores en wrap</h1><p>Nouvelle composition <b>768 × 512</b>, au lieu de 512 × 640 : plus large, moins haute, accès sud raccourci. Terrain et ciel régénérés séparément ; aucune déformation de l’ancien portrait.</p><div class="row"><div><canvas id="scene" width="768" height="512"></canvas><p class="tag">Ciel fixe · aurore transparente défilante · terrain fixe</p></div><aside><button id="play">Pause</button><button id="join">Voir le raccord de boucle</button><p id="clock"></p><input id="seek" type="range" min="0" max="26399" value="0"><div id="controls"></div><p>Bande périodique 792 px, 30 px/s : une boucle de 26,4 s. L’aurore sort à gauche et rentre à droite. Le raccord spatial est adouci jusqu’à une transparence exacte ; le retour temporel est calculé modulo la période.</p><p>Dessin d’aurore canonique, arrangement/mouvement/alpha nouveaux. Terrain et ciel générés. Pas de cycle officiel retrouvé ni de runtime PMDO validé.</p></aside></div><details><summary>Aurore seule sur transparence</summary><canvas id="strip" width="768" height="240"></canvas></details><script>const data=__DATA__;const c=document.getElementById('scene'),ctx=c.getContext('2d'),strip=document.getElementById('strip'),sx=strip.getContext('2d'),seek=document.getElementById('seek');let running=true,t=0,start=performance.now();const checks={};function image(url){const im=new Image();im.src=url;return im}const sky=image(data.sky),stars=image(data.stars),tile=image(data.tile),layers=data.layers.map(l=>image(l.uri));for(const id of ['ciel','etoiles','aurore',...data.layers.map(l=>l.id)]){const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;checks[id]=ch;label.append(ch,document.createTextNode(id));document.getElementById('controls').append(label)}function wrap(context){if(!tile.complete||!tile.naturalWidth)return;const shift=Math.floor(t*30/1000)%792;context.drawImage(tile,-shift,0);context.drawImage(tile,792-shift,0)}function draw(){ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,768,512);if(checks.ciel.checked&&sky.complete&&sky.naturalWidth)ctx.drawImage(sky,0,0);if(checks.etoiles.checked&&stars.complete&&stars.naturalWidth)ctx.drawImage(stars,0,0);if(checks.aurore.checked)wrap(ctx);layers.forEach((im,i)=>{if(checks[data.layers[i].id].checked&&im.complete&&im.naturalWidth)ctx.drawImage(im,0,0)});sx.clearRect(0,0,768,240);wrap(sx);document.getElementById('clock').textContent=(t/1000).toFixed(2)+' / 26,40 s';seek.value=t}function pauseLabel(){document.getElementById('play').textContent=running?'Pause':'Lecture'}seek.oninput=()=>{running=false;t=+seek.value;pauseLabel();draw()};document.getElementById('play').onclick=()=>{running=!running;start=performance.now()-t;pauseLabel()};document.getElementById('join').onclick=()=>{t=25400;running=true;start=performance.now()-t;pauseLabel()};function tick(now){if(running)t=(now-start)%26400;draw();requestAnimationFrame(tick)}requestAnimationFrame(tick)</script></html>'''
 (R/'apercu_arene_glace_large_v3.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
if __name__=='__main__':build()
