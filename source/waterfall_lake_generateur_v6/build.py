"""Local waterfall material/inset repair; preserve approved V4 outside the three chutes."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_generateur_v6';OLD=R/'renders/waterfall_lake_encastrees_v5';S=O/'sprites';S.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
W,H,N=504,360,24;yy,xx=np.mgrid[:H,:W];m0=json.loads((OLD/'manifest.json').read_text());dur=m0['durations_ms']
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for _,im in ls:out.alpha_composite(im)
 return out
raw=np.array(load(O/'bruts/raccords_generes.png').resize((W,H),Image.Resampling.NEAREST));r,g,b=raw[:,:,:3].astype(float).transpose(2,0,1)
base=load(OLD/'jour/COMPOSITION.png');channels={};overlay=np.zeros_like(raw);repair=np.zeros((H,W),bool)
for k,(lo,hi,cx) in enumerate([(87,156,128),(348,417,376)]):
 region=(xx>=lo)&(xx<hi)&(yy>=18)&(yy<144);flow=region&(yy<129)&(b-r>22)&(g>80)&(b>g)
 labs,num=nd.label(flow,np.ones((3,3)));counts=np.bincount(labs.ravel());counts[0]=0;flow=labs==counts.argmax();ys=np.flatnonzero(flow.any(axis=1));mask=np.zeros((H,W),bool)
 for y in range(int(ys.min()),144):
  xs=np.flatnonzero(flow[min(y,int(ys.max()))]);
  if not len(xs):xs=np.flatnonzero(flow[int(ys.max())])
  mask[y,xs[0]:xs[-1]+1]=True
 # Keep the original foam and every lower-lake pixel; integrate only upper channel rock.
 dry=region&(yy<129)&~mask;overlay[dry]=raw[dry];repair|=region;channels[1 if k==0 else 3]=mask
 Image.fromarray((mask*255).astype('uint8')).save(S/f'lake6_canal_{k}.png')
Image.fromarray(overlay).save(S/'lake6_raccords_roche_generes.png');Image.fromarray((repair*255).astype('uint8')).save(O/'MASQUE_RETOUCHE.png')
refs=R/'source/antre_harmonie_v3/references';native=[np.array(load(refs/f'chute_native_{p}.png'))[:96] for p in range(4)]
remove=['07b_levres_rocheuses','07c_ombres_encastrement'];static=[n for n in m0['static'] if n not in remove]+['06b_raccords_roche_generes'];animated=m0['animated']
def waterfall(k,p):
 mask=channels[k];ys=np.flatnonzero(mask.any(axis=1));a=np.zeros_like(raw)
 for y in ys:
  xs=np.flatnonzero(mask[y]);tx=np.rint(np.linspace(0,47,len(xs))).astype(int);sy=round((y-ys[0])*95/(ys[-1]-ys[0]));a[y,xs]=native[p%4][sy,tx]
 return Image.fromarray(a)
def layers(p):
 ls=[]
 for n in m0['layer_order']:
  if n in remove:continue
  if n=='07_cascade_1':ls.append(('06b_raccords_roche_generes',Image.fromarray(overlay)))
  im=waterfall(int(n[-1]),p) if n in ['07_cascade_1','07_cascade_3'] else load(OLD/'jour'/(f'lake5_jour_{n}_{p:02}.png' if n in animated else f'lake5_jour_{n}.png'))
  ls.append((n,im))
 return ls
order=[n for n,_ in layers(0)];frames={}
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)];im=merge(ls);assert np.all(np.array(im)[:,:,3]==255)
  for n,l in ls:
   if p==0 or n in animated:l.save(P/(f'lake6_{mode}_{n}_{p:02}.png' if n in animated else f'lake6_{mode}_{n}.png'))
  im.save(P/f'lake6_{mode}_composition_{p:02}.png');frames[mode].append(im)
  if p==0:
   im.save(P/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'lake6_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
m=dict(m0,layer_order=order,static=static,animated=animated,parent='waterfall_lake_encastrees_v5',rock='Local side rock recesses and water contours extracted from a new generator pass; other V5 layers preserved.',water='Native Altere River four-phase material, fitted in height and central width; side cropped. Border shades quantized to native water palette. Adapted native material, not untouched native sprites.',runtime_validated=False)
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
data={}
for mode in frames:
 P=O/mode;items=[dict(name='V6 — composition animée',src=uri((P/'ANIMATION.webp').read_bytes(),'image/webp')),dict(name='V5 — avant correction',src=uri((OLD/mode/'ANIMATION.webp').read_bytes(),'image/webp'))]
 for n in order:
  if n in animated:
   ims=[load(P/f'lake6_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);u=uri(b.getvalue(),'image/webp')
  else:u=uri((P/f'lake6_{mode}_{n}.png').read_bytes())
  items.append(dict(name=n,src=u))
 data[mode]=items
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake V6</title><style>body{background:#172c32;color:#eef3e6;font:16px system-ui;max-width:1080px;margin:32px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:8px;background:#355863;color:white}</style><h1>Waterfall Lake V6 — cascades encastrées</h1><p>Motifs natifs PMD en quatre phases, noyau clair et bords ombrés. Raccords latéraux repassés au générateur : ouvertures creusées et eau extraite des mêmes contours rocheux. Demi-cercle, bassin, plateforme et écume Métano conservés.</p><select id="mode"><option>jour</option><option>nuit</option></select><select id="sel"></select><br><img id="view" alt="Cascades PMD encastrées"><p>Matière native adaptée à la géométrie des trois chutes ; ce ne sont pas des sprites natifs intacts. Nuit exacte Abyss. Aucun test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script></html>'''
(R/'apercu_waterfall_lake_generateur_v6.html').write_text(html)
print('Built',len(order),'layers,48scenes')
