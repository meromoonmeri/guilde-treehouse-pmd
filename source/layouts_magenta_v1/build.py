from pathlib import Path
import json,colorsys,hashlib,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/layouts_magenta_v1';CONFIG=json.loads((P/'config.json').read_text());NN=Image.Resampling.NEAREST
PALETTES={'cote':[('ardoise_rosee','Côte · ardoise rosée'),('cuivre_lagon','Côte · cuivre et lagon')],'cristal':[('boreal','Cristal · boréal'),('opalin','Cristal · opalin')],'foret':[('mousse_doree','Forêt · mousse dorée'),('emeraude','Forêt · émeraude')],'sables':[('ocre','Sables · ocre'),('rose_desert','Sables · rose du désert')]}
def load(p,size=None):
 im=Image.open(p).convert('RGBA');return im.resize(size,NN) if size else im

from palette import key,tint

def clipped(a,mask):
 out=a.copy();out[~mask]=0;return Image.fromarray(out)

def poly(size,points):
 w,h=size;m=Image.new('L',size);ImageDraw.Draw(m).polygon([(round(x*w),round(y*h)) for x,y in points],fill=255);return np.array(m)>0

def ora(path,layers,comp):
 root=ET.Element('image',{'w':str(comp.width),'h':str(comp.height),'name':path.stem});stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):
   filename=f'data/layer{i}.png';ET.SubElement(stack,'layer',{'name':name,'src':filename,'x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'});b=io.BytesIO();im.save(b,format='PNG');z.writestr(filename,b.getvalue())
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));b=io.BytesIO();comp.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())

manifest={'method':'Generator magenta -> alpha cleanup -> protected native fluid frames -> aligned layers and coherent palettes','runtime_validated':False,'scenes':[]};checks=[]
for conf in CONFIG:
 name=conf['id'];size=tuple(conf['size']);w,h=size;yy,xx=np.mgrid[:h,:w];raw=load(O/'bruts'/(name+'.png'),size);terrain=key(raw);ta=np.array(terrain);valid=ta[:,:,3]>0
 native=Image.open(R/conf['source']);src=[]
 for fi in range(conf['frames']):native.seek(fi);src.append(native.convert('RGBA').copy())
 a0=np.array(src[0]);preserve=np.array(Image.open(P/(name+'_preserve.png'))) >0
 md=O/'masques'/name;md.mkdir(parents=True,exist_ok=True);Image.fromarray(preserve.astype('uint8')*255).save(md/'animation_protegee.png');terrain.save(md/'terrain_detoure.png')
 # A failed empty-sand generation is replaced honestly by a patch of the generated dry sand.
 if name=='sables':
  patch=terrain.crop((8,8,32,32));assert np.min(np.array(patch)[:,:,3])==255
  floor=Image.new('RGBA',size)
  for y in range(0,h,24):
   for x in range(0,w,24):floor.alpha_composite(patch,(x,y))
  patch.save(md/'echantillon_sol_24px.png');floor.save(md/'sol_reconstitue_patch.png')
 else:floor=load(O/'bruts'/(name+'_sol.png'),size)
 full=floor.copy();full.alpha_composite(terrain);a=np.array(full)
 dist=nd.distance_transform_edt(~preserve) if preserve.any() else np.full((h,w),1000.)
 # Restore the original interface and softly match color over a6px outer band.
 weight=np.clip((8-dist)/6,0,1);a[:,:,:3]=np.rint(a[:,:,:3]*(1-weight[:,:,None])+a0[:,:,:3]*weight[:,:,None]).astype('uint8')
 # Main entrance of the coastal cave stays exactly where the reference places it.
 gate=np.zeros((h,w),bool)
 if name=='cote':
  ar,ag,ab=a0[:,:,:3].astype(float).transpose(2,0,1);gate=(xx>w*.30)&(xx<w*.48)&(yy>h*.19)&(yy<h*.37)&(ar<65)&(ag<58)&(ab<65)
  gd=nd.distance_transform_edt(~gate);blend=np.clip((4-gd)/3,0,1);a[:,:,:3]=np.rint(a[:,:,:3]*(1-blend[:,:,None])+a0[:,:,:3]*blend[:,:,None]).astype('uint8')
 a[:,:,3]=255;a[preserve]=a0[preserve]
 # Separate actual vegetation overlay in forest; depth partitions in rocky environments.
 r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 if name=='foret':
  lab,n=nd.label(valid,np.ones((3,3)));counts=np.bincount(lab.ravel());small=(lab>0)&(counts[lab]<450);structure=valid&~small
  ground=~valid;objects={'04_massif_gauche':structure&(xx<w*.5),'05_massif_droit':structure&(xx>=w*.5),'06_petits_decors':small}
 elif name=='sables':
  stone=(g<185)&(r<224)&(b<140)&~preserve
  lab,n=nd.label(stone,np.ones((3,3)));counts=np.bincount(lab.ravel());stone=(lab>0)&(counts[lab]>=12);stone=nd.binary_fill_holes(nd.binary_dilation(stone,iterations=1))&~preserve
  ground=~stone&~preserve;objects={'04_rochers_arriere':stone&(yy<h*.72),'05_rochers_avant':stone&(yy>=h*.72)}
 elif name=='cote':
  ground=poly(size,[(.36,.33),(.46,.33),(.56,.45),(.60,.56),(1,.59),(1,.77),(.78,.84),(.53,.82),(.35,.69),(.23,.50)])&~preserve&~gate
  lum=(r+g+b)/3;seed=ground&(lum<np.median(lum[ground])*.76);lab,n=nd.label(seed,np.ones((3,3)));counts=np.bincount(lab.ravel());stones=(lab>0)&(counts[lab]>20);stones=nd.binary_fill_holes(nd.binary_dilation(stones,iterations=2))&ground;ground&=~stones
  structure=~ground&~preserve&~gate;objects={'04_parois_arriere':structure&(yy<h*.59)&~stones,'05_relief_avant':structure&((yy>=h*.59)|stones),'06_ouverture':gate}
 else:
  center=poly(size,[(.43,0),(.57,0),(.56,.26),(.66,.45),(.54,.62),(.60,.85),(.56,1),(.41,1),(.42,.82),(.45,.62),(.33,.45),(.44,.25)])
  ground=center&~preserve;structure=~ground&~preserve;objects={'04_cristaux_gauche':structure&(xx<w*.5),'05_cristaux_droit':structure&(xx>=w*.5)}
 # Protected seams are a dedicated layer, drawn above terrain and contact shadows.
 seam=(dist>0)&(dist<=8)&~preserve
 for k in objects:objects[k]&=~seam
 ground&=~seam
 obj=np.zeros((h,w),bool)
 for mask in objects.values():obj|=mask
 support=np.array(floor);support[:,:,3]=255;support[ground]=a[ground];support[preserve]=0
 # New contact shadow derived from silhouettes, not falsely labelled a recovered native shadow.
 sh=Image.fromarray((obj*255).astype('uint8'));shifted=Image.new('L',size);shifted.paste(sh,(0,3));shadowalpha=np.array(shifted.filter(ImageFilter.GaussianBlur(1))).astype(float)*.23;shadowalpha[obj|preserve|seam]=0
 sa=np.zeros_like(a);sa[:,:,:3]=[15,24,27];sa[:,:,3]=np.rint(shadowalpha).astype('uint8');sa[sa[:,:,3]==0]=0
 ungraded={'02_sol_reconstitue':Image.fromarray(support),'03_ombres_contact':Image.fromarray(sa)}
 for key_name,mask in objects.items():
  if mask.any():ungraded[key_name]=clipped(a,mask)
 if seam.any():ungraded['07_raccord_reference']=clipped(a,seam)
 for key_name,mask in objects.items():Image.fromarray(mask.astype('uint8')*255).save(md/(key_name+'.png'))
 Image.fromarray(ground.astype('uint8')*255).save(md/'sol_visible.png')
 for pi,(palette,title) in enumerate(PALETTES[name]):
  ident=name+'_'+palette;out=O/'zones'/ident;out.mkdir(parents=True,exist_ok=True);layers={k:tint(v,name,pi) for k,v in ungraded.items()};layerfiles=[]
  for key_name,im in layers.items():fn=ident+'_'+key_name+'.png';im.save(out/fn);layerfiles.append({'name':key_name,'file':fn})
  animfiles=[];scene_frames=[];native_count=0
  for fi,frame in enumerate(src):
   comp=Image.new('RGBA',size)
   if preserve.any():
    water=tint(clipped(np.array(frame),preserve),name,pi);fn=f'{ident}_01_animation_{fi:03}.png';water.save(out/fn);animfiles.append(fn);comp.alpha_composite(water)
   for im in layers.values():comp.alpha_composite(im)
   assert np.all(np.array(comp)[:,:,3]==255)
   if preserve.any():assert np.array_equal(np.array(comp)[preserve],np.array(tint(frame,name,pi))[preserve]);native_count+=1
   scene_frames.append(comp)
  scene_frames[0].save(out/'COMPOSITION.png')
  if len(scene_frames)>1:scene_frames[0].save(out/'ANIMATION_COMPLETE.webp',save_all=True,append_images=scene_frames[1:],duration=conf['durations_ms'],loop=0,lossless=True)
  ora_layers={}
  if animfiles:ora_layers['01_animation_phase0']=load(out/animfiles[0])
  ora_layers.update(layers);ora(out/(ident+'.ora'),ora_layers,scene_frames[0])
  record={'id':ident,'title':title,'biome':name,'palette_index':pi,'size':list(size),'source':conf['source'],'source_sha256':hashlib.sha256((R/conf['source']).read_bytes()).hexdigest(),'layers':layerfiles,'animation':{'files':animfiles,'durations_ms':conf['durations_ms'],'cycle_ms':sum(conf['durations_ms']),'source_sequence_preserved':True,'colors_transformed':True} if animfiles else None,'hidden_ground':'generator plate' if name!='sables' else 'tiled24px patch from generated dry sand','contact_shadows':'reconstructed, not native','native_runtime_validated':False};manifest['scenes'].append(record)
  checks.append({'id':ident,'fully_opaque_composition':True,'frames_verified_in_native_protected_mask':native_count,'frame_count':len(src),'source_size_preserved':True})
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'verification_build.json').write_text(json.dumps(checks,indent=2));print('4 magenta-guided layouts,8 palette scenes;30/12/6 native cycles preserved; forest static')
