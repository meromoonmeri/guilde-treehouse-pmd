from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_aquatique_bois_v1';P=O/'arene';S=O/'sprites';P.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
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
im=key(load(O/'bruts/arene_pierre_bois_magenta.png'));im=im.crop(im.getbbox()).resize((204,240),Image.Resampling.NEAREST);im.save(S/'arene_pierre_bois.png');full=Image.new('RGBA',(W,H));full.alpha_composite(im,(138,72));pa=np.array(full);pr,pg,pb=pa[:,:,:3].astype(float).transpose(2,0,1);solid=pa[:,:,3]>0
wood=solid&(pr>pg*1.15)&(pg>pb*1.13);bridge=solid&(yy>=248)&(np.abs(xx-240)<35);floor=wood&~bridge;rim=solid&~floor&~bridge
platform=[('04_couronne_pierre_humide',cut(pa,rim)),('05_plancher_arene_bois',cut(pa,floor)),('06_passerelle_sud',cut(pa,bridge))]
assert np.array_equal(np.array(compose(platform)),pa)
# Original surrounding boulder contours retained, remapped to wet slate. Do not keep old arena spikes.
rois=[(126,37,43,22),(354,37,43,22),(134,114,23,22),(346,114,23,22),(110,251,27,24),(370,251,27,24),(0,222,27,35),(479,222,27,35),(0,67,26,23),(479,67,26,23),(19,168,22,20),(461,168,22,20)]
rock=np.zeros((H,W),bool)
for x,y,rx,ry in rois:rock|=((xx-x)/rx)**2+((yy-y)/ry)**2<=1
rock &= (r<151)&(g<97)&~solid
lum=.2126*r+.7152*g+.0722*b;stone=a.copy();ramp=np.array([[30,49,59],[53,76,84],[83,112,116],[128,157,153],[182,202,187]])
for j in range(3):stone[:,:,j]=np.interp(lum,[0,35,65,100,155],ramp[:,j]).astype('uint8')
rocks=cut(stone,rock)
# Reuse previously generated PMD-style water material; no lava pattern remains in the pool.
raw=load(R/'renders/siphons_ecoulement_v3/bruts/eau_matiere.png').resize((W,H),Image.Resampling.NEAREST)
v=np.array(raw)[:,:,:3]@np.array([.2126,.7152,.0722]);lo,hi=np.percentile(v,[2,99]);idx=np.clip(np.rint((v-lo)/(hi-lo)*7),0,7).astype('uint8');Image.fromarray(idx*32).save(S/'indices_matiere_reference.png')
poolpalette=np.array([[33+i*4,105+i*5,133+i*5] for i in range(8)],dtype='uint8')
palette=np.array([[28,81,107],[32,99,123],[37,119,140],[48,139,158],[66,158,173],[91,177,186],[128,199,200],[168,219,216]],dtype='uint8')
# Six falling columns preserve the reference positions, widths and vertical lengths.
falls=[{'x':31,'width':14,'foot_y':99},{'x':79,'width':30,'foot_y':150},{'x':200,'width':15,'foot_y':43},{'x':280,'width':15,'foot_y':43},{'x':400,'width':30,'foot_y':150},{'x':449,'width':14,'foot_y':99}]
obstacles=solid|rock;shore=nd.binary_dilation(obstacles,iterations=2)&~obstacles
static=[('03_rochers_peripheriques',rocks)]+platform
# Shadow stays on water; platform itself is unchanged by water or foam layers.
shadowmask=nd.binary_dilation(solid,iterations=4)&~solid;sh=np.zeros((H,W,4),dtype='uint8');sh[:,:,:3]=[18,62,79];sh[:,:,3]=shadowmask*75;sh[sh[:,:,3]==0]=0;static.insert(0,('02_ombre_arene',Image.fromarray(sh)))
def animated(t):
 phase=t%N;wa=np.zeros((H,W,4),dtype='uint8');theta=2*np.pi*phase/N;dx=np.rint(2*np.sin(theta+yy*.03)).astype(int);dy=np.rint(2*np.cos(theta+xx*.025)).astype(int);base=idx[(yy+dy)%H,(xx+dx)%W];wa[:,:,:3]=poolpalette[base];wa[:,:,3]=255
 # Small drifting horizontal highlights share the water palette, never cross dry objects.
 highlights=(base>=6)&((xx+yy)%5==0)&~obstacles;wa[highlights,:3]=poolpalette[7]
 water=Image.fromarray(wa)
 border=np.zeros_like(wa);border[:,:,:3]=[180,223,223];border[:,:,3]=np.where(shore,48+np.rint(18*np.sin(2*np.pi*phase/40+xx*.1)).astype(int),0).astype('uint8');border[border[:,:,3]==0]=0
 streams=[];foams=[];waves=[]
 for k,f in enumerate(falls):
  x,w,foot=f['x'],f['width'],f['foot_y'];arr=np.zeros_like(wa);u=xx-x;mask=(np.abs(u)<=w/2)&(yy<foot)&~solid
  val=np.clip(np.rint(3+1.5*np.cos(u*1.1)+1.5*np.sin((yy-2*phase)*np.pi/8+u*.38)),0,7).astype('uint8');arr[:,:,:3]=palette[val];arr[:,:,3]=mask*255
  streak=(np.mod(yy-2*phase+np.abs(u)*2,16)<3)&mask;arr[streak,:3]=[172,221,227];edge=mask&(np.abs(u)>w/2-2);arr[edge,:3]=[105,183,205];arr[~mask]=0;streams.append((f'10_cascade_{k+1:02}',Image.fromarray(arr)))
  foam=Image.new('RGBA',(W,H));d=ImageDraw.Draw(foam);cy=foot+2
  # Persistent aerated impact, irregular perimeter and small timed splash droplets.
  for j in range(13):
   theta=2*np.pi*j/13;rad=w*.48+3+2*np.sin(2*np.pi*phase/10+j*1.7);cx=x+round(np.cos(theta)*rad);fy=cy+round(np.sin(theta)*5);rr=2+(j%3);d.ellipse((cx-rr,fy-2,cx+rr,fy+2),fill=(214,246,247,230))
  d.ellipse((x-w*.40,cy-4,x+w*.40,cy+3),fill=(236,252,251,245))
  for j in range(4):
   age=(phase+j*3+k)%10;dx=(-1 if j%2 else 1)*(w*.3+age*.7);dy=-np.sin(np.pi*age/10)*8;cx=round(x+dx);fy=round(cy+dy);d.rectangle((cx,fy,cx+1,fy+1),fill=(225,250,251,230))
  fa=np.array(foam);fa[obstacles]=0;foams.append((f'20_ecume_impact_{k+1:02}',Image.fromarray(fa)))
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
m={'size':[W,H],'source':'images.png','reference_commit':'3b96b74399b53f4b772139df9e977e30e5b72e66','frames':N,'frame_ms':DT,'loop_ms':N*DT,'falls':falls,'static':[n for n,_ in static],'animated':[n for n,_ in animated(0)],'order':[n for n,_ in layers(0)],'provenance':{'platform':'generated, magenta keyed, resized204x240, placed138,72; gray stone, timber arena and bridge separated','rocks':'reference boulder pixels within documented regions, recolored wet slate','water':'previously generated siphons_ecoulement_v3 water material, reindexed to8color pool palette, periodic bounded2px warp; adapted material, NOT native water','falls_foam_ripples':'procedural animation, reference cascade positions; artistic2D not fluid simulation'},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')}]
for n,im in static:items.append({'name':n,'src':uri(png(im))})
for i,(n,_) in enumerate(animated(0)):
 ims=[load(P/f'aqua_{n}_{t:03}.png') for t in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=DT,loop=0,lossless=True);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Arène aquatique · pierre et bois</title><style>body{background:#162e39;color:#e2f1ee;font:16px system-ui;max-width:1000px;margin:30px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:960px;max-width:100%;background:repeating-conic-gradient(#29434f 0 25%,#355967 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#335460;color:white}</style><h1>Arène aquatique · pierre humide et bois</h1><p>Six cascades séparées, écume au pied et remous indépendants. Arène circulaire et passerelle sud en bois, couronne de pierre grise. Nouvelle adaptation PMD guidée par la référence volcanique ; pas de revendication de sprites officiels ni de test moteur.</p><select id="sel"></select><br><img id="view" alt="Arène aquatique"><script>const items='''+json.dumps(items)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>view.src=items[+sel.value].src;</script>'''
(R/'apercu_arene_aquatique_bois_v1.html').write_text(html)
print('Built',len(layers(0)),'layers,',N,'frames')
