"""Smaller native Altere platform; regenerated water/falls; authored 4/3/8 clocks."""
from pathlib import Path
import sys,io,json,zipfile,base64,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];REF=R/'source/antre_harmonie_v3/references';O=R/'renders/antre_bassin_v4';P=O/'antre';S=O/'sprites';P.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
sys.path.insert(0,str(R/'source/amp_plains_fleurie_v1'));from inspect_references import decode
W,H=480,312;N=24;yy,xx=np.mgrid[:H,:W];NN=Image.Resampling.NEAREST;OLD=R/'renders/antre_harmonie_v3/antre'
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def full(im,xy):
 o=Image.new('RGBA',(W,H));o.alpha_composite(im,xy);return o
def compose(ls):
 im=Image.new('RGBA',(W,H))
 for _,l in ls:im.alpha_composite(l)
 return im
# Preserve the approved Crooked-style walls exactly. Do not regenerate their layout.
rocknames=['02_paroi_fond','03_bordure_gauche','04_bordure_droite','05_rebord_bas'];rocks=[(n,load(OLD/f'harmonie_{n}.png')) for n in rocknames];rock=np.maximum.reduce([np.array(im)[:,:,3] for _,im in rocks])>0
# Actual8key platform animation from Altere's Objects layer, backed by the Metano atlas.
path=R/'source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile';size,bank=decode(path);atlas=Image.new('RGBA',(512,1408))
for (x,y),im in bank.items():atlas.alpha_composite(im,(8*x,8*y))
mapobj=json.loads((REF/'altere_pond.rsground').read_text(encoding='utf-8-sig'))['Object'];proof=mapobj['Layers'][5]['Tiles'][67][44]['Layers'][0]
assert proof['FrameLength']==10 and len(proof['Frames'])==8
native=[];origin=(184,178)
for p in range(8):
 x=112*(p%4);y=984+144*(p//4);im=atlas.crop((x,y,x+112,y+144));im.save(S/f'plateforme_native_complete_{p:02}.png');native.append(np.array(im))
ref=native[0];rr,gg,bb=ref[:,:,:3].astype(float).transpose(2,0,1);stone=(rr>=gg*.8)&(ref[:,:,3]>0);labels,num=nd.label(stone,np.ones((3,3)));assert num==4
stone0=np.array(cut(ref,stone));nearest=nd.distance_transform_edt(~stone,return_distances=False,return_indices=True);regions=labels[nearest[0],nearest[1]]
for a in native:
 r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mask=(r>=g*.8)&(a[:,:,3]>0);assert np.array_equal(np.array(cut(a,mask)),stone0)
# Static stone pixels are copied1:1, not reduced generated pixels. Water/shadows have their own4layers.
platform=[('06_disque_natif',full(cut(ref,labels==1),origin))]+[(f'07_pas_japonais_{k}',full(cut(ref,labels==k+1),origin)) for k in range(1,4)]
static=rocks+platform;solid=np.maximum.reduce([np.array(im)[:,:,3] for _,im in platform])>0;dry=rock|solid
nativecontacts=[]
for phase in range(8):
 arr=native[phase].copy();arr[stone]=0;layers=[]
 for k in range(1,5):
  im=full(cut(arr,regions==k),origin);a=np.array(im);a[dry]=0;layers.append((f'08_reflets_natifs_{"disque" if k==1 else "pas_"+str(k-1)}',Image.fromarray(a)))
 nativecontacts.append(layers)
# Regenerated basin: four actual keyframes, not a repeated flat native crop.
raw=load(O/'bruts/bassin_quatre_poses.png');waters=[];watercolors=[]
for j in range(2):
 for i in range(2):
  im=key(raw.crop((i*raw.width//2,j*raw.height//2,(i+1)*raw.width//2,(j+1)*raw.height//2)));box=im.getbbox();im=im.crop((box[0]+3,box[1]+3,box[2]-3,box[3]-3)).resize((W,H),NN);a=np.array(im);assert np.all(a[:,:,3]==255);waters.append(im);watercolors.append(a[:,:,:3].reshape(-1,3))
# One common small palette prevents per-pose brightness/palette changes.
strip=Image.new('RGB',(W*4,H))
for p,im in enumerate(waters):strip.paste(im.convert('RGB'),(p*W,0))
pal=strip.quantize(colors=12,method=Image.Quantize.MEDIANCUT)
waters=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA') for im in waters]
for p,im in enumerate(waters):im.save(S/f'bassin_regenere_{p:02}.png')
# Generated4pose cascade silhouettes and impact tongues. Reference texture restores small native-style detail.
sheet=key(load(O/'bruts/cascades_quatre_poses_magenta.png'));sa=np.array(sheet);spans=nd.find_objects(nd.label((sa[:,:,3]>0).sum(axis=0)>10)[0]);assert len(spans)==4
motifs=[];fallrefs=[np.array(load(REF/f'chute_native_{p}.png')) for p in range(4)];foams=[load(REF/f'ecume_native_{p}.png') for p in range(3)]
colors=np.unique(np.concatenate([a[:,:,:3][a[:,:,3]>0] for a in fallrefs]+[np.array(im)[:,:,:3][np.array(im)[:,:,3]>0] for im in foams]),axis=0);ctree=cKDTree(colors)
for p,(sl,) in enumerate(spans):
 im=sheet.crop((sl.start,0,sl.stop,sheet.height));im=im.crop(im.getbbox()).resize((40,112),NN);a=np.array(im);im.save(S/f'cascade_generee_pose_{p:02}.png');motifs.append(a)
falls=json.loads((R/'renders/antre_harmonie_v3/manifest.json').read_text())['falls']
# All feet overlap their native foam by5pixels; flaring occurs only near the contact, never through rock.
fallimgs=[];foamimgs=[]
for phase in range(4):
 layers=[]
 for k,f in enumerate(falls):
  top=f['top_y'];foot=f['foot_y'];rel=np.clip((yy-top)/max(foot-top,1),0,1);center=f['top_x']+(f['x']-f['top_x'])*np.clip((yy-top)/18,0,1);u=xx-center
  flare=np.clip((rel-.82)/.18,0,1);width=f['width']*(1+.42*flare);tx=np.clip(np.rint((u/width+.5)*39),0,39).astype(int);ty=np.clip(np.rint(rel*111),0,111).astype(int)
  gen=motifs[phase][ty,tx].copy();nat=fallrefs[phase][np.clip(yy-top,0,111),np.clip(np.rint(24+u),0,47).astype(int)]
  #70% native fine material on the body, tapering out toward the generated white contact tongue.
  weight=.7*(1-flare);rgb=np.rint(gen[:,:,:3]*(1-weight[:,:,None])+nat[:,:,:3]*weight[:,:,None]);_,ids=ctree.query(rgb);gen[:,:,:3]=colors[ids]
  mask=(np.abs(u)<=width/2)&(yy>=top)&(yy<foot+5)&~dry;gen[~mask]=0
  layers.append((f'10_cascade_{k+1}',Image.fromarray(gen)))
 fallimgs.append(layers)
for phase in range(3):
 ls=[]
 for k,f in enumerate(falls):
  sp=foams[phase].resize((48,28),NN);im=full(sp,(f['x']-24,f['foot_y']-8));a=np.array(im);a[dry]=0;ls.append((f'20_ecume_{k+1}',Image.fromarray(a)))
 foamimgs.append(ls)
def animated(p):return [('00_bassin_regenere',waters[p%4])]+nativecontacts[p%8]+fallimgs[p%4]+foamimgs[p%3]
def layers(p):
 an=animated(p);return [an[0]]+rocks+nativecontacts[p%8]+platform+fallimgs[p%4]+foamimgs[p%3]
for n,im in static:im.save(P/f'bassin4_{n}.png')
frames=[];dur=[round((p+1)*1000/6)-round(p*1000/6) for p in range(N)]
for p in range(N):
 for n,im in animated(p):im.save(P/f'bassin4_{n}_{p:02}.png')
 im=compose(layers(p));assert np.all(np.array(im)[:,:,3]==255);im.save(P/f'bassin4_composition_{p:02}.png');frames.append(im)
frames[0].save(P/'COMPOSITION.png');frames[0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'antre_bassin_v4.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for i,(n,im) in reversed(list(enumerate(layers(0)))):
  fn=f'data/{i}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
m={'size':[W,H],'frames':N,'durations_ms':dur,'loop_ms':4000,'game_frames_per_pose':10,'cycles':{'basin_generated':4,'cascades_regenerated':4,'foam_native_adapted':3,'platform_water_native':8},'static':[n for n,_ in static],'animated':[n for n,_ in animated(0)],'order':[n for n,_ in layers(0)],'falls':falls,'platform':{'origin':list(origin),'source_rects':[[112*(p%4),984+144*(p//4),112*(p%4)+112,1128+144*(p//4)] for p in range(8)],'disc_native_bbox':[20,9,92,62],'disc_size':[72,53],'previous_disc_size':[160,106],'stone_pixels_unchanged':True,'scale':1},'native_platform_proof':proof,'native_atlas_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'material':'generated4key basin;4generated cascade silhouettes blended with native fine texture, mapped to native fall/foam colors; native3key foam fitted50%; full8key native platform water separated from static stones','runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION.webp').read_bytes(),'image/webp')}]
for n,im in static:items.append({'name':n,'src':uri(png(im))})
for n,_ in animated(0):
 ims=[load(P/f'bassin4_{n}_{p:02}.png') for p in range(N)];b=io.BytesIO();ims[0].save(b,format='WEBP',save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Antre · bassin animé V4</title><style>body{background:#292c29;color:#f1eddc;max-width:1000px;margin:30px auto;padding:0 20px;font:16px system-ui}p{line-height:1.6}img{image-rendering:pixelated;width:960px;max-width:100%;background:repeating-conic-gradient(#3a4643 0 25%,#4c5952 0 50%) 0/16px 16px}select{padding:10px;margin:10px;background:#4b5549;color:white}</style><h1>Antre · bassin animé · V4</h1><p>Disque réduit à sa taille native72×53px, pierres immobiles, cycle natif complet de8poses pour les rides/reflets. Bassin et cascades régénérés en4poses, écume native adaptée en3poses. Boucle commune4secondes, calques indépendants.</p><select id="sel"></select><br><img id="view" alt="Antre au bassin dégagé"><p>Les parois Crooked de la V3 sont conservées. Les cascades régénérées sont des adaptations, pas des sprites officiels. Les pierres et leurs rides sont des pixels natifs à échelle1. Aucun test PMDO.</p><script>const items='''+json.dumps(items)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>view.src=items[+sel.value].src;</script>'''
(R/'apercu_antre_bassin_v4.html').write_text(html)
print('Built',len(layers(0)),'layers;24states;4/3/8cycles;4s; native72x53disc')
