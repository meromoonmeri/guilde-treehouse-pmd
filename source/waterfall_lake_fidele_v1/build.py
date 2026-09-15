"""Conservative native-pixel Waterfall Lake edit, with a small mirrored perimeter only."""
from pathlib import Path
import io,json,sys,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_fidele_v1';S=O/'sprites';S.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/amp_plains_fleurie_v1'));from inspect_references import decode
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
SOURCE='Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png'
W,H=504,360;OX,OY=24,16;N=24;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def full(im,xy):
 a=Image.new('RGBA',(W,H));a.alpha_composite(im,xy);return a
def merge(ls):
 im=Image.new('RGBA',(W,H))
 for n,layer in ls:im.alpha_composite(layer)
 return im
original=load(R/SOURCE);src=np.array(original);assert original.size==(456,312)
# Conservative24px side/16px upper/32px lower continuation from original edge pixels.
# The entire original rectangle is retained at scale1; no central generator output is used.
base=np.pad(src,((16,32),(24,24),(0,0)),mode='reflect');rr,gg,bb=base[:,:,:3].astype(float).transpose(2,0,1)
core=(xx>=OX)&(xx<OX+456)&(yy>=OY)&(yy<OY+312);extension=~core
# Original central rock removed only within its own small silhouette, even beneath the new platform.
island=(xx>=OX+204)&(xx<OX+254)&(yy>=OY+160)&(yy<OY+212)&(rr>15)&(bb<gg*1.12)
near=nd.distance_transform_edt(island,return_distances=False,return_indices=True);base[island]=base[near[0,island],near[1,island]]
# Native source waterfall and foam are isolated, not substituted with the rejected redrawn lake.
r,g,b=base[:,:,:3].astype(float).transpose(2,0,1)
fall=(xx>=OX+180)&(xx<OX+268)&(yy<OY+64)&(r<100)&(g>60)&(b>120)
foam=(xx>=OX+176)&(xx<OX+272)&(yy>=OY+48)&(yy<OY+81)&(r>120)&(g>180)&(b>180)
# Pixel-color based native lake surface, retaining all depth rings without palette replacement.
blue=(r<70)&(b>120)&((b>g*1.05)|(g>150));labs,num=nd.label(blue,np.ones((3,3)));pool_label=labs[OY+220,OX+228];water=(labs==pool_label)|fall|foam
bright=(r>100)&(g>180)&(b>180);water|=bright&nd.binary_dilation(water,iterations=1)
# Rebuild just the foam underlay from neighboring water, not from dry-bank pixels.
plain=water&~foam&~fall;inds=nd.distance_transform_edt(~plain,return_distances=False,return_indices=True);under=base.copy();under[foam]=base[inds[0,foam],inds[1,foam]]
# Complete water background under independently layered terrain (hidden surfaces inferred).
inds=nd.distance_transform_edt(~water,return_distances=False,return_indices=True);under[~water]=base[inds[0,~water],inds[1,~water]]
# Neutral body color under the animated waterfall, so displaced foam never reveals old white pixels.
under[fall]=src[10,220]
terrain=~water
cliffs=terrain&(yy<OY+110)&(xx>=OX+100)&(xx<=OX+350)&(r>g*.9)&(b<g*.85)
grass=terrain&~cliffs&(g>b*1.15)&(r>g*.38)
foliage=terrain&~cliffs&~grass
masks=[('02_roche_cascade',cliffs),('03_herbe_berges',grass),('04_vegetation_arriere',foliage&(yy<OY+205)),('05_canopy_avant_gauche',foliage&(yy>=OY+205)&(xx<W//2)),('06_canopy_avant_droite',foliage&(yy>=OY+205)&(xx>=W//2))]
static=[('01_eau_profondeurs_originales',Image.fromarray(under))]+[(n,cut(base,m)) for n,m in masks]
# Extract original GBA material. A48px vertical cycle moves downward by2px per pose.
# Original silhouette and top/bottom planes stay fixed. This reconstructs motion from a static reference.
material=src[4:52,188:264].copy();aquatic=(material[:,:,0]<100)&(material[:,:,1]>60)&(material[:,:,2]>120);material[:,:,:3]=np.where(aquatic[:,:,None],material[:,:,:3],src[10,220,:3]);material[:,:,3]=255
Image.fromarray(material).save(S/'matiere_cascade_gba.png')
fallframes=[];foamframes=[]
for p in range(N):
 a=np.zeros((H,W,4),dtype='uint8');coords_y=(yy-OY-2*p)%48;coords_x=np.clip(xx-OX-188,0,75);a[fall]=material[coords_y[fall],coords_x[fall]];fallframes.append(Image.fromarray(a))
for phase in range(3):
 # One-pixel local swelling of the native froth; original impact position does not translate.
 a=np.zeros((H,W,4),dtype='uint8')
 for x in range(OX+176,OX+272):
  ys=np.flatnonzero(foam[:,x]);shift=0 if phase==0 else (1 if (x//3+phase)%3==0 else -1 if (x//4+phase)%4==0 else 0)
  for y in ys:
   ny=y+shift
   if 0<=ny<H and water[ny,x]:a[ny,x]=base[y,x]
 # Keep a small original attachment region at the impact's back edge.
 back=foam&(yy<OY+64);a[back]=base[back];foamframes.append(Image.fromarray(a))
# Native Altere/Metano platform: original8poses, separate immobile stone surfaces and moving water.
size,bank=decode(R/'source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile');atlas=Image.new('RGBA',(512,1408))
for (x,y),tile in bank.items():atlas.alpha_composite(tile,(x*8,y*8))
platform_native=[np.array(atlas.crop((112*(p%4),984+144*(p//4),112*(p%4)+112,1128+144*(p//4)))) for p in range(8)]
a=platform_native[0];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);stone=(a[:,:,3]>0)&(r>=g*.8);labels,n=nd.label(stone,np.ones((3,3)));assert n==4
nearest=nd.distance_transform_edt(~stone,return_distances=False,return_indices=True);regions=labels[nearest[0],nearest[1]]
origin=(OX+172,OY+152)
platform=[('10_disque_altere',full(cut(a,labels==1),origin))]+[(f'11_pas_japonais_{k}',full(cut(a,labels==k+1),origin)) for k in range(1,4)]
# Three more copies continue the stepping-stone approach through the southern crop boundary.
for k in range(3):
 sp=np.array(cut(a,labels==4))[110:144,32:80];platform.append((f'11_pas_japonais_{k+4}',full(Image.fromarray(sp),(origin[0]+32,origin[1]+134+24*k))))
stone_mask=np.maximum.reduce([np.array(im)[:,:,3] for _,im in platform])>0
# Terrain is never repainted to make room: source water at every stone position is checked separately.
assert not np.any(stone_mask&terrain)
platformcontacts=[]
for phase,ar in enumerate(platform_native):
 r,g,b=ar[:,:,:3].astype(float).transpose(2,0,1);mask=(ar[:,:,3]>0)&(r>=g*.8);assert np.array_equal(np.array(cut(ar,mask)),np.array(cut(a,stone)))
 arr=ar.copy();arr[stone]=0;ls=[]
 for k in range(1,5):
  im=full(cut(arr,regions==k),origin);aa=np.array(im);aa[terrain|stone_mask]=0;ls.append((f'12_reflets_altere_{k}',Image.fromarray(aa)))
 for k in range(3):
  sp=np.array(cut(arr,regions==4))[110:144,32:80];im=full(Image.fromarray(sp),(origin[0]+32,origin[1]+134+24*k));aa=np.array(im);aa[terrain|stone_mask]=0;ls.append((f'12_reflets_altere_{k+5}',Image.fromarray(aa)))
 platformcontacts.append(ls)
# Save immutable terrain/stone and modification masks for review against the provided source.
for name,mask in [('source_preservee',core),('extension_peripherique',extension),('rocher_retire',island),('cascade',fall),('ecume_originale',foam)]:Image.fromarray((mask*255).astype('uint8')).save(O/f'MASQUE_{name}.png')
static+=platform
all_effect=np.maximum.reduce([np.array(im)[:,:,3] for ls in platformcontacts for _,im in ls])>0
all_foam=np.maximum.reduce([np.array(im)[:,:,3] for im in foamframes])>0
allowed=island|stone_mask|all_effect|fall|foam|all_foam|extension
Image.fromarray((allowed*255).astype('uint8')).save(O/'MASQUE_MODIFICATIONS_AUTORISEES.png')

def layers(p):return static[:6]+[('07_cascade_descendante',fallframes[p]),('08_ecume_impact',foamframes[p%3])]+platformcontacts[p%8]+platform
# static[:6] is exactly water+the five original terrain partitions.
frames={'jour':[],'nuit':[]};durations=[round((p+1)*1000/6)-round(p*1000/6) for p in range(N)]
for mode in frames:
 path=O/mode;path.mkdir(exist_ok=True)
 for p in range(N):
  ls=[(n,night(im) if mode=='nuit' else im) for n,im in layers(p)]
  for n,im in ls:
   animated=n.startswith(('07_','08_','12_'))
   if animated or p==0:im.save(path/(f'lake_{mode}_{n}_{p:02}.png' if animated else f'lake_{mode}_{n}.png'))
  im=merge(ls);frames[mode].append(im);im.save(path/f'lake_{mode}_composition_{p:02}.png')
  if mode=='jour':
   aa=np.array(im);assert np.array_equal(aa[~allowed],base[~allowed])
  assert np.all(np.array(im)[:,:,3]==255)
  if p==0:
   im.save(path/'COMPOSITION.png');root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(path/f'waterfall_lake_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(n,l) in reversed(list(enumerate(ls))):
     fn=f'data/{i}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
 frames[mode][0].save(path/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=durations,loop=0,lossless=True)
# A strict original-size view is supplied too: no framing/extension imposed on the user.
for mode,ims in frames.items():
 crops=[im.crop((OX,OY,OX+456,OY+312)) for im in ims];crops[0].save(O/mode/'COMPOSITION_CADRE_ORIGINAL.png');crops[0].save(O/mode/'ANIMATION_CADRE_ORIGINAL.webp',save_all=True,append_images=crops[1:],duration=durations,loop=0,lossless=True)
m={'source':SOURCE,'source_size':[456,312],'size':[W,H],'source_origin':[OX,OY],'padding':[24,16,24,32],'extension_method':'native edge pixels reflected only outside original rectangle; no central regeneration','frames':N,'durations_ms':durations,'loop_ms':4000,'layer_order':[n for n,_ in layers(0)],'static':[n for n,_ in static],'animated':['07_cascade_descendante','08_ecume_impact']+[n for n,_ in platformcontacts[0]],'platform_origin':list(origin),'steps':6,'source_unchanged_pixels_each_frame':int((core&~allowed).sum()),'source_total_pixels':456*312,'night':'existing Abyss filter used for Northern; applied consistently per layer, not a native GBA night asset','waterfall':'reconstructed downward motion from original static GBA material;2px per pose;48px period','foam':'local1px swelling from original GBA foam,3poses;not recovered native temporal data','native_platform_cycle':8,'runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
data={}
for mode in frames:
 path=O/mode;items=[{'name':'Composition animée · cadrage original','src':uri((path/'ANIMATION_CADRE_ORIGINAL.webp').read_bytes(),'image/webp')},{'name':'Composition animée · bordures étendues','src':uri((path/'ANIMATION.webp').read_bytes(),'image/webp')},{'name':'Référence originale · comparaison','src':uri(png(original if mode=='jour' else night(original)))}]
 for n,_ in layers(0):
  if n in m['animated']:
   ims=[load(path/f'lake_{mode}_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=durations,lossless=True,loop=0);srcuri=uri(b.getvalue(),'image/webp')
  else:srcuri=uri((path/f'lake_{mode}_{n}.png').read_bytes())
  items.append({'name':n,'src':srcuri})
 data[mode]=items
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Waterfall Lake · édition fidèle</title><style>body{background:#162a31;color:#edf1db;font:16px system-ui;max-width:1080px;margin:30px auto;padding:0 20px}p{line-height:1.6}img{image-rendering:pixelated;width:1008px;max-width:100%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#355863;color:white}</style><h1>Waterfall Lake · édition fidèle jour/nuit</h1><p>L’image GBA originale reste à son échelle. Seul le rocher central est remplacé par la plateforme d’Altere, avec six pierres d’accès indépendantes. Cascade descendante et écume séparées. Extension limitée à la périphérie, sans redessiner le lac.</p><select id="mode"><option value="jour">Jour</option><option value="nuit">Nuit</option></select><select id="sel"></select><br><img id="view" alt="Waterfall Lake fidèle"><p>La première génération étendue a été écartée. Les animations de la chute et de l’écume sont reconstruites depuis l’image statique ; le cycle de8poses autour des pierres est natif. Nuit via le filtre déjà utilisé pour Northern. Pas de test PMDO.</p><script>const data='''+json.dumps(data)+''';function setup(){sel.replaceChildren();data[mode.value].forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=data[mode.value][0].src}view.onload=()=>view.style.width=(view.naturalWidth*2)+'px';mode.onchange=setup;sel.onchange=()=>view.src=data[mode.value][+sel.value].src;setup();</script>'''
(R/'apercu_waterfall_lake_fidele_v1.html').write_text(html)
print('Built',len(layers(0)),'layers,day/night; preserved',m['source_unchanged_pixels_each_frame'],'/',456*312,'core pixels each frame')
