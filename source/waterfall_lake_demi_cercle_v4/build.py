from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_demi_cercle_v4';OLD=R/'renders/waterfall_lake_trois_v2';S=O/'sprites';S.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
W,H,N=504,360,24; yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST;m0=json.loads((OLD/'manifest.json').read_text());dur=m0['durations_ms']
def load(p):return Image.open(p).convert('RGBA')
def full(im,xy=(0,0)):
 out=Image.new('RGBA',(W,H));out.alpha_composite(im,xy);return out
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def merge(ls):
 out=Image.new('RGBA',(W,H))
 for _,im in ls:out.alpha_composite(im)
 return out
src=np.array(load(R/m0['source']));r,g,b=src[:,:,:3].astype(float).transpose(2,0,1)
pal=np.unique(src[:100,120:336,:3][(r[:100,120:336]>g[:100,120:336]*1.08)&(b[:100,120:336]<g[:100,120:336]*.9)],axis=0)
a=np.array(full(key(load(O/'bruts/falaise_demi_cercle_sans_eau.png')).resize((504,200),NN)));rock=a[:,:,3]>0
_,idx=cKDTree(pal).query(a[:,:,:3]);a[:,:,:3]=pal[idx];a[~rock]=0
Image.fromarray(a).save(S/'lake4_falaise_seule.png')
cliffs=[(f'06_falaise_{n}',cut(a,mask&rock)) for n,mask in [('fond',yy<60),('gauche',(yy>=60)&(xx<168)),('centre',(yy>=60)&(xx>=168)&(xx<336)),('droite',(yy>=60)&(xx>=336))]]
# Independent generated water guide is registered row-by-row onto outlets of dry relief.
raw=np.array(key(load(O/'bruts/cascades_matiere_magenta.png')));rh,rw=raw.shape[:2]
material=np.array(load(R/'renders/waterfall_lake_fidele_v1/sprites/matiere_cascade_gba.png'))
channels=[]
for k,(cx,top,bottom,width,lo,hi) in enumerate([(128,28,137,48,0,.34),(252,0,109,64,.35,.65),(376,28,137,48,.66,1)]):
 sub=raw[:,int(rw*lo):int(rw*hi)];sm=sub[:,:,3]>0;ys=np.flatnonzero(sm.any(axis=1));mask=np.zeros((H,W),bool);centers=np.full(H,cx,dtype=int)
 for y in range(top,bottom+1):
  row=int(np.interp(y,[top,bottom],[ys[0],ys[-1]]));xs=np.flatnonzero(sm[row]);assert len(xs)
  bend=round(20*max(0,1-(y-top)/42)) if k!=1 else 0;c=cx+(-bend if k==0 else bend);centers[y]=c
  # Width taper follows generated silhouette, rather than a hard rectangle.
  w=max(width-4,min(width,round(width*len(xs)/max(1,np.median(sm.sum(axis=1)[ys])))))
  mask[y,c-w//2:c+(w+1)//2]=True
 channels.append(dict(mask=mask,centers=centers,foot=[cx,bottom],top=top,width=width))
 Image.fromarray((mask*255).astype('uint8')).save(S/f'lake4_masque_cascade_{k+1}.png')
terrain=[(n,load(OLD/f'jour/lake2_jour_{n}.png')) for n in m0['static'] if n.startswith(('03_','04_','05_','06_canopy'))]
platform=[(n,load(OLD/f'jour/lake2_jour_{n}.png')) for n in m0['static'] if n.startswith(('10_','11_'))]
contacts=[n for n in m0['animated'] if n.startswith('12_')]
refs=R/'source/antre_harmonie_v3/references';foams=[load(refs/f'ecume_native_{p}.png') for p in range(3)]
for p,im in enumerate(foams):im.save(S/f'lake4_ecume_metano_native_{p}.png')
def layers(p):
 ls=[('01_eau_anneaux',load(OLD/f'jour/lake2_jour_01_eau_anneaux_{p:02}.png'))]+terrain+cliffs
 for k,ch in enumerate(channels):
  ar=np.zeros((H,W,4),dtype=np.uint8);mask=ch['mask'];u=xx-ch['centers'][:,None]+38
  ar[mask]=material[(yy[mask]-2*p)%48,np.clip(u[mask],0,75)]
  ls.append((f'07_cascade_{k+1}',Image.fromarray(ar)))
 for k,ch in enumerate(channels):
  cx,bottom=ch['foot'];# Native 96x56 motif, same pixels, no resizing/recoloring/cropping.
  ls.append((f'08_ecume_metano_{k+1}',full(foams[p%3],(cx-48,bottom-14))))
 ls += [(n,load(OLD/f'jour/lake2_jour_{n}_{p:02}.png')) for n in contacts]+platform
 return ls
order=[n for n,_ in layers(0)];static=[n for n,_ in terrain+cliffs+platform];animated=[n for n in order if n not in static];frames={}
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)];im=merge(ls);assert np.all(np.array(im)[:,:,3]==255)
  for n,l in ls:
   if p==0 or n in animated:l.save(P/(f'lake4_{mode}_{n}_{p:02}.png' if n in animated else f'lake4_{mode}_{n}.png'))
  im.save(P/f'lake4_{mode}_composition_{p:02}.png');frames[mode].append(im)
  if p==0:
   im.save(P/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'lake4_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
manifest=dict(size=[W,H],frames=N,durations_ms=dur,loop_ms=sum(dur),layer_order=order,static=static,animated=animated,source=m0['source'],parent='waterfall_lake_trois_v2',cascade_count=3,channels=[dict(foot=c['foot'],top=c['top'],width=c['width']) for c in channels],rock='Generated dry semicircular layout and texture inspired by original; nearest original rock colors. Not native tiles.',water='Separate generated guide registered to outlets; original GBA 76x48 material advected down 2px per pose; reconstructed animation.',foam='Exact native96x56 Metano foam from Altere Objects Over,3poses/10ticks, translated only; no recoloring or resampling in day.',native_reference_commit='1522c7a8b7a34d70078e11ed605b21d563b0dc51',runtime_validated=False)
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
data={}
for mode in frames:
 P=O/mode;items=[dict(name='Composition animée',src=uri((P/'ANIMATION.webp').read_bytes(),'image/webp'))]
 for n in order:
  if n in animated:
   ims=[load(P/f'lake4_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);u=uri(b.getvalue(),'image/webp')
  else:u=uri((P/f'lake4_{mode}_{n}.png').read_bytes())
  items.append(dict(name=n,src=u))
 data[mode]=items
extras=[('Original',R/m0['source']),('Sélection : demi-cercle sans les chutes',O/'GUIDE_LAYOUT_504.png'),('Nouveau relief sans eau',S/'lake4_falaise_seule.png')]+[(p.stem,p) for p in sorted((O/'origine_decomposee').glob('origine_*.png'))]
data['étapes']=[dict(name=n,src=uri(p.read_bytes())) for n,p in extras]
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake V4 · demi-cercle</title><style>body{background:#172c32;color:#eef3e6;font:16px system-ui;max-width:1080px;margin:32px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:8px;background:#355863;color:white}a{color:#b9e9db}</style><h1>Waterfall Lake V4 — grand demi-cercle</h1><p>Original décomposé → relief seul → trois cascades raccordées → écume native Métano. Nouveau massif continu au fond et sur les côtés ; accès sud, disque d’Altere, pas japonais et animation douce du lac conservés.</p><select id="mode"><option>jour</option><option>nuit</option><option>étapes</option></select><select id="sel"></select><br><img id="view" alt="Aperçu du nouveau demi-cercle"><p>Roche générée d’après la référence GBA, palette originale : pas des tuiles natives. Matière des chutes issue de l’original, animation reconstruite. Écume Métano : trois poses natives, sans redimensionnement. Filtre nocturne exact Abyss. Aucun test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script></html>'''
(R/'apercu_waterfall_lake_demi_cercle_v4.html').write_text(html)
print('Built',len(order),'layers,48scenes')
