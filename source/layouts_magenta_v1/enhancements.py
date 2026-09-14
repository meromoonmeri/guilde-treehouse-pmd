from pathlib import Path
import json,math,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage as nd
from palette import key,tint
R=Path(__file__).resolve().parents[2];O=R/'renders/layouts_magenta_v1';BASE=json.loads((O/'manifest.json').read_text());BYID={e['id']:e for e in BASE['scenes']};NN=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def rgba(mask,rgb):
 a=np.zeros((*mask.shape,4),dtype='uint8');a[:,:,:3]=rgb;a[:,:,3]=mask;a[a[:,:,3]==0]=0;return Image.fromarray(a)
def ramp(im,points):
 a=np.array(im);lum=np.dot(a[:,:,:3],[.2126,.7152,.0722]);pos=[p[0] for p in points]
 for c in range(3):a[:,:,c]=np.interp(lum,pos,[p[1][c] for p in points]).round().astype('uint8')
 a[a[:,:,3]==0]=0;return Image.fromarray(a)
def ash(im):
 a=np.array(im);lum=np.dot(a[:,:,:3],[.2126,.7152,.0722])*.78
 for j,k in enumerate([1.0,1.005,1.045]):a[:,:,j]=np.clip(lum*k,0,255).round().astype('uint8')
 a[a[:,:,3]==0]=0;return Image.fromarray(a)
def ora(path,layers,comp):
 root=ET.Element('image',{'w':str(comp.width),'h':str(comp.height),'name':path.stem});stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in reversed(list(enumerate(layers))):
   fn=f'data/layer{i}.png';ET.SubElement(stack,'layer',{'name':name,'src':fn,'x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'});b=io.BytesIO();im.save(b,format='PNG');z.writestr(fn,b.getvalue())
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));b=io.BytesIO();comp.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())

# The first border generation replicated too much forest. Use only the second, isolated-branch sheet.
sheet=key(load(O/'bruts/rameaux_premier_plan.png'));sprites=[];sd=O/'rameaux_detoures';sd.mkdir(exist_ok=True)
for i in range(2):
 piece=sheet.crop((i*sheet.width//2,0,(i+1)*sheet.width//2,sheet.height));piece=piece.crop(piece.getbbox());piece.save(sd/f'rameau_{i}.png');sprites.append(piece)
REQUESTS=[('foret_mousse_immersive','Forêt mousse · feuillage immersif','foret_mousse_doree','forest'),('foret_emeraude_immersive','Forêt émeraude · feuillage immersif','foret_emeraude','forest'),('sables_siphons_eau','Sables · siphons d’eau','sables_ocre','water'),('cristal_irise','Passage cristallin · bleu rose blanc','cristal_boreal','iridescent'),('cote_cendres_lave','Coastal Cave · cendres et lave','cote_ardoise_rosee','lava')]
manifest={'scenes':[],'runtime_validated':False};reports=[]
for ident,title,parent,kind in REQUESTS:
 e=BYID[parent];p=O/'zones'/parent;out=O/'variantes'/ident;out.mkdir(parents=True,exist_ok=True);w,h=e['size'];size=(w,h);yy,xx=np.mgrid[:h,:w];layers={l['name']:load(p/l['file']) for l in e['layers']};groups=[];proof={}
 if e['animation']:
  groups.append({'name':'01_animation_base','images':[load(p/f) for f in e['animation']['files']],'durations_ms':e['animation']['durations_ms'],'position':'under','origin':'native sequence, color-transformed in parent'})
 if kind=='forest':
  leaves=Image.new('RGBA',size)
  def place(sprite,width,xy,flip=False):
   q=sprite.copy()
   if flip:q=q.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
   q=q.resize((width,round(q.height*width/q.width)),NN);leaves.alpha_composite(q,xy)
  l0=sprites[0];l1=sprites[1].transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  bw=round(w*.24);bh0=round(l0.height*bw/l0.width);bh1=round(l1.height*bw/l1.width)
  place(l0,bw,(-12,h-bh0+12));place(l1,bw,(w-bw+12,h-bh1+12))
  tw=round(w*.15);place(l0,tw,(-10,-18),True);place(l1,tw,(w-tw+10,-18),True)
  mw=round(w*.15);place(l0,mw,(-35,round(h*.36)));place(l1,mw,(w-mw+35,round(h*.37)))
  leaves=tint(leaves,'foret',e['palette_index']);a=np.array(leaves);corridor=(xx>w*.30)&(xx<w*.70);assert not np.any(a[corridor,3])
  alpha=a[:,:,3];shadow=Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1));sh=Image.new('L',size);sh.paste(shadow,(2,3));sa=(np.array(sh)*.22).astype('uint8');layers['08_ombre_feuillage']=rgba(sa,[14,29,21])
  for keyname,mask in [('09_feuillage_gauche',xx<w*.5),('10_feuillage_droit',xx>=w*.5)]:
   part=a.copy();part[~mask]=0;layers[keyname]=Image.fromarray(part)
  proof={'central_access_corridor_uncovered':True,'leaves_from':'rameaux_premier_plan.png','new_border_is_static':True}
 elif kind=='water':
  g=groups[0];g['name']='01_siphons_eau_adaptes';g['origin']='new water color adaptation of6 native sand phases';g['images']=[ramp(im,[(60,(8,38,85)),(115,(10,75,133)),(160,(20,133,174)),(200,(53,193,207)),(232,(172,238,233)),(255,(234,254,248))]) for im in g['images']]
  # A tiny independent pebble is moved4px right,2px up; its old place reveals reconstructed sand.
  layername='04_rochers_arriere';a=np.array(layers[layername]);lab,n=nd.label(a[:,:,3]>0,np.ones((3,3)));counts=np.bincount(lab.ravel());protected=np.array(g['images'][0])[:,:,3]>0;shift=None
  for idx in range(1,n+1):
   if not 70<counts[idx]<220:continue
   ys,xs=np.where(lab==idx)
   if xs.mean()<w*.55 or ys.mean()<h*.5:continue
   moving=lab==idx;dest=np.zeros((h,w),bool);dest[ys-2,xs+4]=True
   if np.any(dest&protected) or np.any(dest&(a[:,:,3]>0)&~moving):continue
   piece=np.zeros_like(a);piece[ys-2,xs+4]=a[ys,xs];a[moving]=0;layers[layername]=Image.fromarray(a);layers['06_galet_decale']=Image.fromarray(piece)
   shadows=np.array(layers['03_ombres_contact']);old=nd.binary_dilation(moving,iterations=4);shadows[old]=0
   sm=Image.fromarray((dest*255).astype('uint8'));sh=Image.new('L',size);sh.paste(sm,(0,3));new=(np.array(sh.filter(ImageFilter.GaussianBlur(1)))*.23).astype('uint8');new[dest|protected]=0
   shadow_img=Image.fromarray(shadows);shadow_img.alpha_composite(rgba(new,[15,24,27]));layers['03_ombres_contact']=shadow_img;shift={'delta':[4,-2],'source_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'sprite_pixels':int(counts[idx])};break
  assert shift is not None
  proof={'sand_sequence_adapted_not_native_water':True,'pebble_shift':shift,'fluid_alpha_unchanged':True}
 elif kind=='iridescent':
  ref=load(R/'source/layouts_magenta_v1/references/cristal_reference.png');a=np.array(ref);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
  # Highlight selection stays fixed, no scrolling hue or moving rainbow geometry.
  reflective=(g>150)&(b>185)&(r>55);strength=np.clip((g-145)/95,0,1)*reflective
  u=np.clip((xx/w-.30)/.40,0,1);colors=np.empty((h,w,3))
  for j in range(3):colors[:,:,j]=np.interp(u,[0,.5,1],[[100,185,255][j],[247,250,255][j],[255,130,205][j]])
  colors=colors.round().astype('uint8');imgs=[]
  for fi in range(24):
   # Fixed blue-white-pink RGB; only opacity pulses.
   power=.42+.34*(1+np.sin(2*math.pi*fi/24+yy/h*math.pi))/2;alpha=np.rint(strength*power*255).astype('uint8');imgs.append(rgba(alpha,colors))
  groups.append({'name':'08_reflets_bleu_rose_blanc','images':imgs,'durations_ms':[80]*24,'position':'over','origin':'new fixed-RGB iridescent reflection, opacity pulse'})
  proof={'fixed_rgb_no_hue_drift':True,'native_base_cycle_ms':1920,'new_reflection_cycle_ms':1920}
 else:
  layers={name:ash(im) for name,im in layers.items()};g=groups[0];g['name']='01_lave_adaptee';g['origin']='lava color adaptation of30 source water phases, not native lava'
  g['images']=[ramp(im,[(0,(30,8,14)),(50,(92,15,12)),(95,(180,29,6)),(145,(244,73,5)),(195,(255,150,12)),(235,(255,216,65)),(255,(255,242,154))]) for im in g['images']]
  wet=np.array(g['images'][0])[:,:,3]>0;dist=nd.distance_transform_edt(~wet);edge=(dist>0)&(dist<8);imgs=[]
  for fi in range(30):
   power=38+15*(1+math.sin(2*math.pi*fi/30))/2;alpha=np.rint(np.clip((8-dist)/8,0,1)*power*edge).astype('uint8');imgs.append(rgba(alpha,[255,95,13]))
  groups.append({'name':'08_lueur_chaleur_berge','images':imgs,'durations_ms':[130]*30,'position':'over','origin':'new subtle heat glow'})
  proof={'ash_gray_static_terrain':True,'lava_is_adapted_not_native':True,'source_cycle_ms':3900,'fluid_alpha_unchanged':True}
 # Persist independent layers and clocks.
 layerfiles=[]
 for name,im in layers.items():fn=f'{ident}_{name}.png';im.save(out/fn);layerfiles.append({'name':name,'file':fn})
 animation=[]
 for g in groups:
  files=[]
  for fi,im in enumerate(g['images']):fn=f'{ident}_{g["name"]}_{fi:03}.png';im.save(out/fn);files.append(fn)
  animation.append({k:v for k,v in g.items() if k!='images'}|{'files':files})
 def frame_index(t,durations):
  t%=sum(durations)
  for i,d in enumerate(durations):
   if t<d:return i
   t-=d
 def render(t):
  c=Image.new('RGBA',size)
  for g in groups:
   if g['position']=='under':c.alpha_composite(g['images'][frame_index(t,g['durations_ms'])])
  for im in layers.values():c.alpha_composite(im)
  for g in groups:
   if g['position']=='over':c.alpha_composite(g['images'][frame_index(t,g['durations_ms'])])
  assert np.all(np.array(c)[:,:,3]==255);return c
 period=math.lcm(*[sum(g['durations_ms']) for g in groups]) if groups else 0;step=math.gcd(*[d for g in groups for d in g['durations_ms']]) if groups else 0
 comp=render(0);comp.save(out/'COMPOSITION.png');ora_layers=[]
 for g in groups:
  if g['position']=='under':ora_layers.append((g['name']+' phase0',g['images'][0]))
 ora_layers.extend(layers.items())
 for g in groups:
  if g['position']=='over':ora_layers.append((g['name']+' phase0',g['images'][0]))
 ora(out/(ident+'.ora'),ora_layers,comp)
 if groups:
  previews=[render(t) for t in range(0,period,step)];previews[0].save(out/'ANIMATION_COMPLETE.webp',save_all=True,append_images=previews[1:],duration=step,loop=0,lossless=True)
 record={'id':ident,'title':title,'parent':parent,'kind':kind,'size':list(size),'layers':layerfiles,'animation_groups':animation,'cycle_ms':period,'preview_step_ms':step,'proof':proof,'runtime_validated':False};manifest['scenes'].append(record);reports.append({'id':ident,'layers':len(layerfiles),'animation_groups':len(groups),'full_composition_opaque':True})
(O/'enhancements_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'enhancements_checks.json').write_text(json.dumps(reports,indent=2));print('5 additional variants; isolated leaf borders,6 water siphon frames,24 iridescent frames,30 lava+heat frames')
