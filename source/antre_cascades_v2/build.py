from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_cascades_v2';P=O/'arene';S=O/'sprites';P.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=480,312;N=40;DT=80;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def compose(ls):
 im=Image.new('RGBA',(W,H))
 for n,l in ls:im.alpha_composite(l)
 return im
src=load(R/'images.png');a=np.array(src);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
# Generated platform isolated and fitted to the original circular arena and southern approach.
im=key(load(R/'renders/arene_aquatique_bois_v1/bruts/arene_pierre_bois_magenta.png'));im=im.crop(im.getbbox()).resize((170,180),Image.Resampling.NEAREST);im.save(S/'arene_pierre_bois.png');full=Image.new('RGBA',(W,H));full.alpha_composite(im,(155,132));pa=np.array(full);pr,pg,pb=pa[:,:,:3].astype(float).transpose(2,0,1);solid=pa[:,:,3]>0
wood=solid&(pr>pg*1.15)&(pg>pb*1.13);bridge=solid&(yy>=274)&(np.abs(xx-240)<35);floor=wood&~bridge;rim=solid&~floor&~bridge
platform=[('04_couronne_pierre_humide',cut(pa,rim)),('05_plancher_arene_bois',cut(pa,floor)),('06_passerelle_sud',cut(pa,bridge))]
assert np.array_equal(np.array(compose(platform)),pa)
# Newly generated coherent cavern wall, side borders and lower foreground ledges.
cave=key(load(O/'bruts/antre_roches_magenta.png')).resize((W,H),Image.Resampling.NEAREST);cavea=np.array(cave);rock=cavea[:,:,3]>0
rocks=cave
rockgroups=[('03a_paroi_fond',cut(cavea,yy<132)),('03b_bordure_gauche',cut(cavea,(yy>=132)&(yy<277)&(xx<240))),('03c_bordure_droite',cut(cavea,(yy>=132)&(yy<277)&(xx>=240))),('03d_roches_avant_bas',cut(cavea,yy>=277))]
# Generated water is the full independent background below every scene element.
raw=load(O/'bruts/eau_bassin.png').resize((W,H),Image.Resampling.NEAREST).convert('RGB').quantize(colors=20).convert('RGBA');watertex=np.array(raw)
palette=np.array([[28,81,107],[32,99,123],[37,119,140],[48,139,158],[66,158,173],[91,177,186],[128,199,200],[168,219,216]],dtype='uint8')
# Recover four generated waterfall motifs from four separated vertical sheet columns.
sheet=key(load(O/'bruts/cascades_magenta.png'));ca=np.array(sheet);runs=nd.find_objects(nd.label((ca[:,:,3]>0).sum(axis=0)>10)[0]);assert len(runs)==4
motifs=[]
for k,(sl,) in enumerate(runs):
 im=sheet.crop((sl.start,0,sl.stop,sheet.height));im=im.crop(im.getbbox()).resize((32,80),Image.Resampling.NEAREST);im.save(S/f'cascade_generee_{k:02}.png');motifs.append(np.array(im))
# Foam sheet arrived as2x2 (visually checked), not four rows. Extract each whole pose, droplets included.
sheet=key(load(O/'bruts/ecumes_magenta.png'));foammotifs=[]
for j in range(2):
 for i in range(2):
  im=sheet.crop((i*sheet.width//2,j*sheet.height//2,(i+1)*sheet.width//2,(j+1)*sheet.height//2));im=im.crop(im.getbbox());im.save(S/f'ecume_generee_{j*2+i:02}.png');foammotifs.append(im)
# Fit new waterfall ribbons to the actual outlet channels of the generated cave, NOT the old lava axes.
falls=[{'x':64,'top_x':58,'top_y':86,'width':25,'foot_y':196},{'x':152,'top_x':140,'top_y':68,'width':25,'foot_y':164},{'x':216,'top_x':216,'top_y':53,'width':20,'foot_y':119},{'x':264,'top_x':264,'top_y':53,'width':20,'foot_y':119},{'x':327,'top_x':339,'top_y':68,'width':25,'foot_y':164},{'x':417,'top_x':424,'top_y':86,'width':25,'foot_y':196}]
obstacles=solid|rock;shore=nd.binary_dilation(obstacles,iterations=2)&~obstacles
static=rockgroups+platform
# Shadow stays on water; platform itself is unchanged by water or foam layers.
shadowmask=nd.binary_dilation(solid,iterations=4)&~solid;sh=np.zeros((H,W,4),dtype='uint8');sh[:,:,:3]=[18,62,79];sh[:,:,3]=shadowmask*75;sh[sh[:,:,3]==0]=0;static.insert(0,('02_ombre_arene',Image.fromarray(sh)))
def animated(t):
 phase=t%N;theta=2*np.pi*phase/N;dx=np.rint(2*np.sin(theta+yy*.03)).astype(int);dy=np.rint(2*np.cos(theta+xx*.025)).astype(int);wa=watertex[(yy+dy)%H,(xx+dx)%W].copy();wa[:,:,3]=255;water=Image.fromarray(wa)
 border=np.zeros_like(wa);border[:,:,:3]=[180,223,223];border[:,:,3]=np.where(shore,48+np.rint(18*np.sin(2*np.pi*phase/40+xx*.1)).astype(int),0).astype('uint8');border[border[:,:,3]==0]=0
 streams=[];foams=[];waves=[]
 for k,f in enumerate(falls):
  x,w,foot=f['x'],f['width'],f['foot_y'];top=f['top_y'];cx=f['top_x']+(x-f['top_x'])*np.clip((yy-top)/22,0,1);u=xx-cx
  mask=(np.abs(u)<=w/2)&(yy>=top)&(yy<foot)&~obstacles
  tex=motifs[k%4];tx=np.clip(np.rint((u/w+.5)*31),0,31).astype(int);ty=(yy-top-2*phase)%80
  arr=tex[ty,tx].copy();arr[:,:,3]=mask*255;arr[~mask]=0;streams.append((f'10_cascade_{k+1:02}',Image.fromarray(arr)))
  # Generated foam shape phases, independent from each waterfall. No procedural stand-in silhouette.
  pose=foammotifs[((phase//5)+k)%4];fw=w+17;fh=17;pose=pose.resize((fw,fh),Image.Resampling.NEAREST)
  foam=Image.new('RGBA',(W,H));foam.alpha_composite(pose,(x-fw//2,foot-7));fa=np.array(foam);fa[obstacles]=0;foams.append((f'20_ecume_impact_{k+1:02}',Image.fromarray(fa)));cy=foot+2
  wave=Image.new('RGBA',(W,H));d=ImageDraw.Draw(wave)
  for j in range(2):
   age=(phase+j*10)%20;rad=w*.55+age*.8;alpha=round(135*(1-age/20));d.arc((x-rad,cy-rad*.35,x+rad,cy+rad*.35),0,180,fill=(171,226,230,alpha),width=1)
  aa=np.array(wave);aa[obstacles]=0;waves.append((f'30_remous_{k+1:02}',Image.fromarray(aa)))
 return [('01_eau_bassin',water),('07_liseres_eau_pierre',Image.fromarray(border))]+streams+foams+waves

def layers(t):
 anim=animated(t);return [anim[0]]+static+anim[1:]
for n,im in static:im.save(P/f'aqua_{n}.png')
frames=[]
for t in range(N):
 ls=layers(t)
 for n,im in animated(t):im.save(P/f'aqua_{n}_{t:03}.png')
 im=compose(ls);im.save(P/f'aqua_composition_{t:03}.png');frames.append(im)
frames[0].save(P/'COMPOSITION.png');frames[0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[1:],duration=DT,lossless=True,loop=0)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'arene_aquatique_bois.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for i,(n,im) in reversed(list(enumerate(layers(0)))):
  fn=f'data/{i}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
m={'size':[W,H],'source':'images.png','reference_commit':'3b96b74399b53f4b772139df9e977e30e5b72e66','frames':N,'frame_ms':DT,'loop_ms':N*DT,'falls':falls,'static':[n for n,_ in static],'animated':[n for n,_ in animated(0)],'order':[n for n,_ in layers(0)],'provenance':{'platform':'previous generated stone/timber sprite fitted170x180 at155,132 to new cavern layout','rocks':'new generated cavern and foreground borders, keyed magenta,4 independent rock regions','water':'new generated20color full-canvas water background, periodic bounded2px warp','falls_foam_ripples':'generated waterfall and foam sprites; falling texture translated2px/frame in fitted outlet masks,4 foam poses, procedural expanding ripples; artistic animation not native nor fluid simulation'},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')}]
for n,im in static:items.append({'name':n,'src':uri(png(im))})
for i,(n,_) in enumerate(animated(0)):
 ims=[load(P/f'aqua_{n}_{t:03}.png') for t in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=DT,loop=0,lossless=True);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Antre des cascades · pierre et bois</title><style>body{background:#162e39;color:#e2f1ee;font:16px system-ui;max-width:1000px;margin:30px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:960px;max-width:100%;background:repeating-conic-gradient(#29434f 0 25%,#355967 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#335460;color:white}</style><h1>Antre des cascades · décor généré</h1><p>Parois et bordures rocheuses générées pour former un antre. Six cascades générées ajustées aux ouvertures ; écumes générées à part. Fond d’eau et roches du bas indépendants. Arène circulaire et passerelle sud en bois, couronne de pierre grise. Nouvelle adaptation PMD guidée par la référence volcanique ; pas de revendication de sprites officiels ni de test moteur.</p><select id="sel"></select><br><img id="view" alt="Arène aquatique"><script>const items='''+json.dumps(items)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>view.src=items[+sel.value].src;</script>'''
(R/'apercu_antre_cascades_v2.html').write_text(html)
print('Built',len(layers(0)),'layers,',N,'frames')
