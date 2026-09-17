from pathlib import Path
import json,hashlib,zipfile,io,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];S=R/'source/zones_pmd_20_v1/references';O=R/'renders/references_fideles_v1';O.mkdir(parents=True,exist_ok=True)
refs=json.loads((S/'sources.json').read_text());manifest={'reference_commit':'8eb46bc','approach':'Reference pixels preserved; disjoint visible-surface layers, not reconstructed hidden scenery','scenes':[]};report=[]
# Polygons delimit depth zones only. No source pixel is translated, resized or repainted.
FLOOR={
1:[(.42,.41),(.58,.41),(.65,.49),(.62,.63),(.7,.77),(.6,1),(.4,1),(.3,.77),(.36,.64),(.35,.5)],
2:[(.37,0),(.61,0),(.59,.23),(.65,.40),(.59,.58),(.68,.8),(.65,1),(.29,1),(.31,.79),(.40,.61),(.34,.45),(.39,.25)],
3:[(.40,.22),(.61,.22),(.71,.4),(.62,.63),(.57,1),(.31,1),(.32,.77),(.43,.56),(.33,.42)],
4:[(0,.42),(.55,.43),(.8,.36),(1,.5),(1,.66),(.77,.77),(.43,.74),(0,.74)],
5:[(.41,0),(.57,0),(.59,.28),(.73,.51),(.82,1),(.14,1),(.2,.7),(.35,.5),(.41,.29)],
6:[(.35,.23),(.62,.23),(.76,.45),(.67,.71),(.61,1),(.29,1),(.30,.75),(.20,.53),(.26,.35)],
7:[(.43,0),(.61,0),(.61,.23),(.83,.55),(.88,1),(.12,1),(.19,.63),(.33,.35)],
9:[(0,0),(1,0),(1,.72),(.82,.81),(.74,1),(.32,1),(.22,.79),(0,.64)],
10:[(.35,0),(.64,0),(.62,.26),(.72,.46),(.60,.65),(.69,.85),(.64,1),(.30,1),(.32,.8),(.40,.62),(.31,.43),(.4,.22)],
11:[(.43,0),(.58,0),(.6,.35),(.61,.64),(.63,1),(.32,1),(.4,.71),(.35,.48),(.43,.27)],
12:[(.36,.39),(.55,.38),(.67,.52),(.59,.70),(.62,1),(.29,1),(.36,.79),(.28,.56)],
13:[(.43,.27),(.61,.27),(.65,.37),(.83,.44),(.99,.44),(1,.78),(.78,.89),(.55,.91),(.32,.82),(.20,.60),(.27,.44)],
14:[(.07,.56),(.80,.55),(.91,.38),(.93,.77),(.09,.83)],
15:[(.42,.39),(.62,.39),(.89,.64),(1,1),(0,1),(.06,.68),(.27,.54)]}
TITLES={0:'Fond nocturne fourni',1:'Entrée cascade',2:'D05P11A · chemin fruitier',3:'D05P31A · clairière fruitière',4:'D07P11A · corniche rocheuse',5:'D11P11A · passage gris',6:'D12P41A · cirque gris',7:'D13P11A · défilé désertique',9:'D14P11A · bassins de sable',10:'D17P33A · passage cristallin',11:'D24P11A · forêt à racines',12:'D24P31A · clairière à racines',13:'D25P11A · côte et grotte',14:'D28P31A · salle à fresques',15:'P04P01C · promontoire nocturne'}
for ref in refs:
 idx=ref['id']
 if idx==8:continue # Byte-identical duplicate, not an extra layout.
 name=f'ref_{idx:02}';out=O/name;out.mkdir(exist_ok=True);src=Image.open(R/ref['source']);frames=[];dur=[]
 for fi in range(getattr(src,'n_frames',1)):
  src.seek(fi);frames.append(np.array(src.convert('RGBA')));dur.append(int(src.info.get('duration',100)))
 a=frames[0];h,w=a.shape[:2];rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);yy,xx=np.mgrid[:h,:w];opaque=a[:,:,3]>0
 def poly(pts):
  p=Image.new('L',(w,h));ImageDraw.Draw(p).polygon([(round(x*w),round(y*h)) for x,y in pts],fill=255);return np.array(p)>0
 animated=np.zeros((h,w),bool)
 for f in frames[1:]:animated|=np.any(f!=a,axis=2)
 floor=poly(FLOOR[idx]) if idx else np.zeros((h,w),bool)
 sky=np.zeros((h,w),bool)
 if idx==0:sky=yy<h*.58
 if idx==4:sky=(yy<h*.42)&(xx<w*.56)&(b>r*.93)&(b>g*.96)
 if idx==15:sky=(yy<h*.51)&~floor
 water=np.zeros((h,w),bool)
 if idx in [0,1,10,13,15]:
  water=((b>r*1.15)&(b>g*.86))|((r>190)&(g>200)&(b>210))
  if idx==0:water&=yy>=h*.58
  if idx==10:water&=~floor
  if idx==15:water&=~floor&~sky
  if idx==13:water&=(yy>h*.3)
 # Small vegetation and material-color layer; full forest masses are depth partitions below.
 green=(g>r*1.08)&(g>b*1.18)&(g>55)
 vegetation=green.copy()
 if idx in [2,3,11,12]:vegetation&=floor # side crowns remain intact with their trunks in the mass layer.
 if idx==15:vegetation&=~floor # peninsula turf remains part of its ground.
 portal=np.zeros((h,w),bool)
 if idx==4:portal=(xx>w*.5)&(xx<w*.79)&(yy<h*.53)&(yy>h*.10)&(r<85)&(g<80)&(b<75)
 if idx==13:portal=(xx>w*.37)&(xx<w*.61)&(yy>h*.20)&(yy<h*.39)&(r<65)&(g<58)&(b<60)
 # Painted dark detail is not sold as a physically reconstructed cast shadow.
 dark=(np.max(rgb,axis=2)<63)&~sky&~water&~portal
 foreground=(yy>h*.70)&~floor
 rear=~floor&~foreground
 masks={};used=animated.copy()
 def take(n,m):
  mm=m&opaque&~used
  if np.any(mm):masks[n]=mm;used[mm]=True
 stars=sky&(abs(r-g)<=9)&(r>38)&(b>r*1.07) if idx in [0,15] else np.zeros((h,w),bool)
 clouds=sky&(g-r>9) if idx==0 else np.zeros((h,w),bool)
 take('01b_etoiles',stars);take('01c_nuages',clouds);take('01_ciel_fond_visible',sky);take('02_eau_visible',water);take('03_vegetation_visible',vegetation);take('04_ouverture_profondeur',portal);take('05_details_sombres',dark);take('06_massif_arriere',rear);take('07_premier_plan',foreground);take('08_sol_chemin_visible',~used)
 layers=[];comp=Image.new('RGBA',(w,h))
 for n,mask in sorted(masks.items()):
  ar=a.copy();ar[~mask]=0;im=Image.fromarray(ar);fn=f'{name}_{n}.png';im.save(out/fn);comp.alpha_composite(im);layers.append({'name':n,'file':fn})
 animation=None
 if len(frames)>1:
  ad=out/'animation_native';ad.mkdir(exist_ok=True);animfiles=[]
  for fi,f in enumerate(frames):
   ar=f.copy();ar[~animated]=0;fn=f'{name}_phase_{fi:03}.png';im=Image.fromarray(ar);im.save(ad/fn);animfiles.append('animation_native/'+fn)
   c=comp.copy();c.alpha_composite(im);assert np.array_equal(np.array(c),f)
  animation={'files':animfiles,'durations_ms':dur,'native_from_supplied_gif':True};comp.alpha_composite(Image.open(out/animfiles[0]).convert('RGBA'))
 assert np.array_equal(np.array(comp),a);comp.save(out/'REFERENCE_RECOMPOSEE.png')
 # Tiny optional light accent, localized on existing ground; no silhouette/path/entrance moves.
 patch=np.zeros_like(a);mask=np.zeros((h,w),bool)
 if idx in [1,3,4,7,12,14]:
  safe=masks.get('08_sol_chemin_visible',np.zeros((h,w),bool))
  region=((xx-w*.49)/(w*.10))**2+((yy-h*.70)/(h*.075))**2<1
  mask=safe&region&~animated
  patch[mask]=a[mask];patch[mask,:3]=np.clip(np.rint(rgb[mask]*1.025),0,255).astype('uint8')
  Image.fromarray(patch).save(out/'OPTION_reflet_discret.png');v=comp.copy();v.alpha_composite(Image.fromarray(patch));v.save(out/'VARIANTE_SUBTILE.png')
 # Editable ORA: original reference, not the optional variation.
 root=ET.Element('image',{'w':str(w),'h':str(h),'name':TITLES[idx]});stack=ET.SubElement(root,'stack');ora_layers=[(l['name'],out/l['file']) for l in layers]
 if animation:ora_layers.append(('Animation native · phase0',out/animation['files'][0]))
 with zipfile.ZipFile(out/(name+'_calques.ora'),'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for j,(n,p) in reversed(list(enumerate(ora_layers))):
   fn=f'data/layer{j}.png';ET.SubElement(stack,'layer',{'name':n,'src':fn,'x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'});z.write(p,fn)
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));z.write(out/'REFERENCE_RECOMPOSEE.png','mergedimage.png')
 record={'id':name,'title':TITLES[idx],'source':ref['source'],'source_sha256':hashlib.sha256((R/ref['source']).read_bytes()).hexdigest(),'size':[w,h],'layers':layers,'animation':animation,'optional_subtle_variant':bool(mask.any()),'source_pixels_unchanged':True,'hidden_surfaces_reconstructed':False};manifest['scenes'].append(record)
 report.append({'id':name,'pixel_exact':True,'native_frames_verified':len(frames),'layers':len(layers),'subtle_changed_pixels':int(np.any(patch[:,:,:3]!=a[:,:,:3],axis=2)[mask].sum()) if mask.any() else 0})
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'verification.json').write_text(json.dumps({'reference_commit':'8eb46bc','records':report,'runtime_validated':False},indent=2));print('14 reference zones +1 supplied background; exact recomposition; native GIF phases preserved')
