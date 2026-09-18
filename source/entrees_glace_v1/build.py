"""Trois entrées glacées référencées PMD, calques alignés et climat séparé."""
from pathlib import Path
import sys,json,hashlib,io,zipfile,importlib.util
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/entrees_glace_v1'
W,H=768,640;SIZE=(W,H);TERRAIN_H=512;TOP=128
sys.path.insert(0,str(ROOT/'source'));import ciels_valides as climate
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'));from night import night
spec=importlib.util.spec_from_file_location('color_helpers',ROOT/'source/caps_terrasses_v4/build.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
CONFIG=json.loads((HERE/'layouts.json').read_text())

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def blank():return Image.new('RGBA',SIZE)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def polygon(points,size):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return np.array(im)>0
def select(im,mask):
 a=np.array(im);a[~mask]=0;return Image.fromarray(a)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(p,layers):
 root=ET.Element('image',w=str(W),h=str(H),name=p.stem,version='0.0.3');stack=ET.SubElement(root,'stack');merged=blank()
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers.items()):z.writestr(f'data/layer{i}.png',png(im));merged.alpha_composite(im)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):ET.SubElement(stack,'layer',name=name,src=f'data/layer{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'));z.writestr('mergedimage.png',png(merged))
  thumb=merged.copy();thumb.thumbnail((256,256),Image.Resampling.NEAREST);z.writestr('Thumbnails/thumbnail.png',png(thumb))

def normalise(im):
 factor=min(W/im.width,TERRAIN_H/im.height);size=(round(im.width*factor),round(im.height*factor));x=(W-size[0])//2;y=H-size[1]
 out=Image.new(im.mode,SIZE);out.paste(im.resize(size,Image.Resampling.NEAREST),(x,y))
 return out,{'source_size':list(im.size),'scale_uniform':factor,'resized_size':list(size),'offset':[x,y],'method':'nearest uniforme, aucune déformation anisotrope ; bande de ciel indépendante au-dessus'}

def build():
 refs=[ROOT/'iceroadpmdsky.png',ROOT/'pmdskyicearena.png'];pal=np.unique(np.concatenate([np.array(load(p))[:,:,:3].reshape(-1,3) for p in refs]),axis=0);tree=cKDTree(helpers.lab(pal))
 def quantize(im):
  a=np.array(im);mask=a[:,:,3]>0;colors,inv=np.unique(a[mask,:3],axis=0,return_inverse=True);_,indices=tree.query(helpers.lab(colors));a[mask,:3]=pal[indices][inv];a[~mask]=0;return Image.fromarray(a)
 context=OUT/'climat';context.mkdir(parents=True,exist_ok=True)
 backgrounds={};shared={}
 for mode in ['jour','nuit']:
  backgrounds[mode]={}
  for name,im in [('ciel',climate.sky(SIZE,mode)),('etoiles',climate.stars(SIZE,mode)),('nuages_bande',climate.clouds(mode))]:
   p=context/f'ICE_ENTRY_V1_{name}_{mode}.png';save(im,p);shared[mode+'_'+name]=str(p.relative_to(OUT));backgrounds[mode][name]=im
 # Canonical texture effect V10: remove only tiny disconnected components (star remnants), no redraw/resampling.
 auroras=[];animation_origins=[]
 for i in range(10):
  src=ROOT/'renders/effet_boreale_canonique_v10/couches'/f'EffetBorealeV10_frame_{i:02d}.png';a=np.array(load(src));labels,_=ndimage.label(a[:,:,3]>0);counts=np.bincount(labels.ravel());ids=np.where(counts>=40)[0];ids=ids[ids!=0];a[~np.isin(labels,ids)]=0
  im=blank();im.paste(Image.fromarray(a),((W-a.shape[1])//2,0));p=context/f'ICE_ENTRY_V1_onde_canonique_{i:02d}.png';save(im,p);auroras.append(im)
  animation_origins.append({'source':str(src.relative_to(ROOT)),'sha256':sha(src),'output':str(p.relative_to(OUT)),'removed_small_components_lt_pixels':40,'offset':[(W-a.shape[1])//2,0],'resampled':False})
 # Alternative latest authored cycling (V12), preserved byte-for-byte in its source size.
 cycling=[]
 for i in range(8):
  src=ROOT/'renders/boreales_palette_cycling_v12/couches'/f'PaletteCycleV12_frame_{i:02d}.png';p=context/f'ICE_ENTRY_V1_palette_cycling_{i:02d}.png';p.write_bytes(src.read_bytes());cycling.append(str(p.relative_to(OUT)))
 auroras[0].save(context/'ICE_ENTRY_V1_onde_canonique.webp',save_all=True,append_images=auroras[1:],duration=160,loop=0,lossless=True,exact=True)
 records=[];floor_source=load(OUT/'bruts/sol_neige_doux.png')
 for config in CONFIG:
  slug=config['id'];folder=OUT/slug;folder.mkdir(parents=True,exist_ok=True);raw=load(OUT/'bruts'/config['raw']);a=helpers.chroma(raw);a[a[:,:,3]==0]=0;original=Image.fromarray(a);valid=a[:,:,3]>0
  floor_mask=polygon(config['floor'],raw.size)&valid
  # Remove side-wall fragments from the annotated floor polygon. Small enclosed
  # cracks stay on the floor; large rock masses are excluded explicitly below.
  bright=(a[:,:,0]>100)&(a[:,:,1]>160)&(a[:,:,2]>160)&floor_mask
  bright=ndimage.binary_opening(bright,iterations=1)
  floor_mask=ndimage.binary_fill_holes(bright)&floor_mask
  for points in config['obstacles']:floor_mask &= ~polygon(points,raw.size)
  # The cave threshold has a deliberately dark contact shadow, not a wall.
  tx,ty=config['threshold'];floor_mask[max(0,ty-20):ty+22,tx-28:tx+29] |= valid[max(0,ty-20):ty+22,tx-28:tx+29]
  # Seeded dark cavity selection constrained to its annotated rectangle.
  x0,y0,x1,y1=config['cave_roi'];region=np.zeros(valid.shape,bool);region[y0:y1,x0:x1]=True
  dark=region&(a[:,:,0]<65)&(a[:,:,1]<145)&(a[:,:,2]<175)&valid
  labels,_=ndimage.label(dark);sx,sy=config['cave_seed'];idx=labels[sy,sx];assert idx>0
  cave=ndimage.binary_fill_holes(labels==idx)&region&valid;floor_mask&=~cave
  yy,xx=np.mgrid[:raw.height,:raw.width];remaining=valid&~floor_mask&~cave
  foreground=remaining&(yy>=config['foreground_y']);left=foreground&(xx<raw.width/2);right=foreground&~left;relief=remaining&~foreground
  masks={'sol_visible':floor_mask,'profondeur_grotte':cave,'cliffs_reliefs':relief,'immersion_gauche':left,'immersion_droite':right}
  assert np.array_equal(sum(m.astype(np.uint8) for m in masks.values()),valid.astype(np.uint8))
  source_q=quantize(original);terrain,norm=normalise(source_q)
  base_raw=select(floor_source,valid);base_raw=quantize(base_raw);sol=np.array(base_raw);sol[floor_mask]=np.array(source_q)[floor_mask]
  planes={'01_sol_avec_chemin':normalise(Image.fromarray(sol))[0]}
  for name in ['profondeur_grotte','cliffs_reliefs','immersion_gauche','immersion_droite']:
   prefix={'profondeur_grotte':'02','cliffs_reliefs':'03','immersion_gauche':'04','immersion_droite':'05'}[name]
   planes[prefix+'_'+name]=normalise(select(source_q,masks[name]))[0]
  for name,mask in masks.items():save(normalise(Image.fromarray((mask*255).astype('uint8')))[0],folder/f'ICE_ENTRY_V1_{slug}_masque_{name}.png')
  composite=blank()
  for layer in planes.values():composite.alpha_composite(layer)
  assert composite.tobytes()==terrain.tobytes(),'Exact terrain recomposition'
  save(terrain,folder/f'ICE_ENTRY_V1_{slug}_terrain_jour.png')
  # Annotated traversal corridor; descriptive test artifact, NOT collision data.
  resized_w,resized_h=norm['resized_size'];dx,dy=norm['offset']
  project=lambda p:(round(p[0]*resized_w/raw.width)+dx,min(H-1,round(p[1]*resized_h/raw.height)+dy))
  route=[project(p) for p in config['route']];mask=Image.new('L',SIZE);d=ImageDraw.Draw(mask);d.line(route,fill=255,width=13,joint='curve')
  for x,y in route:d.ellipse((x-6,y-6,x+6,y+6),fill=255)
  save(mask,folder/f'ICE_ENTRY_V1_{slug}_controle_parcours.png')
  files={};mode_layers={}
  for mode in ['jour','nuit']:
   mode_layers[mode]={}
   for name,im in planes.items():
    result=im if mode=='jour' else night(im);p=folder/f'ICE_ENTRY_V1_{slug}_{name}_{mode}.png';save(result,p);mode_layers[mode][name]=str(p.relative_to(OUT))
   layers={'00_ciel_valide':backgrounds[mode]['ciel'],'00b_etoiles':backgrounds[mode]['etoiles'],'00c_onde_boreale':auroras[0] if mode=='nuit' else blank()}
   for name,path in mode_layers[mode].items():layers[name]=load(OUT/path)
   layers['06_nuages_wrap_overlay']=climate.wrap(backgrounds[mode]['nuages_bande'],SIZE)
   scene=blank()
   for im in layers.values():scene.alpha_composite(im)
   p=folder/f'ICE_ENTRY_V1_{slug}_scene_{mode}.png';save(scene,p);files['scene_'+mode]=str(p.relative_to(OUT))
   p=folder/f'ICE_ENTRY_V1_{slug}_{mode}.ora';ora(p,layers);files['ora_'+mode]=str(p.relative_to(OUT))
  # Animated night preview, terrain fixed. Preview cycle only for the aurora; clouds fixed here.
  scene_frames=[]
  for im in auroras:
   scene=backgrounds['nuit']['ciel'].copy();scene.alpha_composite(backgrounds['nuit']['etoiles']);scene.alpha_composite(im)
   for path in mode_layers['nuit'].values():scene.alpha_composite(load(OUT/path))
   scene.alpha_composite(climate.wrap(backgrounds['nuit']['nuages_bande'],SIZE));scene_frames.append(scene)
  p=folder/f'ICE_ENTRY_V1_{slug}_onde_preview.webp';scene_frames[0].save(p,save_all=True,append_images=scene_frames[1:],duration=160,loop=0,lossless=True,exact=True);files['preview_webp']=str(p.relative_to(OUT))
  p=folder/f'ICE_ENTRY_V1_{slug}_onde_preview.gif';scene_frames[0].save(p,save_all=True,append_images=scene_frames[1:],duration=160,loop=0);files['preview_gif']=str(p.relative_to(OUT))
  records.append({'id':slug,'title':config['title'],'description':config['description'],'raw':'bruts/'+config['raw'],'raw_sha256':sha(OUT/'bruts'/config['raw']),'normalization':norm,'size':list(SIZE),'layers':mode_layers,'files':files,'route_centerline':route,'threshold_xy':project(config['threshold']),'south_xy':route[0],'palette_locked':True,'canonical_tile_identity':False,'runtime_PMDO':'NOT TESTED','art_approved':False})
 manifest={'title':'Trois entrées de grotte glacées','date':'2026-09-18','canvas':list(SIZE),'zones':records,'shared':shared,'climate_provenance':climate.provenance(),'ice_palette_rgb':pal.tolist(),'references':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in refs],'hidden_floor':{'source':'bruts/sol_neige_doux.png','sha256':sha(OUT/'bruts/sol_neige_doux.png'),'method':'Nouvelle sous-couche générée ; pixels visibles des sols et chemins préservés après palette. Faces cachées des cliffs non reconstituées.'},'aurora':{'frames':10,'frame_ms':160,'period_ms':1600,'wrap':False,'sources':animation_origins,'description':'Texture canonique PMD du lot V10, mouvement adapté existant ; petites composantes détachées retirées pour séparer les étoiles. Pas le cycle officiel retrouvé.'},'cycling_alternative':{'frames':cycling,'frame_ms':120,'source':'boreales_palette_cycling_v12','note':'Dessin généré V12 conservé byte-identique, pas une texture native extraite.'},'clouds':{'strip_width':1440,'height':208,'velocity_px_s':-4,'period_ms':360000,'overlay':True,'formula':'x(t)=-floor(t_ms*4/1000) mod1440 ; dessiner les copies jointives'},'layer_order':['ciel','etoiles','onde','01_sol_avec_chemin','02_profondeur_grotte','03_cliffs_reliefs','04_immersion_gauche','05_immersion_droite','nuages_overlay'],'limits':['Nouveaux dessins générés référencés, palette issue des PNG canoniques ; pas de motifs natifs certifiés.','Sol caché généré, faces cachées des reliefs non reconstituées.','PNG et ORA, pas de Ground/collisions/warp ni runtime PMDO.','GIF/WebP de scène : onde seule en boucle, nuages phase0 fixes ; wrap nuages dans le viewer et la recette.']}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 # Board with actual day/night scenes and names, nearest display only.
 board=Image.new('RGB',(1560,2080),'#101d2b');d=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
 d.text((24,20),'ENTRÉES GLACÉES / SUD → GROTTE AU NORD',font=font,fill='#e7f0ee');d.text((24,59),'3 layouts · ciel validé · familles de nuages · étoiles · onde boréale indépendante',font=small,fill='#acc5d3')
 for i,z in enumerate(records):
  y=106+i*646
  for j,mode in enumerate(['jour','nuit']):
   scene=load(OUT/z['files']['scene_'+mode]);scene.thumbnail((748,602),Image.Resampling.NEAREST);board.paste(scene,(14+j*778,y+30));d.text((22+j*778,y),z['title']+' / '+mode,font=small,fill='#e9f2e6')
 d.text((24,2050),'Candidats référencés PMD. Calques vérifiés, intégration et collisions non testées.',font=small,fill='#acc5d3');save(board,OUT/'PLANCHE_ENTREES_GLACE.png')
 layer_board(records)
 print('3 layouts, 5 calques terrain chacun × jour/nuit, 6 ORA, 10 frames boréales + alternative V12.')
def layer_board(records):
 board=Image.new('RGB',(1600,1680),'#142632');d=ImageDraw.Draw(board);f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 for i,z in enumerate(records):
  for j,(name,path) in enumerate(z['layers']['jour'].items()):
   x=j*320;y=i*540;im=load(OUT/path);im.thumbnail((312,475),Image.Resampling.NEAREST);board.paste(im,(x,y+60),im);d.text((x+8,y+34),name[3:].replace('_',' '),font=f,fill='white')
  d.text((8,i*540+6),z['title'],font=f,fill='#a9e9e0')
 d.text((12,1640),'Cinq calques de terrain / zone. Ciel, étoiles, nuages et onde séparés dans climat/.',font=f,fill='white');save(board,OUT/'PLANCHE_CALQUES_TERRAIN.png')

if __name__=='__main__':build()
