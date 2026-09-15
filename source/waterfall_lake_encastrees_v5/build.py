"""Local waterfall material/inset repair; preserve approved V4 outside the three chutes."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_encastrees_v5';OLD=R/'renders/waterfall_lake_demi_cercle_v4';S=O/'sprites';S.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
W,H,N=504,360,24;yy,xx=np.mgrid[:H,:W];m0=json.loads((OLD/'manifest.json').read_text());dur=m0['durations_ms']
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for _,im in ls:out.alpha_composite(im)
 return out
rock=np.array(load(OLD/'sprites/lake4_falaise_seule.png'))
references=R/'source/antre_harmonie_v3/references';native=[np.array(load(references/f'chute_native_{p}.png'))[:96] for p in range(4)]
for p,a in enumerate(native):Image.fromarray(a).save(S/f'lake5_matiere_native_{p}.png')
waterpal=np.unique(native[0][:,:,:3].reshape(-1,3),axis=0);tree=cKDTree(waterpal)
rockpal=np.unique(rock[:,:,:3][rock[:,:,3]>0],axis=0);rtree=cKDTree(rockpal)
channels=[];occlusion=np.zeros_like(rock);shade=np.zeros_like(rock);repair=np.zeros((H,W),bool)
for k,ch in enumerate(m0['channels']):
 old=np.array(load(OLD/f'sprites/lake4_masque_cascade_{k+1}.png'))[:,:,0]>0;mask=old.copy();lefts=np.zeros(H,int);rights=np.zeros(H,int)
 for y in range(ch['top'],ch['foot'][1]+1):
  xs=np.flatnonzero(old[y]);l,r=int(xs[0]),int(xs[-1]);local=y-ch['top']
  if k!=1:
   # Unmoving stepped rock intrusions follow source ledges; a narrower inlet lies behind the upper lip.
   taper=max(0,9-local//2);a=4+[0,1,3,2,0,2,1][(local//7)%7]+taper;b=4+[2,0,1,3,1,0][(local//9)%6]+taper
   l+=a;r-=b;mask[y]=False;mask[y,l:r+1]=True
  lefts[y],rights[y]=l,r
 if k!=1:
  bank=old&~mask&(rock[:,:,3]>0);occlusion[bank]=rock[bank]
  # A 2px recess shadow on the actual exposed cliff pixels, no added freestanding pillars.
  inner=nd.binary_dilation(mask,iterations=2)&bank
  _,idx=rtree.query(rock[:,:,:3].astype(float)*.62);shade[inner,:3]=rockpal[idx[inner]];shade[inner,3]=255
 repair|=old
 channels.append(dict(mask=mask,left=lefts,right=rights,**ch))
 Image.fromarray((mask*255).astype('uint8')).save(S/f'lake5_canal_{k+1}.png')
Image.fromarray(occlusion).save(S/'lake5_levres_rocheuses.png');Image.fromarray(shade).save(S/'lake5_ombres_encastrement.png');Image.fromarray((repair*255).astype('uint8')).save(O/'MASQUE_RETOUCHE.png')
static=m0['static']+['07b_levres_rocheuses','07c_ombres_encastrement'];animated=m0['animated']
def waterfall(k,p):
 ch=channels[k];a=np.zeros_like(rock);ref=native[p%4];top=ch['top'];bottom=ch['foot'][1]
 for y in range(top,bottom+1):
  l,r=ch['left'][y],ch['right'][y];width=r-l+1
  # Native four-phase motifs, fitted to channel length. Side width cropped rather than stretched.
  sy=round((y-top)*95/(bottom-top));tx=np.clip(np.arange(width)+(48-width)//2,0,47) if width<=48 else np.rint(np.linspace(0,47,width)).astype(int)
  a[y,l:r+1]=ref[sy,tx]
  # Side-wall depth uses only the same native water ramp, keeping the bright falling core.
  for j in range(min(3,width//2)):
   for x in [l+j,r-j]:
    _,idx=tree.query(a[y,x,:3].astype(float)*([.58,.73,.88][j] if k!=1 else [.76,.87,.96][j]));a[y,x,:3]=waterpal[idx]
 return Image.fromarray(a)
def layers(p):
 ls=[]
 for n in m0['layer_order']:
  if n.startswith('07_cascade_'):im=waterfall(int(n[-1])-1,p)
  else:im=load(OLD/'jour'/(f'lake4_jour_{n}_{p:02}.png' if n in animated else f'lake4_jour_{n}.png'))
  if n=='08_ecume_metano_1':ls += [('07b_levres_rocheuses',Image.fromarray(occlusion)),('07c_ombres_encastrement',Image.fromarray(shade))]
  ls.append((n,im))
 return ls
order=[n for n,_ in layers(0)];frames={}
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)];im=merge(ls);assert np.all(np.array(im)[:,:,3]==255)
  for n,l in ls:
   if p==0 or n in animated:l.save(P/(f'lake5_{mode}_{n}_{p:02}.png' if n in animated else f'lake5_{mode}_{n}.png'))
  im.save(P/f'lake5_{mode}_composition_{p:02}.png');frames[mode].append(im)
  if p==0:
   im.save(P/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'lake5_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
m=dict(m0,layer_order=order,static=static,animated=animated,parent='waterfall_lake_demi_cercle_v4',rock='Approved V4 intact; original rock pixels form foreground channel lips, original rock palette forms narrow recess shadows.',water='Native Altere River four-phase material, fitted in height and central width; side cropped. Border shades quantized to native water palette. Adapted native material, not untouched native sprites.',runtime_validated=False)
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
data={}
for mode in frames:
 P=O/mode;items=[dict(name='V5 — composition animée',src=uri((P/'ANIMATION.webp').read_bytes(),'image/webp')),dict(name='V4 — avant correction',src=uri((OLD/mode/'ANIMATION.webp').read_bytes(),'image/webp'))]
 for n in order:
  if n in animated:
   ims=[load(P/f'lake5_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);u=uri(b.getvalue(),'image/webp')
  else:u=uri((P/f'lake5_{mode}_{n}.png').read_bytes())
  items.append(dict(name=n,src=u))
 data[mode]=items
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake V5</title><style>body{background:#172c32;color:#eef3e6;font:16px system-ui;max-width:1080px;margin:32px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:8px;background:#355863;color:white}</style><h1>Waterfall Lake V5 — cascades encastrées</h1><p>Motifs natifs PMD en quatre phases, noyau clair et bords ombrés. Sorties latérales resserrées, lèvres rocheuses irrégulières devant l’eau et ombres de renfoncement. Demi-cercle, bassin, plateforme et écume Métano conservés.</p><select id="mode"><option>jour</option><option>nuit</option></select><select id="sel"></select><br><img id="view" alt="Cascades PMD encastrées"><p>Matière native adaptée à la géométrie des trois chutes ; ce ne sont pas des sprites natifs intacts. Nuit exacte Abyss. Aucun test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script></html>'''
(R/'apercu_waterfall_lake_encastrees_v5.html').write_text(html)
print('Built',len(order),'layers,48scenes')
