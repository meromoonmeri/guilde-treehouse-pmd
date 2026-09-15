from pathlib import Path
import sys,json,io,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];REF=Path(__file__).parent/'references';O=R/'renders/antre_harmonie_v3';P=O/'antre';P.mkdir(parents=True,exist_ok=True);S=O/'sprites';S.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=480,312;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def fitpalette(im,reference):
 a=np.array(im);b=np.array(reference);colors=np.unique(b[:,:,:3][b[:,:,3]>0],axis=0);_,ids=cKDTree(colors).query(a[:,:,:3]);a[:,:,:3]=colors[ids];a[a[:,:,3]==0]=0;return Image.fromarray(a)
def full(im,xy):
 o=Image.new('RGBA',(W,H));o.alpha_composite(im,xy);return o
# Generated forms, but a shared exact reference palette, not arbitrary blue/slate recoloring.
rockref=load(R/'source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png').crop((0,0,320,110))
cave=key(load(O/'bruts/parois_crooked_magenta.png')).resize((W,H),NN);cave=fitpalette(cave,rockref);ca=np.array(cave)
# Open narrow southern inlet under the three native stepping stones.
ca[(yy>=240)&(np.abs(xx-240)<24)]=0;cave=Image.fromarray(ca);rock=ca[:,:,3]>0
static=[('02_paroi_fond',cut(ca,yy<132)),('03_bordure_gauche',cut(ca,(yy>=132)&(yy<277)&(xx<240))),('04_bordure_droite',cut(ca,(yy>=132)&(yy<277)&(xx>=240))),('05_rebord_bas',cut(ca,yy>=277))]
objects=load(REF/'altere_layer_5.png');refdisk=objects.crop((504,336,584,392));refdisk.save(S/'plateforme_altere_source.png')
disk=key(load(O/'bruts/plateforme_altere_magenta.png'));disk=disk.crop(disk.getbbox()).resize((160,106),NN);disk=fitpalette(disk,refdisk);disk.save(S/'plateforme_adaptee.png');da=np.array(full(disk,(160,137)));dmask=da[:,:,3]>0;top=(da[:,:,:3].mean(axis=2)>175)&dmask
platform=[('07_surface_pierre_claire',cut(da,top)),('06_tranche_plateforme',cut(da,dmask&~top))]
for k in range(3):
 sprite=objects.crop((528,392+24*k,560,416+24*k));sprite.save(S/f'pas_japonais_natif_{k}.png');platform.append((f'08_pas_japonais_{k+1}',full(sprite,(224,240+24*k))))
solid=np.maximum.reduce([np.array(im)[:,:,3] for _,im in platform])>0
shadow=nd.binary_dilation(solid,iterations=3)&~solid&~rock;sh=np.zeros((H,W,4),dtype='uint8');sh[:,:,:3]=[48,100,105];sh[:,:,3]=shadow*65;sh[~shadow]=0;static=[('01b_ombre_pierre',Image.fromarray(sh))]+static+platform
falls=[{'x':64,'top_x':58,'top_y':92,'width':25,'foot_y':156},{'x':152,'top_x':140,'top_y':75,'width':25,'foot_y':164},{'x':216,'top_x':216,'top_y':57,'width':20,'foot_y':119},{'x':264,'top_x':264,'top_y':57,'width':20,'foot_y':119},{'x':327,'top_x':339,'top_y':75,'width':25,'foot_y':164},{'x':417,'top_x':424,'top_y':92,'width':25,'foot_y':156}]
water=[np.array(load(REF/f'eau_native_{p}.png')) for p in range(4)];assert all(np.all(a[:,:,3]==255) for a in water)
chutes=[np.array(load(REF/f'chute_native_{p}.png')) for p in range(4)];foam=[load(REF/f'ecume_native_{p}.png') for p in range(3)]
def animated(phase):
 # Exact4/3 authored cycles,10gameframes per pose, no scrolling generated texture.
 out=[('00_eau_altere',Image.fromarray(water[phase%4][yy%32,xx%32]))]
 for k,f in enumerate(falls):
  top=f['top_y'];foot=f['foot_y'];center=f['top_x']+(f['x']-f['top_x'])*np.clip((yy-top)/18,0,1);u=np.rint(xx-center).astype(int);mask=(np.abs(u)<=f['width']/2)&(yy>=top)&(yy<foot)&~rock&~solid
  # Native-scale central strip, bent by integer offsets only; no vertical resizing or scroll.
  tex=chutes[phase%4];tx=np.clip(24+u,0,47);ty=np.clip(yy-top,0,111);arr=tex[ty,tx].copy();arr[~mask]=0
  out.append((f'10_cascade_{k+1}',Image.fromarray(arr)))
  # Full native foam composition retains its3poses and timing; fitted at half-size to the narrower outlets.
  sp=foam[phase%3].resize((48,28),NN);im=full(sp,(f['x']-24,foot-8));a=np.array(im);a[rock|solid]=0;out.append((f'20_ecume_{k+1}',Image.fromarray(a)))
 return out

def layers(p):
 anim=animated(p);return [anim[0]]+static+anim[1:]
def compose(ls):
 im=Image.new('RGBA',(W,H))
 for _,layer in ls:im.alpha_composite(layer)
 return im
for n,im in static:im.save(P/f'harmonie_{n}.png')
frames=[];durations=[round((i+1)*1000/6)-round(i*1000/6) for i in range(12)]
for p in range(12):
 for n,im in animated(p):im.save(P/f'harmonie_{n}_{p:02}.png')
 im=compose(layers(p));im.save(P/f'harmonie_composition_{p:02}.png');frames.append(im)
frames[0].save(P/'COMPOSITION.png');frames[0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'antre_harmonie.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(n,im) in reversed(list(enumerate(layers(0)))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
m={'size':[W,H],'static':[n for n,_ in static],'animated':[n for n,_ in animated(0)],'order':[n for n,_ in layers(0)],'frames':12,'durations_ms':durations,'loop_ms':2000,'game_frames_per_pose':10,'native_cycles':{'waterfall':4,'foam':3},'falls':falls,'native_reference':'Halcyon Altere Pond, commit1522c7a8b7a34d70078e11ed605b21d563b0dc51','cave':'generated Crooked-guided form, palette mapped to existing native Crooked rock colors','platform':'generated wider Altere disc, mapped to native disc colors;3native stepping stones unchanged','cascade_adaptation':'native central24px strip follows new fitted masks; no resized/scrolled texture','foam_adaptation':'native3poses fitted at50percent nearest-neighbor; no procedural foam','runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(b,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(b).decode()
items=[{'name':'Composition harmonisée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')}]
for n,im in static:items.append({'name':n,'src':uri(png(im))})
for n,_ in animated(0):
 ims=[load(P/f'harmonie_{n}_{p:02}.png') for p in range(12)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=durations,lossless=True,loop=0);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Antre harmonisé · Crooked / Altere / Métano</title><style>body{background:#292c29;color:#f1eddc;max-width:1000px;margin:30px auto;padding:0 20px;font:16px system-ui}p{line-height:1.6}img{image-rendering:pixelated;width:960px;max-width:100%;background:repeating-conic-gradient(#3a4643 0 25%,#4c5952 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#4b5549;color:white}</style><h1>Antre harmonisé · V3</h1><p>Roche ocre-gris inspirée de Crooked Cavern, disque de pierre claire d’après Altere Pond et pas japonais natifs. Cascades à4phases, écumes de Métano à3phases : même cadence native de10frames de jeu, boucle commune de2secondes. Fond d’eau et calques séparés.</p><select id="sel"></select><br><img id="view" alt="Antre harmonisé"><p>Formes rocheuses et disque adaptés par génération ; animations récupérées dans les ressources Halcyon. Écume réduite à50% pour ces chutes étroites. Aucun test PMDO.</p><script>const items='''+json.dumps(items)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>view.src=items[+sel.value].src;</script>'''
(R/'apercu_antre_harmonie_v3.html').write_text(html)
print('Built',len(layers(0)),'layers;12states;native4/3cycles;2s')
