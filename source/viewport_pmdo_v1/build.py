"""Native Ground serialization at unchanged pixel scale; viewport is NOT map size.
Build per-duo PMDO editing packs, with explicit animation/engine limitations.
"""
from pathlib import Path
import sys,io,json,struct,zipfile,hashlib,copy,importlib.util,subprocess,shutil,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;C=R/'.cache/viewport_pmdo_v1';OUT=C/'out';ST=C/'stage'
def loadmod(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
gfx=loadmod('pmdo_codec',R/'source/pmdo_cote/build.py');nr=loadmod('native_reader',R/'source/cote_v5_expeditions/audit_references.py');night=loadmod('abyss_night',R/'source/cote_v4_abyss/night.py').night

def sha(b):return hashlib.sha256(b).hexdigest()
def image(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):return gfx.png_bytes(im)
def save(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def readim(z,n):return image(z.read(n))
def gpu(im):
 a=np.array(im);a[:,:,:3]=((a[:,:,:3].astype('uint16')>>3)*255//31).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a)
def add(base,over):
 b=np.array(base).astype('uint16');a=np.array(over).astype('uint16');b[:,:,:3]=np.minimum((b[:,:,:3]>>3)+(a[:,:,:3]>>3)*(a[:,:,3:4]>0),31)*255//31;return Image.fromarray(b.astype('uint8'))
def compose(layers,tick=0):
 out=Image.new('RGBA',layers[0]['frames'][0].size)
 for l in layers:out.alpha_composite(l['frames'][(tick//l['dt'])%len(l['frames'])])
 return out
def layer(title,frames,dt=60):return {'title':title,'frames':frames if isinstance(frames,list) else [frames],'dt':dt}
def correction(base,over):
 target=add(base,over);a=np.array(target);a[np.all(np.array(base)==a,axis=2)]=0;return Image.fromarray(a)
def crop_camera(im,spawn,offset,zoom=1):
 w,h=round(320/zoom),round(240/zoom);cx=spawn[0]+offset[0];cy=spawn[1]+offset[1];x=max(0,min(im.width-w,int(cx-w/2)));y=max(0,min(im.height-h,int(cy-h/2)));return im.crop((x,y,x+w,y+h)),[x,y,w,h]

def packs():
 paths={'lisiere':R/'.cache/lisiere_pmd_v1/releases/LE1_lisiere_calques_et_effets.zip','finale':R/'.cache/suite_foret_cafe_v1/releases/LF1_finale_calques.zip','jungle':R/'.cache/jungle_pmd_v1/releases/JG1_jungle_duo_calques.zip','plaines':R/'.cache/plaines_pmd_v1/releases/WP1_plaines_duo_calques.zip'}
 commands={'lisiere':['source/lisiere_pmd_v1/release.py'],'finale':['source/suite_foret_cafe_v1/storage.py'],'jungle':['source/jungle_pmd_v1/restore.py','--restore'],'plaines':['source/plaines_pmd_v1/restore.py','--restore']}
 for k,p in paths.items():
  if not p.exists():subprocess.run([sys.executable]+commands[k],cwd=R,check=True,stdout=subprocess.DEVNULL)
 return paths

def collect():
 result=[];paths=packs()
 with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as z:
  m=json.loads(z.read('manifest.json'));an=m['animations']
  for rec in m['maps']:
   ident=rec['id'];biome=ident.split('_')[0];size=tuple(rec['size']);layers=[];notes=[]
   if biome in ['ile','volcan']:
    key='ile' if biome=='ile' else 'volcan_lave';a=an[key];layers.append(layer(key,[readim(z,n) for n in a['frames']],a['frame_ticks']))
   else:layers.append(layer('Fond',Image.new('RGBA',size,{'foret':'#112c17','desert':'#392e16','marin':'#03243f'}[biome])))
   layers.extend(layer(Path(p).stem,readim(z,p)) for p in rec['layers'])
   if biome in ['foret','desert','marin']:
    for l in layers:l['frames']=[gpu(i) for i in l['frames']]
    base=compose(layers)
    if biome=='foret':ovs=[readim(z,an['foret']['frames'][(64//7)%14*32+(64//8)%32])];dt=60;notes.append('Lumiere additive figee au tick64; cycles independants conserves dans le pack source, pas pretendus portes au moteur.')
    elif biome=='desert':
     im=readim(z,an['desert_voile']['frames'][8]);a=np.array(im);ov=Image.new('RGBA',size);ov.paste(Image.fromarray(a[:,(np.arange(size[0])-16)%im.width]),(0,0));ovs=[ov];dt=60;notes.append('Voile additif + translation en pose64; animation longue non portee dans cette base editeur.')
    else:ovs=[readim(z,n) for n in an['marin']['frames']];dt=8;notes.append('Lumiere RGB555 compilee sur le terrain: desactiver/recalculer apres changement du decor.')
    layers.append(layer('Effet RGB555 compile', [correction(base,i) for i in ovs],dt))
   if biome=='volcan':a=an['volcan_cendres'];layers.append(layer('Cendres',[readim(z,n) for n in a['frames']],a['frame_ticks']))
   result.append({'id':ident,'duo':biome,'layers':layers,'spawn':[size[0]//2,size[1]-72],'offset':[0,-24],'notes':notes+['Calques historiques de surfaces visibles; fonds caches non reconstruits.'],'tick':64})
 for mode,key in [('entree','lisiere'),('fin','finale')]:
  with zipfile.ZipFile(paths[key]) as z:
   m=json.loads(z.read('manifest.json'));ls=[layer('Fond',gpu(Image.new('RGBA',tuple(m['size']),(4,44,12,255))))]+[layer(Path(n).stem,gpu(readim(z,n))) for n in m['static_layers']]
   ov=Image.alpha_composite(readim(z,m['animations']['rayons']['frames'][8]),readim(z,m['animations']['particules']['frames'][9]));ls.append(layer('Lumiere RGB555 pose64',correction(compose(ls),ov)))
   result.append({'id':'lisiere_'+mode,'duo':'lisiere','layers':ls,'spawn':[240,264],'offset':[0,-32],'notes':['Sol continu original conserve. Lumiere pose64; les deux cycles autonomes restent dans les sources.'],'tick':64})
 for key in ['jungle','plaines']:
  with zipfile.ZipFile(paths[key]) as z:
   m=json.loads(z.read('manifest.json'))
   for rec in m['maps']:
    ls=[layer(l['title'],[readim(z,n) for n in l['frames']],l['frame_ticks']) if 'frames' in l else layer(l['title'],readim(z,l['file'])) for l in rec['layers']]
    size=ls[0]['frames'][0].size;result.append({'id':key+'_'+rec['id'],'duo':key,'layers':ls,'spawn':[size[0]//2,208 if key=='plaines' else 264],'offset':[0,-80 if key=='plaines' else -32],'notes':['Calques originaux1x, cycles simples conserves.'],'tick':0})
 return result


def skies():
 src=Image.open(R/'bgnightbackgroundpmdskyda.png').convert('RGBA');a=np.array(src);h,w=a.shape[:2];yy,xx=np.indices((h,w));moon_area=(xx>=120)&(xx<184)&(yy>=20)&(yy<84);moon_mask=moon_area&(a[:,:,0]>96)&(a[:,:,1]>96)&(a[:,:,2]<a[:,:,0].astype(int)+24)
 lunar=a[20:84,120:184].copy();lunar[~moon_mask[20:84,120:184]]=0;moon=Image.fromarray(lunar);assert moon.getbbox()==(0,0,64,64)
 # All halo colour donors are unobstructed native sky in the top18 rows.
 safe=(yy<18)&(a[:,:,0]<64)&(a[:,:,1]<100)&(a[:,:,2]>a[:,:,1]);sy,sx=np.where(safe);rad=np.sqrt((sx-152)**2+(sy-52)**2);order=np.argsort(rad);rad=rad[order];sx=sx[order];sy=sy[order];Y,X=np.indices((112,456));rr=np.sqrt((X-228)**2+(Y-44)**2);n=np.searchsorted(rad,rr).clip(0,len(rad)-1);sky_n=Image.fromarray(a[sy[n],sx[n]])
 moon_plane=Image.new('RGBA',(456,112));moon_plane.alpha_composite(moon,(196,12))
 seeds=(a[:,:,0]>200)&(a[:,:,1]>210)&(a[:,:,2]>225)&(yy<104)&~moon_area;mask=ndimage.binary_dilation(seeds,iterations=1)&(a[:,:,0]>80)&(a[:,:,1]>100)&(a[:,:,2]>150)&~moon_area;labels,count=ndimage.label(mask);stars=a[:112].copy();stars[~mask[:112]]=0
 # Keep the moon unobstructed; stars behind its new footprint are omitted.
 covered=np.array(moon_plane)[:,:,3]>0;stars[covered]=0;frames=[]
 for t in range(12):
  b=stars.copy();off=np.isin(labels[:112], [i for i in range(1,count+1) if (t+i*5)%12<2]);b[off]=0;frames.append(Image.fromarray(b))
 paths=packs()
 with zipfile.ZipFile(paths['plaines']) as z:ref=np.array(readim(z,'references/WP1_H06P01_natif_00.png'))
 sky_d=np.zeros((112,456,4),dtype='uint8')
 for y in range(112):
  row=ref[min(y,90)];candidates=row[(row[:,2]>row[:,0]+20)&(row[:,0]<180)&(row[:,3]>0)];pixel=candidates[len(candidates)//2] if len(candidates) else ref[0,228];sky_d[y]=pixel
 clouds={mode:Image.open(R/f'renders/beach_network_v1/fonds/BeachNetwork_nuages_{mode}_wrap.png').convert('RGBA') for mode in ['jour','nuit']}
 for mode in clouds:assert clouds[mode].size==(512,112)
 return {'jour':Image.fromarray(sky_d),'nuit':sky_n,'moon':moon_plane,'moon_crop':moon,'stars':frames,'clouds':clouds,'source_sha256':sha((R/'bgnightbackgroundpmdskyda.png').read_bytes())}

def variants(records,assets):
 out=[]
 for orig in records:
  if orig['duo']!='plaines':continue
  for mode in ['jour','nuit']:
   rec={k:copy.deepcopy(v) for k,v in orig.items() if k!='layers'};rec['id']=orig['id']+('_nuages' if mode=='jour' else '_nuit');rec['notes']=['Variante additive, original inchange. Nuages generes reemployes, mouvement adapte -8px/s, boucle64s.','Lune de la reference PMD Sky1x. Etoiles originales a visibilite adaptee,12poses x8ticks; ce scintillement nest pas un cycle natif. Collines en pose0 dans ces variantes; les originaux conservent leurs18phases.']
   rec['layers']=[{'title':l['title']+(' - copie nuit Abyss' if mode=='nuit' else ''),'frames':[night(im) if mode=='nuit' else im.copy() for im in l['frames'][:1]],'dt':l['dt']} for l in orig['layers'][1:]];rec['background_mode']=mode;out.append(rec)
 return out

def bg_render(assets,mode,size,tick):
 out=Image.new('RGBA',size);out.alpha_composite(assets[mode],(0,0))
 if mode=='nuit':out.alpha_composite(assets['stars'][(tick//8)%12]);out.alpha_composite(assets['moon'])
 cloud=assets['clouds'][mode];shift=int(-8*tick/60)%512
 for x in [shift-512,shift,shift+512]:out.alpha_composite(cloud,(x,0))
 return out

def render(rec,assets,tick=None):
 tick=rec['tick'] if tick is None else tick;out=compose(rec['layers'],tick)
 if rec.get('background_mode'):
  bg=bg_render(assets,rec['background_mode'],out.size,tick);bg.alpha_composite(out);out=bg
 return out

def write_anim_dir(path,frames):
 w,h=frames[0].size;cols=min(4,len(frames));rows=(len(frames)+cols-1)//cols;sheet=Image.new('RGBA',(cols*w,rows*h))
 for i,im in enumerate(frames):sheet.paste(gfx.premult(im),(i%cols*w,i//cols*h))
 b=png(sheet);save(path,struct.pack('<q',len(b))+b+struct.pack('<4i',w,h,0,len(frames)))

def export_map(rec,assets):
 slug='vp1_'+rec['id'];dest=ST/rec['duo'];size=rec['layers'][0]['frames'][0].size;w,h=size[0]//8,size[1]//8;layers=[];banks=[]
 for j,l in enumerate(rec['layers']):
  bank=gfx.TileBank(f'VP1_{rec["id"]}_{j:02d}');arrays=[np.array(im) for im in l['frames']]
  if len(arrays)>1:bank.ids[bytes(256)]=(0,0);bank.data[(0,0)]=bytes(256)
  def cell(x,y):
   fs=[]
   for a in arrays:
    tile=Image.fromarray(a[y*8:y*8+8,x*8:x*8+8]);f=bank.add(tile,x,y)
    # Animated transparent poses need an explicit transparent tile, never None.
    if f is None and len(arrays)>1:
     f={'Sheet':bank.name,'TexLoc':{'X':0,'Y':0}}
    fs.append(f)
   if all(f is None for f in fs) or (len(arrays)>1 and all(f['TexLoc']=={'X':0,'Y':0} for f in fs)):return []
   if all(f==fs[0] for f in fs):return [fs[0]]
   return fs
  layers.append(gfx.layer(l['title'],w,h,cell,l['dt']));bank.write(dest/f'Content/Tile/{bank.name}.tile');banks.append(bank.name)
  save(dest/f'PNG/{slug}/{j:02d}.png',png(l['frames'][0]))
 background=gfx.background('')
 if rec.get('background_mode'):
  mode=rec['background_mode'];bgs=[];name='VP1_CIEL_'+mode;write_anim_dir(dest/f'Content/BG/{name}.dir',[assets[mode]]);bgs.append({'BG':gfx.background(name)})
  if mode=='nuit':
   for name,frames,dt in [('VP1_ETOILES',assets['stars'],8),('VP1_LUNE',[assets['moon']],1)]:
    write_anim_dir(dest/f'Content/BG/{name}.dir',frames);b=gfx.background(name);b['BGAnim']['FrameTime']=dt;bgs.append({'BG':b})
  name='VP1_NUAGES_'+mode;write_anim_dir(dest/f'Content/BG/{name}.dir',[assets['clouds'][mode]]);bgs.append({'BG':gfx.background(name,0,-8,True)});background={'$type':'RogueEssence.Dungeon.LayeredBG, RogueEssence','Layers':bgs}
 template=json.loads(support('refs/crooked.rsground').decode('utf-8-sig'));o=template['Object'];o.update(AssetName=slug,Name={'DefaultText':rec['id'],'LocalTexts':{}},Released=False,Comment='Base editable1x; collisions/warps a preparer. Voir README et limites animations.',TexSize=1,Layers=layers,Background=background,EdgeView=1,ViewCenter=None,ViewOffset={'X':rec['offset'][0],'Y':rec['offset'][1]},ActiveChar=None,Music='',Status={})
 o['obstacles']=[[{'Bounds':{'X':x*8,'Y':y*8,'Width':8,'Height':8},'Tags':0} for y in range(h)] for x in range(w)]
 x,y=rec['spawn'];o['Entities']=[{'Name':'Entrees et vos acteurs','Visible':True,'MapChars':[],'GroundObjects':[],'Spawners':[],'Markers':[{'EntName':'entrance','Direction':0,'EntEnabled':True,'triggerType':0,'Collider':{'X':x-8,'Y':y-8,'Width':16,'Height':16}}]}];o['Decorations']=[{'Name':'Vos decorations','Layer':2,'Visible':True,'Anims':[]}]
 save(dest/f'Data/Ground/{slug}.rsground',jb({'Version':'0.7.15.1','Object':o}));save(dest/f'Data/Script/ground/{slug}/init.lua',f'-- Editor base. No forced global zoom or gameplay.\nlocal {slug} = {{}}\nreturn {slug}\n'.encode())
 world=render(rec,assets);view,rect=crop_camera(world,rec['spawn'],rec['offset']);save(dest/f'Apercus/{slug}_carte.png',png(world));save(dest/f'Apercus/{slug}_viewport.png',png(view));return {'id':rec['id'],'asset':slug,'size':list(size),'spawn':rec['spawn'],'offset':rec['offset'],'viewport_at_x1':rect,'tile_size':8,'banks':banks,'notes':rec['notes'],'background_variant':rec.get('background_mode'),'animation_tracks':[{'title':l['title'],'frames':len(l['frames']),'ticks':l['dt']} for l in rec['layers']]}


def support(name):
 p=S/name
 if p.exists():return p.read_bytes()
 return subprocess.check_output(['git','show',REV+':source/viewport_pmdo_v1/'+name],cwd=R)

def references():
 data=support('refs/crooked.rsground');o=json.loads(data.decode('utf-8-sig'))['Object'];im=Image.new('RGBA',(320,240));cache={}
 for l in o['Layers']:
  for x,col in enumerate(l['Tiles']):
   for y,t in enumerate(col):
    for tr in t['Layers']:
     f=tr['Frames'][0];name=f['Sheet']
     if not name:continue
     if name not in cache:
      p=C/'ref_tiles'/f'{name}.tile';save(p,support('refs/'+name+'.tile'));cache[name]=nr.tiles(p)[1]
     pos=f['TexLoc'];im.alpha_composite(nr.straight(cache[name][pos['X'],pos['Y']]),(x*8,y*8))
 return im

def build(duo=None):
 OUT.mkdir(parents=True,exist_ok=True);records=collect();assets=skies();records+=variants(records,assets);chosen=[r for r in records if duo is None or r['duo']==duo];groups=sorted(set(r['duo'] for r in chosen));manifests={}
 for group in groups:
  dest=ST/group
  if dest.exists():shutil.rmtree(dest)
  metas=[]
  for rec in chosen:
   if rec['duo']==group:metas.append(export_map(rec,assets))
  manifest={'duo':group,'maps':metas,'runtime_tested':False,'schema':'RogueEssence Ground + native8px TileBank + DirSheet','camera':{'screen':[320,240],'recommended_zoom':'x1','crooked_map':[320,240],'crooked_tex_size':1,'crooked_edge_view':1,'crooked_offset':[0,0],'note':'WindowZoom is independent. At x2Far viewport640x480 can show a whole map; do not resize images to compensate.'},'collisions':'ALL FREE editing scaffolds, no gameplay/warps, markers to verify','limited_animations':'Forest and desert additive effects held at tick64. Others keep simple native tracks. Compiled RGB555 light depends on its terrain; disable/rebuild when repainting.','missing_maps':['MD1 unpublished assets absent from recovered branch','secret forest only raw generations, not finalized','burned plains not made']}
  save(dest/'manifest.json',jb(manifest));save(dest/'README.md',support('README.md'));save(dest/'INSTALLER.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes());save(dest/'references/VP1_Crooked_terrain.png',png(references()));save(dest/'references/camera_audit.json',jb({'halcyon_pin':'da6c2130d641507447e6386a5e47a296e8cb4c71','crooked_blob':'1be7032fd8e0d3f2f7bba468336ef3d15abd8368','engine_pin':'8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b','source_ground_sha256':sha(support('refs/crooked.rsground'))}))
  if group=='plaines':
   for name,im in [('VP1_lune_native64.png',assets['moon_crop']),('VP1_ciel_nuit.png',assets['nuit']),('VP1_lune_calque.png',assets['moon']),('VP1_nuages_jour_wrap.png',assets['clouds']['jour']),('VP1_nuages_nuit_wrap.png',assets['clouds']['nuit'])]:save(dest/'Effets'/name,png(im))
   for f,im in enumerate(assets['stars']):save(dest/f'Effets/VP1_etoiles_{f:02d}.png',png(im))
   save(dest/'Effets/provenance.json',jb({'moon_source':'bgnightbackgroundpmdskyda.png','sha256':assets['source_sha256'],'moon_crop':[120,20,184,84],'position':[196,12],'scale':1,'night_sky':'reconstructed radial field using unchanged native top18-row colours; not an unchanged source background','clouds':'existing generated BeachNetwork silhouettes, copied not changing Beach; adapted movement -8px/s;512px period64s','stars':'source pixels with added staggered on/off visibility;12x8ticks, adapted not native cycle','terrain':'night copies via Abyss formula, original daytime untouched'}))
  manifests[group]=manifest;print('Built duo',group,len(metas),'Ground maps',flush=True)
 # Direct reference-sized viewport comparison; these are simulated renders, not engine screenshots.
 if 'plaines' in groups:
  recs={r['id']:r for r in records};board=Image.new('RGB',(960,552),'#182b29');draw=ImageDraw.Draw(board);panels=[('Crooked reference / x1',references()),('Plaines entree / x1',crop_camera(render(recs['plaines_entree'],assets),recs['plaines_entree']['spawn'],recs['plaines_entree']['offset'])[0]),('Plaines finale / x1',crop_camera(render(recs['plaines_fin'],assets),recs['plaines_fin']['spawn'],recs['plaines_fin']['offset'])[0])]
  for mode in ['entree','fin']:
   r=recs['plaines_'+mode+'_nuit'];panels.append(('Nuit '+mode+' / x1',crop_camera(render(r,assets),r['spawn'],r['offset'])[0]))
  r=recs['plaines_entree_nuages'];panels.append(('Nuages overlay / x1',crop_camera(render(r,assets),r['spawn'],r['offset'])[0]))
  for i,(title,im) in enumerate(panels):x=i%3*320;y=i//3*276;draw.text((x+8,y+8),title,fill='#e7eacb');board.paste(im.convert('RGB'),(x,y+28))
  save(OUT/'VP1_cadrages.png',png(board));movie=[]
  for t in range(0,288,8):
   r=recs['plaines_entree_nuit'];im=render(r,assets,t);view,_=crop_camera(im,r['spawn'],r['offset']);movie.append(view.convert('RGB'))
  movie[0].save(OUT/'VP1_nuit_extrait.webp',save_all=True,append_images=movie[1:],duration=[round((t+8)*1000/60)-round(t*1000/60) for t in range(0,288,8)],loop=1,lossless=True,method=4)
  save(OUT/'VP1_plaines_nuit.png',png(render(recs['plaines_entree_nuit'],assets)))
 return manifests

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--duo');a=p.parse_args();build(a.duo)
