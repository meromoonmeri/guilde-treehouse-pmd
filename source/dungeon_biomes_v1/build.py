"""Ten generated layouts + separate source-derived animation components.
Only generated images are resized/quantized. Native raster data is sampled at 1x.
Run with .venv/bin/python source/dungeon_biomes_v1/build.py.
"""
from pathlib import Path
import io,json,zipfile,math,hashlib,shutil
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from scipy import ndimage
from archive import image as archived_image
from red import decode,palettes
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent
O=R/'renders/dungeon_biomes_v1';C=R/'.cache/dungeon_biomes';P=C/'pack';N=C/'native/data/map_bg'
BIOMES={'foret':('Forêt lumineuse',(480,336),'H07P04'), 'ile':('Île céleste',(480,312),'H29P04'), 'volcan':('Volcan',(480,312),'H26P01'), 'desert':('Désert',(456,336),'H20P01'), 'marin':('Courant marin',(456,312),'H02P02')}
# Coordinates are percentages of the complete generated map, not native assets.
# Visible-surface segmentation: no claim of reconstructed surfaces behind walls.
SHAPES={
'foret_entree':{'sol':[(47,30),(55,30),(61,40),(65,49),(70,57),(70,70),(72,81),(85,100),(29,100),(33,81),(35,67),(40,51),(44,43)],'entree':[(40,0),(59,0),(61,27),(55,34),(43,34),(39,24)],'decor':[(31,53),(43,51),(50,60),(48,71),(42,78),(32,74),(28,64)]},
'foret_fin':{'sol':[(36,33),(46,31),(56,32),(66,40),(71,55),(70,65),(62,75),(58,83),(57,100),(42,100),(42,83),(33,74),(28,62),(26,49),(31,38)],'entree':[(42,19),(55,18),(56,33),(45,36),(40,29)]},
'ile_entree':{'sol':[(40,27),(56,28),(61,34),(70,36),(73,43),(72,48),(69,53),(62,56),(57,61),(54,69),(53,80),(58,86),(57,97),(45,100),(41,96),(42,87),(48,79),(47,64),(40,64),(32,59),(26,48),(26,37),(32,29)],'entree':[(38,8),(52,8),(61,22),(61,30),(55,36),(42,34),(34,29),(35,19)]},
'ile_fin':{'sol':[(35,19),(45,17),(56,20),(66,24),(73,36),(73,43),(68,48),(64,54),(57,59),(55,68),(56,100),(45,100),(46,63),(42,59),(33,57),(25,47),(25,34),(29,25)],'entree':[(41,6),(55,5),(61,16),(59,23),(51,27),(43,22),(38,15)]},
'volcan_entree':{'sol':[(45,29),(53,29),(58,46),(59,56),(66,66),(62,77),(57,85),(58,100),(43,100),(43,87),(46,74),(42,64),(42,48)],'entree':[(32,0),(62,0),(68,14),(70,30),(63,38),(56,39),(54,32),(44,30),(41,43),(29,41),(24,30),(25,15)]},
'volcan_fin':{'sol':[(23,21),(35,16),(61,16),(76,23),(86,41),(85,61),(77,74),(62,84),(56,87),(56,100),(43,100),(43,87),(31,83),(20,73),(14,61),(14,43)],'entree':[(36,4),(59,3),(66,10),(64,16),(56,19),(41,18),(32,13)]},
'desert_entree':{'sol':[(32,27),(41,26),(59,26),(67,31),(73,47),(72,58),(68,65),(81,82),(86,100),(12,100),(15,87),(23,77),(29,66),(27,52)],'entree':[(43,4),(52,4),(58,11),(61,26),(54,30),(42,29),(38,23),(39,12)],'decor':[(50,47),(59,47),(68,56),(67,63),(54,66),(47,60)]},
'desert_fin':{'sol':[(35,25),(51,24),(65,28),(73,36),(75,47),(71,59),(61,66),(56,72),(55,100),(44,100),(44,75),(36,68),(26,62),(23,49),(24,38)],'entree':[(41,71),(57,71),(58,86),(41,86)]},
'marin_entree':{'sol':[(43,25),(56,26),(60,30),(66,37),(73,49),(76,59),(73,68),(64,76),(56,81),(59,100),(41,100),(42,83),(33,80),(26,71),(22,58),(24,46),(33,37)],'entree':[(39,2),(55,2),(63,13),(66,27),(59,32),(42,31),(34,25),(33,17)]},
'marin_fin':{'sol':[(36,22),(44,23),(53,24),(63,26),(75,32),(84,45),(85,57),(82,65),(73,73),(61,79),(54,81),(55,100),(43,100),(44,83),(34,79),(23,71),(17,61),(15,46),(21,32)],'entree':[(43,3),(53,4),(60,11),(60,19),(54,24),(44,23),(38,18),(38,10)]}}

def save(im,rel):
 p=P/rel;p.parent.mkdir(parents=True,exist_ok=True)
 a=np.array(im.convert('RGBA'));col,inv=np.unique(a.view(np.uint32).reshape(-1),return_inverse=True)
 if len(col)<=256:
  rgba=col.astype(np.uint32).view(np.uint8).reshape(-1,4);indexed=Image.fromarray(inv.reshape(a.shape[:2]).astype(np.uint8),'P');indexed.putpalette(rgba[:,:3].tobytes());indexed.info['transparency']=rgba[:,3].tobytes();indexed.save(p,optimize=True)
  assert Image.open(p).convert('RGBA').tobytes()==a.tobytes()
 else:im.save(p,optimize=True)
 return rel

def polygon(size,pts):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon([(round(x*size[0]/100),round(y*size[1]/100)) for x,y in pts],fill=255);return np.array(im)>0

def normalized(key,size):
 raw=archived_image(S/'raws'/f'{key}.webp');im=ImageOps.contain(raw,size,Image.Resampling.NEAREST)
 a=np.array(im);rgb=a[:,:,:3].astype(np.int16);mag=(rgb[:,:,0]>130)&(rgb[:,:,2]>120)&(rgb[:,:,1]<100)&(rgb[:,:,0]>rgb[:,:,1]*1.7)&(rgb[:,:,2]>rgb[:,:,1]*1.5)
 a[mag]=0
 # Quantization applies ONLY to new generated art; raw lossless originals retained.
 q=Image.fromarray(a[:,:,:3]).quantize(colors=112,method=Image.Quantize.MEDIANCUT).convert('RGBA');qa=np.array(q);qa[:,:,3]=a[:,:,3];qa[qa[:,:,3]==0]=0
 out=Image.new('RGBA',size);out.paste(Image.fromarray(qa),((size[0]-im.width)//2,(size[1]-im.height)//2))
 return out

def split_map(key,size):
 im=normalized(key,size);a=np.array(im);visible=a[:,:,3]>0;shape=SHAPES[key]
 floor=polygon(size,shape['sol'])&visible;entrance=polygon(size,shape['entree'])&visible
 decor=polygon(size,shape['decor'])&visible if 'decor' in shape else np.zeros(visible.shape,bool)
 floor&=~entrance&~decor;wall=visible&~floor&~entrance&~decor
 # A narrow band of visible architecture next to the drawn walking floor.
 rim=wall&(ndimage.distance_transform_edt(~floor)<=5);wall&=~rim
 masks={'01_sol_visible':floor,'02_bordures_visibles':rim,'03_arbres_visibles' if key.startswith('foret') else '03_parois_visibles':wall,'04_entree_visible' if key.endswith('entree') else '04_terrasse_visible':entrance}
 if decor.any():masks['05_decor_visible']=decor
 layers=[];recom=Image.new('RGBA',size)
 for name,mask in masks.items():
  cut=a.copy();cut[~mask]=0;ci=Image.fromarray(cut);rel=save(ci,f'cartes/{key}/DB1_{key}_{name}.png');layers.append(rel);recom.alpha_composite(ci)
 assert recom.tobytes()==im.tobytes()
 # No redundant flattened terrain in the ZIP: assemble.py recreates it exactly.
 return im,{'id':key,'size':size,'layers':layers,'source':'generated, resized nearest-neighbour and palette-quantized; not native','layer_scope':'visible surfaces only; no hidden ground reconstructed','south_return':True,'north_entrance':key.endswith('entree')}

@lru_cache(maxsize=120)
def native(name,tile_tick=0):return decode(name,tile_tick,N)

def colorize(name,idx,tick):
 pal,_=palettes((N/(name+'.bpl')).read_bytes(),tick);bank=np.zeros((256,4),np.uint8);bank[:pal.shape[0]*16]=pal.reshape(-1,4)
 bad=(idx//16>=len(pal))&(idx%16!=0);assert not bad.any()
 return Image.fromarray(bank[idx])

def component(name,tick,layer=0,box=None):
 # Geometry has its own BPA clock; palette is looked up independently.
 period={'H07P04W':98,'W04':112}.get(name)
 tt=tick%period if period else 0
 idx=native(name,tt)[2][layer]
 if box:x,y,X,Y=box;idx=idx[y:Y,x:X]
 return colorize(name,idx,tick)

def tiled(im,size,offset_x=0):
 a=np.array(im);ys=np.arange(size[1])%im.height;xs=(np.arange(size[0])-offset_x)%im.width
 return Image.fromarray(a[ys[:,None],xs[None,:]])

def additive(base,overlay):
 # Same 16/16 equation as PC-port's RGB555 alpha blend. This is a composed
 # preview, not a claim of a GPU-identical capture of the original ground.
 b=np.array(base).astype(np.uint16);o=np.array(overlay).astype(np.uint16)
 rgb=np.minimum((b[:,:,:3]>>3)+((o[:,:,:3]>>3)*(o[:,:,3:4]>0)),31)*255//31
 b[:,:,:3]=rgb;return Image.fromarray(b.astype(np.uint8))

LAVA_BOX=(88,168,152,232)
@lru_cache(maxsize=1)
def lava_coordinates():
 # Texture quilting selects unchanged source pixels, never interpolates or
 # mirrors them. Minimum-cost overlaps avoid the obvious 64px checkerboard.
 choices=[(88,168),(40,168),(48,168),(48,176),(328,168),(32,168),(336,168),(344,168),(376,168)]
 source=np.array(component('H26P01',0))[:,:,:3].astype(np.float32)
 yy,xx=np.indices((64,64));h,w=352,512;coords=np.zeros((h,w),np.int32);rgb=np.zeros((h,w,3),np.float32);rng=np.random.default_rng(2301)
 def seam(err):
  cost=err.copy();H,W=err.shape
  for y in range(1,H):cost[y]+=np.minimum.reduce([np.r_[np.inf,cost[y-1,:-1]],cost[y-1],np.r_[cost[y-1,1:],np.inf]])
  result=np.empty(H,int);result[-1]=int(cost[-1].argmin())
  for y in range(H-2,-1,-1):
   lo=max(0,result[y+1]-1);hi=min(W,result[y+1]+2);result[y]=lo+int(cost[y,lo:hi].argmin())
  return result
 for y in range(0,h-63,40):
  for x in range(0,w-63,40):
   candidates=[]
   for sx,sy in choices:
    tile=source[sy:sy+64,sx:sx+64];diff=((rgb[y:y+64,x:x+64]-tile)**2).sum(axis=2)
    cost=(diff[:,:24].mean() if x else 0)+(diff[:24].mean() if y else 0)
    candidates.append((cost+float(rng.random())*.01,sx,sy,tile,diff))
   _,sx,sy,tile,diff=min(candidates,key=lambda c:c[0]);take=np.ones((64,64),bool)
   if x:take[:,:24]&=np.arange(24)[None,:]>=seam(diff[:,:24])[:,None]
   if y:take[:24]&=np.arange(24)[:,None]>=seam(diff[:24].T)[None,:]
   block=(yy+sy)*480+xx+sx;coords[y:y+64,x:x+64][take]=block[take];rgb[y:y+64,x:x+64][take]=tile[take]
 coords=coords[:312,:480];assert (coords>0).all();return coords

def lava(tick):
 c=lava_coordinates();idx=native('H26P01')[2][0].reshape(-1)[c]
 assert set(np.unique(idx//16))<=set([1,3,5,6,7,8])
 return colorize('H26P01',idx,tick)

def desert_veil(tick,size):
 im=component('W05',tick);a=np.array(im);xs=(np.arange(size[0])-tick//4)%im.width
 out=Image.new('RGBA',size);out.paste(Image.fromarray(a[:,xs]),(0,0));return out

def render(biome,terrain,tick):
 size=terrain.size
 if biome=='ile':out=component('H29P04',tick,1)
 elif biome=='volcan':out=lava(tick)
 else:out=Image.new('RGBA',size,{'foret':'#112c17','desert':'#392e16','marin':'#03243f'}[biome])
 out.alpha_composite(terrain)
 if biome=='foret':out=additive(out,component('H07P04W',tick))
 elif biome=='marin':out=additive(out,component('H02P02W',tick))
 elif biome=='desert':out=additive(out,desert_veil(tick,size))
 elif biome=='volcan':out.alpha_composite(component('W04',tick).crop((0,0,*size)))
 return out.convert('RGB')


def export_animations():
 manifest={};root='animations'
 # All 14 BPA geometries x 32 BPL phases. This is a factored state bank,
 # NOT 448 consecutive time frames. The two clocks must be evaluated separately.
 frames=[]
 for b in range(14):
  idx=native('H07P04W',b*7)[2][0]
  for p in range(32):frames.append(save(colorize('H07P04W',idx,p*8),f'{root}/foret/DB1_foret_bpa{b:02d}_bpl{p:02d}.png'))
 manifest['foret']={'frames':frames,'selection':'frames[((tick//7)%14)*32 + ((tick//8)%32)]','period_ticks':12544,'blend':'add RGB555, coefficients 16/16; black is neutral, do not use normal-over','source':'H07P04W BPA + BPL','size':[480,336]}
 for key,name,layer,count,dt in [('ile','H29P04',1,36,6),('marin','H02P02W',0,32,8),('desert_voile','W05',0,32,8),('volcan_cendres','W04',0,16,7)]:
  frames=[]
  for f in range(count):
   im=component(name,f*dt,layer)
   if key=='volcan_cendres':im=im.crop((0,0,480,312))
   frames.append(save(im,f'{root}/{key}/DB1_{key}_{f:02d}.png'))
  manifest[key]={'frames':frames,'selection':f'frames[(tick//{dt})%{count}]','frame_ticks':dt,'period_ticks':count*dt,'source':name,'native_scale':1,'blend':'add RGB555 16/16' if key in ['marin','desert_voile'] else 'normal-over','size':im.size}
 manifest['desert_voile'].update(scroll='1 pixel right per 4 update ticks; horizontal wrap480. Native renderer wraps480x264; this full-map composition places one 264px-high strip at y0 and leaves lower72px transparent (screen-anchored effect adapted to a whole-map preview).',combined_period_ticks=3840)
 manifest['volcan_cendres']['crop']=[0,0,480,312]
 frames=[]
 for f in range(31):
  im=lava(f*4);frames.append(save(im,f'{root}/volcan_lave/DB1_volcan_lave_{f:02d}.png'))
 coords=lava_coordinates().astype(np.uint32);encoded=np.stack([coords&255,(coords>>8)&255,(coords>>16)&255],axis=-1).astype(np.uint8)
 save(Image.fromarray(encoded),'provenance/DB1_lava_source_coordinates.png')
 manifest['volcan_lave']={'frames':frames,'selection':'frames[(tick//4)%31]','frame_ticks':4,'period_ticks':124,'source':'H26P01 native texture pixels, palettes 1/3 static and 5/6/7/8 animated','native_scale':1,'layout':'64x64 native texture patches assembled with minimum-cost overlap seams, no colour interpolation/flip/scale; new arrangement, not original map','pixel_provenance':'provenance/DB1_lava_source_coordinates.png: source_offset=R+256*G+65536*B, source image width480','blend':'normal-over'}
 # Original native maps remain reference-only, never substituted for a new map.
 audit=json.loads((S/'audit.json').read_text())
 for rec in audit['references']:
  ims=native(rec['map'])[0];full=Image.new('RGBA',ims[0].size)
  for im in reversed(ims):full.alpha_composite(im)
  save(full,'references/DB1_native_'+rec['map']+'.png')
 # Desert's original sand-column/eddy palette channels are preserved as a
 # reference bank, but not pasted over the newly generated floor.
 for pi,(dt,count) in enumerate(native('H20P01')[1]['palette_spec']):
  if not count:continue
  idx=native('H20P01')[2][0];mask=idx//16==pi;files=[]
  for f in range(count):
   a=np.array(colorize('H20P01',idx,f*dt));a[~mask]=0
   files.append(save(Image.fromarray(a),f'references/desert_cycles/DB1_H20_palette{pi}_{f:02d}.png'))
  manifest[f'reference_desert_p{pi}']={'frames':files,'frame_ticks':dt,'period_ticks':dt*count,'placed':False,'scope':'original map animation pixels, not a complete movable object'}
 return manifest


def font(size):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)

def pair(biome,images):
 label,size,_=BIOMES[biome];w,h=size;im=Image.new('RGB',(992,h+54),'#172227');d=ImageDraw.Draw(im)
 d.text((16,8),label+'  /  entrée',font=font(16),fill='#ebf4d7');d.text((512,8),'zone finale',font=font(16),fill='#ebf4d7')
 im.paste(images[0],(8+(480-w)//2,40));im.paste(images[1],(504+(480-w)//2,40));return im

def main():
 O.mkdir(parents=True,exist_ok=True);C.mkdir(exist_ok=True)
 if P.exists():shutil.rmtree(P)
 P.mkdir();(O/'apercus').mkdir(exist_ok=True)
 with zipfile.ZipFile(S/'native_sources.zip') as z:z.extractall(C/'native')
 terrain={};maps=[]
 for b,(_,size,_) in BIOMES.items():
  for role in ['entree','fin']:
   key=b+'_'+role;terrain[key],rec=split_map(key,size);maps.append(rec)
 anim=export_animations();print('Exported native state banks',flush=True)
 # A short, explicitly labelled excerpt. No falsely seamless loop.
 ticks=list(range(32,160,8));dur=[round((t+8)*1000/60)-round(t*1000/60) for t in ticks]
 pair_stills=[]
 for b in BIOMES:
  frames=[]
  for tick in ticks:
   imgs=[render(b,terrain[b+'_'+role],tick) for role in ['entree','fin']];frames.append(pair(b,imgs))
   # The public overview is the opaque demonstration. The ZIP keeps transparent
   # per-map PNGs, not another duplicate set of opaque composites.
  pair_stills.append(frames[4]);frames[0].save(O/'apercus'/f'DB1_{b}_duo.webp',save_all=True,append_images=frames[1:],duration=dur,loop=1,lossless=False,quality=60,minimize_size=True,method=6)
  print('Preview',b,(O/'apercus'/f'DB1_{b}_duo.webp').stat().st_size,flush=True)
 height=100+sum(im.height for im in pair_stills)+40
 overview=Image.new('RGB',(992,height),'#172227');d=ImageDraw.Draw(overview);d.text((18,15),'DONJONS  /  LOT 01',font=font(26),fill='#edf4d4');d.text((18,54),'5 biomes · 10 nouvelles cartes · calques et animations séparés',font=font(16),fill='#aebec4')
 y=100
 for im in pair_stills:overview.paste(im,(0,y));y+=im.height
 d.text((18,y+8),'Créations non natives · Effets extraits à 1× · Intégration PMDO non testée',font=font(13),fill='#aebec4');overview.quantize(colors=224,method=Image.Quantize.MEDIANCUT).save(O/'apercus/DB1_collection.png',optimize=True)
 manifest={'version':1,'maps':maps,'animations':anim,'preview':{'ticks':ticks,'hz':60,'sample_stride_ticks':8,'duration_ms':sum(dur),'loop_count':1,'overview_tick':64,'presentation_only':True,'webp_lossless':False,'webp_quality':60,'overview_palette_colors':224,'import_PNG_lossless':True,'scope':'sampled excerpt, not the full combined native loop; reopen to replay'},'remaining':['jungle','overgrownforest','mtdiscipline','wildplains','secretiveforest','scorchedplains'],'native_sources':'native_sources.zip','limitations':['Visible-surface layer segmentation; hidden ground is not reconstructed.','Native source colours are not a GPU-screen capture. Additive compositing is required for light layers.','No collision, warp, character or PMDO runtime integration.','Generated layouts are not artistically approved.']}
 (P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(O/'manifest.json').write_text(json.dumps({k:v for k,v in manifest.items() if k!='animations'},indent=2)+'\n')
 shutil.copy2(S/'audit.json',P/'audit.json');shutil.copy2(S/'native_sources.zip',P/'native_sources.zip')
 if (S/'PACK_README.md').exists():
  shutil.copy2(S/'PACK_README.md',P/'README.md');shutil.copy2(S/'PACK_README.md',O/'README.md')
 shutil.copy2(S/'assemble.py',P/'assemble.py')
 with zipfile.ZipFile(O/'DB1_cinq_duos_multicalques.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in sorted(P.rglob('*')):
   if f.is_file():
    zi=zipfile.ZipInfo(f.relative_to(P).as_posix(),(2026,9,21,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,f.read_bytes())
 print('ZIP bytes', (O/'DB1_cinq_duos_multicalques.zip').stat().st_size,'overview bytes',(O/'apercus/DB1_collection.png').stat().st_size)
if __name__=='__main__':main()
