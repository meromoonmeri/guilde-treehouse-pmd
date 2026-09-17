"""Native artwork, NEW authored aurora motion. Not a recovered canonical animation cycle."""
from pathlib import Path
import json,math,hashlib,base64,io
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'exports/ice_arena_aurora_v1';W,H=512,720;N=64;TICKS=6
REF=R/'exports/zones_relayout_v2/aurora'
def load(p):return Image.open(p).convert('RGBA')
def blank(size=(W,H)):return Image.new('RGBA',size)
def part(im,mask):
 a=np.array(im);a[~mask]=0;return Image.fromarray(a)
def paste(im,xy,size=(W,H)):
 c=blank(size);c.alpha_composite(im,xy);return c
def motion(raw,index):
 """Each column translated by an integer; no generated/recolored/interpolated RGB."""
 a=np.array(raw);h,w=a.shape[:2];phase=2*math.pi*(index%N)/N;x=np.arange(w)
 dy=np.rint(3*np.sin(phase+x/35)-3*np.sin(x/35)).astype(int)
 out=np.zeros_like(a);q=np.full((h,w,2),-1,np.int16)
 for sx in range(w):
  ys=np.arange(h);dest=ys+dy[sx];valid=(dest>=0)&(dest<h)&(a[:,sx,3]>0);out[dest[valid],sx]=a[ys[valid],sx];q[dest[valid],sx]=np.stack([np.full(valid.sum(),sx),ys[valid]],1)
 return Image.fromarray(out),q,dy
def star_frame(raw,index):
 a=np.array(raw);mask=a[:,:,3]>0;labels,n=nd.label(mask);phase=2*math.pi*(index%N)/N
 for k in range(1,n+1):a[labels==k,3]=round(178+77*(.5+.5*math.sin(phase+k*1.73)))
 return Image.fromarray(a)
def build():
 for d in ['static','aurora_frames','star_frames','review','provenance']: (O/d).mkdir(parents=True,exist_ok=True)
 ice=load(R/'pmdskyicearena.png');ia=np.array(ice);snow=tuple(ia[248,100]);skycol=load(R/'aurorepmdsky.png').getpixel((0,0));layers={}
 layers['01_dark_sky']=Image.new('RGBA',(W,H),skycol)
 layers['02_native_haze']=paste(load(REF/'ZonesV2_aurora_04_distant_haze.png'),(120,0))
 layers['03_native_distant_ice']=paste(load(REF/'ZonesV2_aurora_05_ice_foreground.png'),(120,0))
 # Snow shape from guide. Texture is the real flat snow pixel, not a new painted material.
 m=Image.new('L',(W,H));md=ImageDraw.Draw(m);md.ellipse((48,304,464,640),fill=255);md.rectangle((64,336,448,400),fill=255);md.rectangle((208,480,304,H),fill=255);floor=np.array(m)>0
 layers['04_snow_ground']=part(Image.new('RGBA',(W,H),snow),floor)
 # Explicit entrance lane: same authentic snow, independent from the arena's main surface.
 lane=Image.new('L',(W,H));ImageDraw.Draw(lane).polygon([(224,440),(288,440),(304,H),(208,H)],fill=255);pathmask=np.array(lane)>0
 layers['04_snow_ground']=part(layers['04_snow_ground'],~pathmask)
 layers['05_south_approach']=part(Image.new('RGBA',(W,H),snow),pathmask)
 rear=blank();operations=[]
 for sx,x in [(0,64),(192,256)]:
  box=(sx,0,sx+192,256);im=ice.crop(box);a=np.array(im);rgb=a[:,:,:3]
  sky_colors=np.unique(np.concatenate([ia[:31,:192,:3].reshape(-1,3),ia[:52,0,:3]]),axis=0)
  candidate=np.zeros(rgb.shape[:2],bool)
  for color in sky_colors:candidate|=np.all(rgb==color,axis=2)
  labels,_=nd.label(candidate);top=np.unique(labels[0]);sky_outside=np.isin(labels,top[top>0]);mask=~sky_outside&np.any(rgb!=np.array(snow[:3]),2);mask=nd.binary_fill_holes(mask)
  rear.alpha_composite(part(im,mask),(x,128));operations.append(dict(layer='06_north_ice_rim',source_rect=box,destination=[x,128]))
 layers['06_north_ice_rim']=rear
 side=blank()
 for sx,x,y in [(0,0,344),(96,416,344),(48,0,472),(96,416,472),(0,112,584),(96,304,584)]:
  box=(sx,272,sx+96,408);im=ice.crop(box);mask=nd.binary_fill_holes(np.any(np.array(im)[:,:,:3]!=np.array(snow[:3]),2));side.alpha_composite(part(im,mask),(x,y));operations.append(dict(layer='07_side_ice_and_ramp',source_rect=box,destination=[x,y]))
 layers['07_side_ice_and_ramp']=side
 fissures=blank()
 for pos in [(128,424),(336,464)]:
  box=(112,224,168,256);im=ice.crop(box);mask=np.any(np.array(im)[:,:,:3]!=np.array(snow[:3]),2);fissures.alpha_composite(part(im,mask),pos);operations.append(dict(layer='08_native_fissures',source_rect=box,destination=list(pos)))
 layers['08_native_fissures']=fissures
 for name,im in layers.items():im.save(O/'static'/f'IceAuroraV1_{name}.png')
 raw=load(REF/'ZonesV2_aurora_03_aurora_ribbons.png');stars=load(REF/'ZonesV2_aurora_02_stars.png');coords=[];scenes=[];bgs=[];frames=[]
 atlas=blank((raw.width*8,raw.height*8));staratlas=blank(atlas.size)
 for f in range(N):
  aurora,q,dy=motion(raw,f);st=star_frame(stars,f);coords.append(q);frames.append(aurora)
  aurora.save(O/'aurora_frames'/f'IceAuroraV1_Ribbons_{f:02}.png');st.save(O/'star_frames'/f'IceAuroraV1_Stars_{f:02}.png')
  atlas.alpha_composite(aurora,(f%8*raw.width,f//8*raw.height));staratlas.alpha_composite(st,(f%8*raw.width,f//8*raw.height))
  comp=layers['01_dark_sky'].copy();comp.alpha_composite(aurora,(120,0));comp.alpha_composite(st,(120,0));comp.alpha_composite(layers['02_native_haze']);comp.alpha_composite(layers['03_native_distant_ice']);bgs.append(comp.crop((120,0,384,216)))
  for name,im in list(layers.items())[3:]:comp.alpha_composite(im)
  scenes.append(comp)
  if f in [0,16,32,48]:comp.save(O/'review'/f'scene_{f:02}.png')
 atlas.save(O/'IceAuroraV1_Ribbons_64frames.png');staratlas.save(O/'IceAuroraV1_Stars_64frames.png');np.savez_compressed(O/'provenance/aurora_source_xy.npz',source_xy=np.stack(coords))
 # Preview palettes are quantized; PNG layers above remain authoritative native RGBs.
 for name,seq in [('scene',scenes),('background',bgs)]:
  rgb=[im.convert('RGB') for im in seq];palette=rgb[0].quantize(colors=256);pal=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in rgb];pal[0].save(O/'review'/f'{name}.gif',save_all=True,append_images=pal[1:],duration=100,loop=0,disposal=2,optimize=False)
  seq[0].save(O/'review'/f'{name}.webp',save_all=True,append_images=seq[1:],duration=100,loop=0,lossless=True)
 Image.fromarray(np.uint8(floor|pathmask)*255).save(O/'snow_surface_mask_NOT_COLLISION.png')
 report={'title':'Arène de glace sous les aurores','size':[W,H],'orientation':'South entrance to central/northern arena, not a lateral corridor','artwork':'Native PMD reference pixels; original references unchanged. Generated image is only a layout guide.','animation_origin':'NEW AUTHORED MOTION on canonical artwork. NOT a recovered canonical game cycle.','native_animation_search':'No matching cycle identified in inspected complete repository trees. Aurora_Beam_Custom is an attack, not this BG. Search is not an exhaustive proof of absence.','frames':N,'frame_ticks':TICKS,'duration_seconds':N*TICKS/60,'animation':['Aurora: integer per-column vertical wave, up to6px, no RGB interpolation','Stars: native shapes and RGB, authored alpha twinkle178..255'],'background_origin':[120,0],'frame_size':[264,216],'atlas_grid':[8,8],'loop':True,'static_layers':[{'id':name,'file':'static/IceAuroraV1_'+name+'.png'} for name in layers],'static_order_note':'Sky, animated ribbons, animated stars, haze, distant ice, ground, approach, rear rim, side ice, fissures.','terrain_operations':operations,'sources':[{'file':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p in ['pmdskyicearena.png','aurorepmdsky.png']],'runtime_PMDO':'NOT TESTED','art_approved':False,'collision':'NOT PROVIDED. Snow mask is only visible-surface geometry; raised ice must be considered separately.','completion_scope':'One animated scene proposal. Other requested zones/guild assets remain open.'}
 (O/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (O/'placement_recipe.json').write_text(json.dumps({'schema':'editor_placement_recipe_not_native_engine_file','frame_count':64,'frame_ticks':6,'frame_size_px':[264,216],'atlas_columns':8,'map_background_origin_px':[120,0],'render_order':['01_dark_sky','Ribbons animated','Stars animated']+[n for n in layers if n!='01_dark_sky'],'entrance_candidate_px':[224,704,64,16],'arena_target_px':[256,456],'parallax':'Not configured or runtime-tested; BG motion is separate from terrain.','collision_imported':False},ensure_ascii=False,indent=2)+'\n')
 def uri(p):return 'data:image/'+('gif' if p.suffix=='.gif' else 'png')+';base64,'+base64.b64encode(p.read_bytes()).decode()
 thumbs=''.join('<details><summary>'+name+'</summary><img src="'+uri(O/'static'/f'IceAuroraV1_{name}.png')+'"></details>' for name in layers)
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Arène glacée · aurores animées</title><style>body{background:#07172a;color:#e3edf4;font:16px system-ui;margin:30px auto;max-width:1200px;padding:20px}h1{font-size:36px}p{line-height:1.6;color:#b8cedd}.tag{color:#ffe3a2;border:1px solid #6a6554;padding:12px;border-radius:8px}.grid{display:flex;gap:32px;flex-wrap:wrap}img{max-width:100%;image-rendering:pixelated}.scene{width:512px}.info{max-width:540px}details{padding:12px;margin:8px 0;background:#142d40;border-radius:8px}details img{max-height:400px;object-fit:contain}a{color:#7ee4d8}</style><h1>Arène de glace · ciel d’aurores</h1><p class="tag">Dessin canonique · mouvement nouveau proposé — ce n’est pas un cycle animé natif retrouvé.</p><div class="grid"><div><img class="scene" src="__SCENE__"><p>Scène complète · 512 × 720 px · boucle 6,4 s</p></div><div class="info"><h2>Un décor vivant, un terrain stable</h2><p>Arrivée au sud vers une arène enneigée. Rubans d’aurore en ondulation lente derrière la bordure nord, étoiles scintillantes indépendantes. Les parois, la neige, l’accès et les fissures ne bougent pas.</p><img src="__BG__"><p>64étapes de6ticks ; PNG des rubans et des étoiles séparés, atlas8×8 et recette de placement. Les GIFs sont des aperçus à palette réduite ; les WebP sans perte et PNG sont également fournis.</p><p>Les recherches dans Halcyon et DumpAsset n’ont pas identifié les phases natives de ce fond précis. L’animation présentée est donc une création à partir de l’image canonique, sans changer ses couleurs. Le scintillement modifie seulement l’opacité des étoiles.</p><p>Aucun import, collision ou parallax PMDO validés. Le masque de neige n’est pas une collision. Cette scène ne termine pas les autres zones demandées.</p></div></div><h2>Calques statiques indépendants</h2>__LAYERS__</html>'''
 (R/'apercu_arene_glace_aurores_animees_v1.html').write_text(page.replace('__SCENE__',uri(O/'review/scene.gif')).replace('__BG__',uri(O/'review/background.gif')).replace('__LAYERS__',thumbs));print('Animated arena built:64steps,128animated PNGs,8static layers,2GIFs and2losslessWebPs.')
if __name__=='__main__':build()
