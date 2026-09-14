"""Non-destructive corrections. Run with Pillow, numpy, scipy installed."""
from pathlib import Path
import io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2]; O=R/'renders/corrections_eau_canopy_v1'; OLD=R/'renders/layouts_magenta_v1'
O.mkdir(parents=True,exist_ok=True)
def load(p): return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def compose(layers):
 out=Image.new('RGBA',layers[0][1].size)
 for _,im in layers: out.alpha_composite(im)
 return out
def ora(path,layers,c):
 root=ET.Element('image',w=str(c.width),h=str(c.height));stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in reversed(list(enumerate(layers))):
   src=f'data/{i}.png';ET.SubElement(stack,'layer',name=name,src=src,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'});z.writestr(src,png(im))
  z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(c))
 with zipfile.ZipFile(path) as z:
  st=ET.fromstring(z.read('stack.xml')).find('stack')
  assert np.array_equal(np.array(compose([(n.attrib['name'],load(io.BytesIO(z.read(n.attrib['src'])))) for n in reversed(st)])),np.array(c))
def save_scene(ident,title,layers,groups,notes):
 p=O/ident;p.mkdir(exist_ok=True);lf=[];gf=[]
 for name,im in layers:
  fn=f'{ident}_{name}.png';im.save(p/fn);lf.append({'name':name,'file':fn})
 for name,ims,dt in groups:
  files=[]
  for i,im in enumerate(ims):
   fn=f'{ident}_{name}_{i:03}.png';im.save(p/fn);files.append(fn)
  gf.append({'name':name,'files':files,'duration_ms':dt})
 first=[(name,ims[0]) for name,ims,_ in groups]+layers
 c=compose(first);assert np.all(np.array(c)[:,:,3]==255);c.save(p/'COMPOSITION.png');ora(p/f'{ident}.ora',first,c)
 frames=[]
 if groups:
  for t in range(0,1440,60):
   frame=compose([(name,ims[(t//dt)%len(ims)]) for name,ims,dt in groups]+layers)
   assert np.all(np.array(frame)[:,:,3]==255)
   frame.save(p/f'{ident}_scene_{t//60:03}.png');frames.append(frame)
  frames[0].save(p/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=60,loop=0,lossless=True)
  assert len({png(f) for f in frames})==24
 scenes.append({'id':ident,'title':title,'size':list(c.size),'layers':lf,'animation_groups':gf,'notes':notes,'complete_frames':len(frames),'cycle_ms':1440 if groups else 0})
scenes=[]
# Whole former sand floor is removed: no old ground, contact shadow or reference transition layer.
p=OLD/'variantes/sables_siphons_eau';size=(456,384);w,h=size
water=load(O/'bruts/eau_surface.png').resize(size,Image.Resampling.NEAREST).convert('RGB').quantize(colors=20).convert('RGB')
a=np.array(water).astype(float);lum=a@np.array([.2126,.7152,.0722]);base=np.zeros((h,w,4),dtype='uint8');base[:,:,3]=255
for j,values in enumerate([(14,27,75),(75,124,193),(107,150,205)]):base[:,:,j]=np.interp(lum,[20,80,190],values).astype('uint8')
yy,xx=np.mgrid[:h,:w];waters=[]
for i in range(12):
 b=base.copy();delta=np.rint(3*np.sin(2*np.pi*i/12+yy/19+xx/73))
 b[:,:,:3]=np.clip(b[:,:,:3].astype(float)+delta[:,:,None],0,255).astype('uint8');waters.append(Image.fromarray(b))
siphons=[load(p/f'sables_siphons_eau_01_siphons_eau_adaptes_{i:03}.png') for i in range(6)]
rocks=[]
for name in ['04_rochers_arriere','05_rochers_avant','06_galet_decale']:
 im=load(p/f'sables_siphons_eau_{name}.png');a=np.array(im);light=a[:,:,:3]@np.array([.2126,.7152,.0722])
 for j,offset in enumerate([0,5,12]): a[:,:,j]=np.clip(light*.86+offset,0,255).astype('uint8')
 a[a[:,:,3]==0]=0;rocks.append((name,Image.fromarray(a)))
mask=np.maximum.reduce([np.array(im)[:,:,3] for _,im in rocks]);shadow=Image.fromarray(mask).filter(ImageFilter.GaussianBlur(2));sa=np.zeros((h,w,4),dtype='uint8');sa[:,:,:3]=[7,49,76];sa[:,:,3]=(np.array(shadow)*.38).astype('uint8');sa[sa[:,:,3]==0]=0
layers=[('03_ombres_rochers_sur_eau',Image.fromarray(sa))]+rocks
save_scene('eau_integrale_rochers_gris','Eau intégrale · rochers gris bleutés',layers,[('01_surface_eau',waters,120),('02_siphons',siphons,60)],'Tout le sol est une nouvelle plaque d’eau générée et animée en 12 phases. Aucun ancien sol, sable ou raccord jaune conservé. Siphons : adaptation des 6 phases de sable, pas une animation d’eau native. Rochers et ombres séparés.')
# Native foreground silhouettes from the newly supplied Southern Jungle reference.
ref=load(R/'Southern_Jungle_entrance_S.png');a=np.array(ref);dark=(a[:,:,0]==7)&(a[:,:,1]<=39)&(a[:,:,2]==23);labels,n=nd.label(dark,np.ones((3,3)));ids=set(labels[:,0])|set(labels[:,-1]);ids.discard(0);mask=np.isin(labels,list(ids));a[~mask]=0
native=Image.fromarray(a);native.save(O/'canopy_source_alpha.png')
magenta=Image.new('RGBA',ref.size,(255,0,255,255));magenta.alpha_composite(native);magenta.convert('RGB').save(O/'canopy_source_magenta.png')
canopy=native.resize((504,480),Image.Resampling.NEAREST)
bases=json.loads((OLD/'manifest.json').read_text())['scenes']
for parent,label in [('foret_mousse_doree','mousse'),('foret_emeraude','emeraude')]:
 entry=next(e for e in bases if e['id']==parent);p=OLD/'zones'/parent;layers=[(l['name'],load(p/l['file'])) for l in entry['layers']];arr=np.array(canopy)
 # Same native silhouette geometry for both palettes, no twig sprites.
 arr[arr[:,:,3]>0,:3]+=np.array([2,4,1] if label=='mousse' else [0,0,4],dtype='uint8')
 assert not np.any(arr[:,202:302,3])
 for name,start,end in [('08_canopy_gauche',0,252),('09_canopy_droite',252,504)]:
  b=arr.copy();b[:,:start]=0;b[:,end:]=0;layers.append((name,Image.fromarray(b)))
 save_scene(f'foret_{label}_canopy',f'Forêt {label} · cadre de canopée',layers,[], 'Masses de feuillage sombre au premier plan extraites de Southern_Jungle_entrance_S.png (commit 46e93da), puis mises à hauteur 480 en nearest-neighbor et accordées à la palette. Pas une nouvelle génération de rameaux. Gauche/droite séparées ; passage central libre. Layout de base généré sur magenta conservé.')
manifest={'scenes':scenes,'runtime_pmdo_validated':False,'gpu_validated':False,'tests':{'opaque_compositions':True,'ora_exact_recomposition':True,'water_complete_frames_unique':24,'canopy_central_100px_clear':True,'old_sand_layers_used':False}}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Self-contained viewer: animations, pause, and individual layers.
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Eau intégrale et cadre de canopée</title><style>body{background:#101d22;color:#e0eee9;font:16px system-ui;margin:28px auto;max-width:1100px;padding:0 20px}h1{font-size:28px}section{border-top:1px solid #39504d;padding:24px 0}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#24383e 0 25%,#34494b 0 50%) 0/16px 16px}button,select{padding:10px;margin:8px 8px 12px 0;background:#263e43;color:white;border:1px solid #66847b;border-radius:6px}p{line-height:1.6;color:#bdd0ca}</style><h1>Eau intégrale & cadre de canopée</h1><p>Corrections séparées des versions précédentes. PNG, calques transparents et OpenRaster dans renders/corrections_eau_canopy_v1/. Animation d’eau reconstruite ; pas de test PMDO.</p>'''
payload=[]
for s in scenes:
 p=O/s['id'];items=[{'name':'Composition animée' if s['complete_frames'] else 'Composition','src':'data:image/'+('webp' if s['complete_frames'] else 'png')+';base64,'+base64.b64encode((p/('ANIMATION_COMPLETE.webp' if s['complete_frames'] else 'COMPOSITION.png')).read_bytes()).decode()}]
 for l in s['layers']: items.append({'name':l['name'],'src':'data:image/png;base64,'+base64.b64encode((p/l['file']).read_bytes()).decode()})
 for g in s['animation_groups']:
  for f in g['files']: items.append({'name':f,'src':'data:image/png;base64,'+base64.b64encode((p/f).read_bytes()).decode()})
 still='data:image/png;base64,'+base64.b64encode((p/'COMPOSITION.png').read_bytes()).decode();payload.append({'title':s['title'],'notes':s['notes'],'items':items,'still':still})
html+='<main id="main"></main><script>const scenes='+json.dumps(payload,ensure_ascii=False)+''';for(const s of scenes){const sec=document.createElement('section');const title=document.createElement('h2');title.textContent=s.title;sec.append(title);const text=document.createElement('p');text.textContent=s.notes;sec.append(text);const select=document.createElement('select');s.items.forEach((x,i)=>{const o=new Option(x.name,i);select.add(o)});const im=new Image();im.src=s.items[0].src;im.alt=s.title;select.onchange=()=>{im.src=s.items[select.value].src;button.textContent='Pause / image fixe'};sec.append(select);const button=document.createElement('button');button.textContent='Pause / image fixe';button.onclick=()=>{const paused=button.textContent==='Reprendre';im.src=paused?s.items[select.value].src:s.still;button.textContent=paused?'Pause / image fixe':'Reprendre'};sec.append(button,document.createElement('br'),im);main.append(sec)}</script>'''
(R/'apercu_corrections_eau_canopy_v1.html').write_text(html)
print(json.dumps(manifest['tests'],indent=2))
