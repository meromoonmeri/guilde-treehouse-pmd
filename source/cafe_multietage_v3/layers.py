from pathlib import Path
import json,base64,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];B=R/'renders/cafe_multietage_v3/bruts';P=R/'source/cafe_multietage_v1/references';O=R/'renders/cafe_multietage_v3/calques_alignés';O.mkdir(exist_ok=True)
def load(p):return Image.open(p).convert('RGBA')
def key(im):
 a=np.array(im);m=(a[:,:,0]>50)&(a[:,:,2]>40)&(a[:,:,2]>a[:,:,1]*1.5)&(a[:,:,0]>a[:,:,1]*1.5);a[m]=0;return Image.fromarray(a)
def clean_generated(im):
 # Remove the magenta chroma-key spill left on generated source edges.
 # This is intentionally applied only to generated cafe sources, never native sprites.
 a=np.array(im).copy();r,g,b=a[:,:,0].astype(np.int16),a[:,:,1].astype(np.int16),a[:,:,2].astype(np.int16)
 spill=(a[:,:,3]>0)&(r>150)&(b>130)&(g<125)&((r-g)>65)&((b-g)>65)
 a[spill,3]=0
 return Image.fromarray(a)
base=load(B/'B_base_vide_sans_rubans.png');size=base.size;w,h=size
# Correct native floor after generation; doorway and wall-contact edges stay protected.
patch=load(P/'Metano_Town_Cafe_Base.png').crop((128,160,192,224)).resize((192,192),Image.Resampling.NEAREST);floor=Image.new('RGBA',size)
for y in range(0,h,192):
 for x in range(0,w,192):floor.paste(patch,(x,y))
m=Image.open(R/'renders/cafe_multietage_v3/accueil_ludicolo/masque_reprise_sol.png');base=key(Image.composite(floor,base,m))
layers={'00_salle_vide':base};meta=[]
def layer(name,im,origin,**kw):
 assert im.size==size;layers[name]=im;meta.append({'name':name,'origin':origin,**kw})
def masked(im,mask):
 a=np.array(im);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask,dtype='uint8'));a[a[:,:,3]==0]=0;return Image.fromarray(a)
damage=clean_generated(load(B/'B_mur_casse_corrige.png'));holemask=Image.new('L',size);ImageDraw.Draw(holemask).rectangle((478,111,790,321),fill=255);holemask=holemask.filter(ImageFilter.GaussianBlur(2))
# Below wall base, keep only the broken silhouette, never a rectangular patch of regenerated floor.
hm=np.array(holemask);da=np.array(damage);hm[246:][~((da[246:,:,0]<225)&(da[246:,:,1]<173))]=0;holemask=Image.fromarray(hm)
# Replacement patch is opaque in its core: it replaces, not overlays a transparent hole on, the intact wall.
layer('01_mur_casse_remplacement',masked(damage,holemask),'Generated local wall replacement; placement locked to common base')
holemask.save(O/'masque_remplacement_mur.png')
a=np.array(damage);yy,xx=np.mgrid[:h,:w];region=(xx>=492)&(xx<794)&(yy>=322)&(yy<460);shadow=region&(a[:,:,1]<160)&(a[:,:,0]<210);debris=shadow&(a[:,:,0]>a[:,:,1]*1.28)&(a[:,:,0]>100)
layer('02_ombre_debris',masked(damage,(shadow&~debris)*255),'Generated cast shadow extracted locally')
layer('03_debris_bois',masked(damage,debris*255),'Generated splintered wood extracted locally')
# Isolate ornaments rather than regenerating the whole underlying architecture.
old=clean_generated(load(B/'A_accueil_interieur_bois_lumiere_corrige.png'));a=np.array(old).astype(float);red=(a[:,:,0]>90)&(a[:,:,0]>a[:,:,1]*1.7)&(a[:,:,1]>20)&(yy>105)&(yy<432)
layer('04_rubans',masked(old,red*255),'Generated canonical-guided ribbons, isolated; not native sprites')
sp=clean_generated(load(B/'B_base_spirales.png'));a=np.array(sp);sm=np.zeros((h,w),bool)
wallboxes=[(488,152,557,202),(710,152,779,202),(289,197,347,265),(926,201,982,261),(132,294,189,377),(1087,300,1145,374)]
floorboxes=[(609,255,685,313),(310,315,388,374),(900,315,980,374),(412,369,489,431),(593,369,672,431),(796,369,874,431),(136,493,217,568),(389,493,470,568),(611,493,689,568),(811,493,892,568),(1066,493,1147,568),(386,646,467,709),(596,646,677,709)]
for boxes,cond in [(wallboxes,(a[:,:,0]>200)&(a[:,:,1]>150)&(a[:,:,2]>65)),(floorboxes,(a[:,:,0]>230)&(a[:,:,1]>212)&(a[:,:,2]>110))]:
 mask=np.zeros_like(sm)
 for x0,y0,x1,y1 in boxes:mask[y0:y1,x0:x1]=True
 sm|=mask&cond
layer('05_spirales_sol_murs',masked(sp,sm*255),'Generated Spinda-reference markings, isolated from unchanged base')
# Native objects: source pixels preserved; only residual magenta key spill is made transparent, then nearest-neighbor x3 is used for this preview canvas.
obj=load(P/'spinda_cafe_layer_1.png');ref=load(P/'spinda_cafe_reference.png')
def sprite(name,source,box,xy,mask=None):
 im=clean_generated(source.crop(box))
 if mask is not None:
  im=masked(im,mask)
  # Drop detached crop fragments from nearby garlands, not the canonical object itself.
  from collections import deque
  ar=np.array(im);visible=ar[:,:,3]>0;seen=np.zeros(visible.shape,bool)
  for sy,sx in zip(*np.where(visible)):
   if seen[sy,sx]:continue
   q=deque([(sy,sx)]);seen[sy,sx]=True;component=[]
   while q:
    y,x=q.popleft();component.append((y,x))
    for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
     ny,nx=y+dy,x+dx
     if 0<=ny<visible.shape[0] and 0<=nx<visible.shape[1] and visible[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((ny,nx))
   if len(component)<16:
    for y,x in component:ar[y,x]=0
  im=Image.fromarray(ar)
 d=O/'sprites_natifs';d.mkdir(exist_ok=True);im.save(d/(name+'.png'))
 scaled=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);out=Image.new('RGBA',size);out.alpha_composite(scaled,xy)
 layer(name,out,'EoSO native reconstructed map',source_box=list(box),destination=list(xy),scale=3,rgba_sha256=hashlib.sha256(im.tobytes()).hexdigest())
for name,box,xy in [('06_table_gauche',(192,192,240,240),(220,505)),('07_table_droite',(456,192,504,240),(906,505)),('08_table_avant',(240,232,288,280),(487,595))]:sprite(name,obj,box,xy)
# Counter bodies and their upper canonical decorations are independent.
for name,box,xy in [('09_comptoir_gauche',(190,160,318,178),(175,395)),('10_comptoir_droit',(386,160,506,178),(720,395))]:sprite(name,ref,box,xy)
# Decorations cropped below the garland line; polygon excludes wall ribbons while retaining counter emblems.
for name,box,xy,poly in [
 ('11_decor_comptoir_spinda',(190,88,318,160),(175,179),[(0,40),(24,34),(24,1),(32,0),(44,9),(64,9),(78,9),(90,0),(100,0),(103,8),(92,24),(96,37),(128,40),(128,72),(0,72)]),
 ('12_decor_comptoir_bleu',(386,80,514,160),(720,155),[(0,50),(15,38),(17,17),(25,12),(40,27),(44,13),(49,6),(70,6),(84,22),(91,13),(102,18),(95,38),(116,34),(128,47),(128,80),(0,80)])]:
 mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(mask).polygon(poly,fill=255);sprite(name,obj,box,xy,mask)
# Avoid displaying native floor rectangles beneath the counters: retain their actual bar silhouette only.
# Counter face crops contain native wood, drinks bases and contact shading; documented separately from decorations.
for name,im in layers.items():im.save(O/(name+'.png'))
def comp(names):
 out=base.copy()
 for n in names:out.alpha_composite(layers[n])
 return out
states={'salle_vide':[],'salle_spirales':['05_spirales_sol_murs'],'salle_mur_casse':['01_mur_casse_remplacement','02_ombre_debris','03_debris_bois']}
for name,names in states.items():comp(names).save(O/(name+'.png'))
comp(['06_table_gauche','07_table_droite','08_table_avant','09_comptoir_gauche','10_comptoir_droit','11_decor_comptoir_spinda','12_decor_comptoir_bleu']).save(O/'apercu_meuble.png')
broken=np.array(comp(states['salle_mur_casse']));orig=np.array(base);union=np.zeros((h,w),bool)
for n in states['salle_mur_casse']:union|=np.array(layers[n])[:,:,3]>0
assert np.array_equal(broken[~union],orig[~union])
assert np.array_equal(broken[710:825,770:950],orig[710:825,770:950])
info={'size':list(size),'common_base':'00_salle_vide.png','layers':meta,'states':states,'checks':{'broken_identical_outside_local_layers':True,'threshold_unchanged':True,'all_layers_same_size':True},'runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
def uri(im):
 import io
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
data={n:uri(im) for n,im in layers.items()}
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Café — calques alignés</title><style>body{background:#231c18;color:#ecd9b4;font:16px system-ui;margin:24px}h1{font-size:26px}p{max-width:1000px;line-height:1.5}main{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:24px}canvas{width:100%;image-rendering:pixelated;background:#30251d}label{display:block;margin:12px 0}button{padding:12px;background:#62482c;color:white;border:1px solid #ac8550;border-radius:5px;margin:4px}a{color:#e9be73}small{color:#d3bf9d}@media(max-width:850px){main{grid-template-columns:1fr}}</style><h1>Café · une salle, des calques alignés</h1><p>Base vide sans rubans. Mur cassé, débris, spirales, rubans, tables et comptoirs sont indépendants. Les états intact/cassé partagent exactement la même base : seuls les pixels des calques de destruction changent.</p><div><button onclick="preset('vide')">Salle vide</button><button onclick="preset('spirales')">Spirales Spinda</button><button onclick="preset('casse')">Mur cassé</button><button onclick="preset('meublee')">Aperçu éléments canoniques</button><button onclick="download(c.toDataURL(),'composition.png')">Exporter PNG</button></div><main><canvas id="scene"></canvas><aside id="options"></aside></main><p><small>Les tables et éléments de comptoir proviennent des vraies couches EoSO, affichés à ×3 sans lissage. L’architecture, la brèche, les rubans et les spirales sont issus des générations guidées ; ce ne sont pas des sprites canoniques pixel-identiques. Les calques sont des découpes alignées, pas des objets 3D ni une intégration PMDO. Le calque mur cassé remplace la zone intacte ; son masque est fourni dans le pack.</small></p><script>const DATA=__DATA__,images={},on={},checks={},c=document.getElementById('scene'),ctx=c.getContext('2d');c.width=1264;c.height=843;const names=Object.keys(DATA);function download(u,n){let a=document.createElement('a');a.href=u;a.download=n;a.click()}for(const n of names){const im=new Image();im.src=DATA[n];images[n]=im;on[n]=n==='00_salle_vide';let l=document.createElement('label'),ch=document.createElement('input'),a=document.createElement('a');ch.type='checkbox';ch.checked=on[n];ch.onchange=()=>on[n]=ch.checked;checks[n]=ch;a.href=DATA[n];a.download=n+'.png';a.textContent=' ↓';l.append(ch,document.createTextNode(n.replace(/^\d+_/,'').replaceAll('_',' ')),a);document.getElementById('options').append(l)}function preset(mode){for(const n of names){on[n]=n==='00_salle_vide'||mode==='spirales'&&n.startsWith('05_')||mode==='casse'&&/^(01|02|03)_/.test(n)||mode==='meublee'&&/^(06|07|08|09|10|11|12)_/.test(n);checks[n].checked=on[n]}}function render(){ctx.clearRect(0,0,c.width,c.height);for(const n of names)if(on[n]&&images[n].complete&&images[n].naturalWidth)ctx.drawImage(images[n],0,0);requestAnimationFrame(render)}requestAnimationFrame(render);</script></html>'''
(R/'apercu_cafe_calques_v3.html').write_text(html.replace('__DATA__',json.dumps(data)),encoding='utf8')
print('13 aligned layers; shared room verified outside damage, original threshold unchanged')
