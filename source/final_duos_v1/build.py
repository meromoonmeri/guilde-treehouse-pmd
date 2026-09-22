"""D22: finish the eleven day/night zone duos without replacing prior releases.
Ground editing assets, independent logical light/effect layers; not gameplay validation.
"""
from pathlib import Path
from functools import lru_cache
import json,io,sys,copy,hashlib,zipfile,subprocess,shutil,struct,argparse,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;C=R/'.cache/final_duos_v1';O=C/'out';ST=C/'stage'
def mod(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=mod('d22_vp',R/'source/viewport_pmdo_v1/build.py');gfx=v.gfx;night=v.night
exec(compile((R/'source/viewport_pmdo_v1/verify.py').read_bytes(),'vp_verify','exec'),v.__dict__)
def sha(b):return hashlib.sha256(b).hexdigest()
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def save(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def image(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):return v.png(im)
def L(title,frames,dt=60):return v.layer(title,frames,dt)
@lru_cache(maxsize=24)
def raw(name):
 if name.startswith('secret:'):
  ident=name.split(':')[1];b=subprocess.check_output(['git','show','90fa7e28:source/secrete_pmd_v1/raws/'+ident+'.webp'],cwd=R)
 else:
  p=S/'raws'/(name+'.webp');b=p.read_bytes() if p.exists() else subprocess.check_output(['git','show','c4354b27:'+str(p.relative_to(R))],cwd=R)
 return image(b)
def key(im,size):
 a=np.array(im.resize(size,Image.Resampling.NEAREST));r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);a[(r>90)&(b>90)&(r>g*1.45+15)&(b>g*1.45+15)]=0;return Image.fromarray(a)
def quant(im,ref):
 a=np.array(ref);col=np.unique(a[:,:,:3][a[:,:,3]>0],axis=0);p=Image.new('P',(1,1));p.putpalette(np.vstack([col,np.tile(col[0],(256-len(col),1))]).astype('uint8').tobytes());a=np.array(im);q=np.array(im.convert('RGB').quantize(palette=p,dither=Image.Dither.NONE).convert('RGBA'));q[:,:,3]=a[:,:,3];q[q[:,:,3]==0]=0;return Image.fromarray(q)
def fit(im,bounds):
 im=im.crop(im.getbbox());s=min(bounds[0]/im.width,bounds[1]/im.height);return im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
def blank(size):return Image.new('RGBA',size)
@lru_cache(maxsize=1)
def refs():
 with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as z:return {n:image(z.read('references/DB1_native_'+n+'.png')) for n in ['H16P01','H07P08','H06P05']}
@lru_cache(maxsize=1)
def flames():
 with zipfile.ZipFile(R/'renders/spinda_torches_v1/Spinda_torches_8angles_animees.zip') as z:return [image(z.read(f'flamme/Torche_flamme_native_{i:02d}.png')) for i in range(4)]

def missing():
 result=[];rs=refs()
 # Discipline: continuous sand, generated paving/access, native forest and practice modules.
 size=(480,336);ref=rs['H16P01'];a=np.array(ref);green=(a[:,:,1].astype(int)>a[:,:,0].astype(int)+8)&(a[:,:,1].astype(int)>a[:,:,2].astype(int)+20);veget=a.copy();veget[~green]=0;veget=Image.fromarray(veget)
 props=[]
 for box in [(64,64,120,160),(360,64,416,160),(100,264,124,304),(140,280,164,320),(164,280,188,320),(292,280,316,320),(316,280,340,320),(356,264,380,304)]:
  crop=np.array(ref.crop(box));r,g,b=np.moveaxis(crop[:,:,:3].astype(int),2,0);mask=(r>g*.82)&(g>b*1.25)&(r<239);labels,_=ndimage.label(mask,np.ones((3,3)));counts=np.bincount(labels.ravel());counts[0]=0;keep=np.isin(labels,np.flatnonzero(counts>=100));keep=ndimage.binary_fill_holes(keep);crop[~keep]=0;props.append(Image.fromarray(crop))
 for mode in ['entree','fin']:
  sand=Image.new('RGBA',size,tuple(a[200,100]));pav=key(raw('discipline_dalles_'+mode),size);pav=quant(pav,ref)
  if mode=='entree':arch=blank(size);p=fit(key(raw('discipline_acces'),size),(176,88));arch.alpha_composite(p,(152,0))
  else:
   arch=blank(size);part=ref.crop((160,0,320,80));q=np.array(part);q[green[:80,160:320]]=0;arch.alpha_composite(Image.fromarray(q),(160,0))
  obj=blank(size);positions=[(0,72,80),(1,352,80),(2,144,264),(3,184,280),(6,272,280),(7,312,264)] if mode=='entree' else [(2,112,112),(3,112,176),(4,344,112),(5,344,176),(6,168,272),(7,288,272)]
  for i,x,y in positions:obj.alpha_composite(props[i],(x,y))
  result.append({'id':'discipline_'+mode,'duo':'discipline','layers':[L('Sable continu',sand),L('Dalles',pav),L('Vegetation native detouree',veget),L('Acces et monument',quant(arch,ref)),L('Exercices natifs1x',obj)],'spawn':[240,256],'offset':[0,-24],'tick':0,'notes':['Nouvelle proposition MD2, pas une restauration silencieuse du MD1 perdu. Natif1x sur vegetation/exercices; creations sur les dalles/acces.']})
 # Secret forest: continuous blue meadow, tree border, stump, foliage, native web.
 size=(456,336);ref=rs['H07P08'];web=np.array(ref.crop((192,0,264,80)));mask=(web[:,:,1]>=175)&(web[:,:,2]>=200);web[~mask]=0;web=Image.fromarray(web)
 for mode in ['entree','fin']:
  sol=quant(key(raw('secret:sol_entree_corrige' if mode=='entree' else 'secret:sol_fin'),size),ref);trees=quant(key(raw('secret:arbres_entree_corrige' if mode=='entree' else 'secret:arbres_fin'),size),ref);leaves=quant(key(raw('secret:feuillage_fin'),size),ref);stump=blank(size)
  piece=fit(key(raw('secrete_souches'),size),(64,56));stump.alpha_composite(quant(piece,ref),(88,200) if mode=='entree' else (196,108));webs=blank(size)
  for pos in ([(192,8),(24,96),(360,88)] if mode=='entree' else [(192,0),(32,112),(352,112)]):webs.alpha_composite(web,pos)
  result.append({'id':'secrete_'+mode,'duo':'secrete','layers':[L('Prairie continue',sol),L('Arbres et racines',trees),L('Souche repere',stump),L('Vegetation basse',leaves),L('Toiles natives1x',webs)],'spawn':[228,272],'offset':[0,-40],'tick':0,'notes':['Feuillage final reutilise: le premier feuillage entree avait des cadres parasites. Toiles natives reemployees sans recoloration en jour.']})
 # Scorched plains: same warm field/horizon, independent stones,trunks and native flames.
 size=(456,336);ref=rs['H06P05'];back=quant(key(raw('brulees_fond'),size),ref)
 for mode in ['entree','fin']:
  sol=quant(key(raw('brulees_sol_'+mode),size),ref);sol.paste((0,0,0,0),(0,0,456,96));rocks=blank(size);src=key(raw('brulees_rochers'),size)
  for box,xy in [((0,0,228,168),(8,120)),((228,0,456,168),(376,120)),((0,168,228,336),(8,256)),((228,168,456,336),(376,256))]:rocks.alpha_composite(fit(src.crop(box),(72,64)),xy)
  trunks=blank(size);src=key(raw('brulees_troncs'),size)
  for box,xy in zip([(0,0,228,336),(228,0,456,336)],[(88,224),(328,224)] if mode=='entree' else [(184,136),(232,136)]):trunks.alpha_composite(fit(src.crop(box),(48,56)),xy)
  frames=[]
  for f in flames():
   im=blank(size)
   for xy in [(32,132),(392,132),(32,264),(392,264)]:im.alpha_composite(f,xy)
   frames.append(im)
  result.append({'id':'brulees_'+mode,'duo':'brulees','layers':[L('Horizon et ciel',back),L('Prairie chaude continue',sol),L('Rochers',quant(rocks,ref)),L('Troncs',quant(trunks,ref)),L('Flammes natives reemployees',frames,6)],'spawn':[228,260],'offset':[0,-40],'tick':0,'notes':['Flammes Halcyon/Ledian reemployees a1x,4poses/6ticks; pas attribuees faussement a la BPA H06P05.']})
 return result

@lru_cache(maxsize=1)
def records():return v.collect()+missing()
@lru_cache(maxsize=1)
def assets():return v.skies()
@lru_cache(maxsize=1)
def native_light():
 p=v.packs()['lisiere']
 with zipfile.ZipFile(p) as z:
  m=json.loads(z.read('manifest.json'));return {k:[image(z.read(n)) for n in m['animations'][k]['frames']] for k in ['rayons','particules']}

def night_record(day):
 group=day['duo'];size=day['layers'][0]['frames'][0].size;layers=[l for l in day['layers'] if not any(s in l['title'].lower() for s in ['rgb555','effet rgb'])];base=v.compose(layers,0);arr=np.array(base);H,W=arr.shape[:2];yy,xx=np.indices((H,W));open_sky=group in ['plaines','ile','desert','brulees'];sky=(arr[:,:,2]>arr[:,:,0]+12)&(arr[:,:,2]>arr[:,:,1])&(yy<128) if open_sky else np.zeros((H,W),bool)
 if group=='ile':sky=np.array(layers[0]['frames'][0])[:,:,3]>0;layers=layers[1:]
 result=[];emission=np.zeros((H,W),bool)
 for l in layers:
  is_hot=any(s in l['title'].lower() for s in ['lave','flamme','cascade']);frames=[]
  for im in l['frames']:
   a=np.array(im if is_hot else night(im));a[sky]=0;frames.append(Image.fromarray(a))
  result.append(L(l['title']+(' / emissif' if is_hot else ' / copie nuit'),frames,l['dt']))
  if is_hot:pass
 occluded=np.zeros((H,W),bool)
 for l in reversed(layers):
  masks=[np.array(im)[:,:,3]>0 for im in l['frames']]
  if any(k in l['title'].lower() for k in ['lave','flamme','cascade']):emission|=np.logical_or.reduce(masks)&~occluded
  occluded|=np.logical_and.reduce(masks)
 # A separate .dir decoration keeps animation cheap and separate from the tiles.
 temp=v.compose(result,0);dark=np.array(temp);lightbase=np.array(base);strength=np.full((H,W),.04 if group=='volcan' else .12,dtype=float)
 if emission.any():strength+=ndimage.gaussian_filter(emission.astype(float),sigma=18)*1.4
 elif group in ['foret','lisiere','secrete','jungle']:strength+=.19*np.exp(-((xx-W*.48)**2/(W*.29)**2+(yy-H*.56)**2/(H*.65)**2))
 else:strength+=.15*np.exp(-((xx-W*.5)**2/(W*.45)**2+(yy-H*.6)**2/(H*.7)**2))
 fx=[];rays=native_light()['rayons'] if group in ['foret','lisiere','secrete','jungle','discipline'] else None
 if group in ['marin','desert']:
  with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as z:
   m=json.loads(z.read('manifest.json'));track=m['animations']['marin' if group=='marin' else 'desert_voile'];rays=[image(z.read(n)) for n in track['frames']]
 count=len(rays) if rays else 4
 for f in range(count):
  st=strength.copy()
  if rays:
   ra=np.array(rays[f]);rh=min(H,ra.shape[0]);rw=min(W,ra.shape[1]);lum=ra[:rh,:rw,:3].max(2)/255.;st[:rh,:rw]+=lum*(.16 if group=='desert' else .45)*(ra[:rh,:rw,3]>0)
  elif emission.any():st*=([.88,1,.95,.91][f])
  else:st*=([.98,1,.99,.97][f])
  a=np.zeros_like(dark);target=np.minimum(lightbase[:,:,:3].astype(float)*np.array([.7,.83,1.08]),255)
  if group in ['volcan','brulees']:target=np.minimum(lightbase[:,:,:3].astype(float)*[1.1,.87,.65]+[12,4,0],255)
  a[:,:,:3]=np.rint(target).astype('uint8');a[:,:,3]=np.rint(np.clip(st,0,.65)*255).astype('uint8');a[sky|emission|(dark[:,:,3]==0)]=0;fx.append(Image.fromarray(a))
 rec={k:copy.deepcopy(val) for k,val in day.items() if k!='layers'};rec.update(id=day['id']+'_nuit',layers=result,tick=0,light=L('Lumiere nocturne adaptee',fx,8 if rays else 12),sky=bool(open_sky),sky_mask=sky)
 rec['notes']+=['Copie nuit Abyss; lumiere separee compilee pour ce decor, pas un shader eclairant automatiquement les acteurs. Natifs jour preserves.','Rayons PMD reutilises en masques de clair de lune' if rays else 'Lueur nocturne adaptee; emission chaude conservee sur lave/flammes.']
 return rec

def background(rec,tick):
 size=rec['layers'][0]['frames'][0].size;out=Image.new('RGBA',size,'#081329')
 if rec.get('sky'):
  A=assets();off=((size[0]-456)//2,0);out.alpha_composite(A['nuit'],off);out.alpha_composite(A['stars'][(tick//8)%12],off);out.alpha_composite(A['moon'],off);cl=A['clouds']['nuit'];x=int(-8*tick/60)%512
  for px in [x-512,x,x+512]:out.alpha_composite(cl,(px,0))
 return out

def render(rec,tick=0):
 if 'light' not in rec:return v.compose(rec['layers'],tick)
 out=background(rec,tick);out.alpha_composite(v.compose(rec['layers'],tick));l=rec['light'];out.alpha_composite(l['frames'][(tick//l['dt'])%len(l['frames'])]);return out

def write_dir(path,frames):v.write_anim_dir(path,frames)
def export(rec,dest):
 ident='dn1_'+rec['id'];size=rec['layers'][0]['frames'][0].size;W,H=size;layers=[]
 for j,l in enumerate(rec['layers']):
  b=gfx.TileBank('DN1_'+rec['id']+f'_{j:02}');arrays=[np.array(i) for i in l['frames']];b.ids[bytes(256)]=(0,0);b.data[(0,0)]=bytes(256)
  def cell(x,y):
   fs=[b.add(Image.fromarray(a[y*8:y*8+8,x*8:x*8+8]),x,y) for a in arrays]
   if all(f is None for f in fs):return []
   fs=[f or {'Sheet':b.name,'TexLoc':{'X':0,'Y':0}} for f in fs];return [fs[0]] if all(f==fs[0] for f in fs) else fs
  layers.append(gfx.layer(l['title'],W//8,H//8,cell,l['dt']));b.write(dest/f'Content/Tile/{b.name}.tile')
  for f,im in enumerate(l['frames']):save(dest/f'PNG/{ident}/DN1_{rec["id"]}_{j:02}_{f:03}.png',png(im))
 bg=gfx.background('');decos=[]
 if 'light' in rec:
  name='DN1_'+rec['id']+'_lumiere';p=dest/f'Content/BG/{name}.dir';write_dir(p,rec['light']['frames']);save(dest/f'Content/Object/{name}.dir',p.read_bytes());p.unlink()
  decos=[{'MapLoc':{'X':0,'Y':0},'ObjectAnim':{'$type':'RogueEssence.Content.ObjAnimData, RogueEssence','AnimIndex':name,'FrameTime':rec['light']['dt'],'StartFrame':-1,'EndFrame':-1,'AnimDir':0,'Alpha':255,'AnimFlip':0}}]
  for f,im in enumerate(rec['light']['frames']):save(dest/f'PNG/{ident}/DN1_{rec["id"]}_lumiere_{f:03}.png',png(im))
  entries=[];sky=Image.new('RGBA',size,'#081329')
  if rec.get('sky'):sky.alpha_composite(assets()['nuit'],((W-456)//2,0))
  name='DN1_'+rec['id']+'_ciel';write_dir(dest/f'Content/BG/{name}.dir',[sky]);entries.append({'BG':gfx.background(name)})
  if rec.get('sky'):
   for kind,ims,dt in [('etoiles',assets()['stars'],8),('lune',[assets()['moon']],1),('nuages',[assets()['clouds']['nuit']],1)]:
    name='DN1_'+rec['id']+'_'+kind;write_dir(dest/f'Content/BG/{name}.dir',ims);b=gfx.background(name,0,-8 if kind=='nuages' else 0,kind=='nuages');b['BGAnim']['FrameTime']=dt;b['MapLoc']['X']=(W-456)//2 if kind!='nuages' else 0;entries.append({'BG':b})
  bg={'$type':'RogueEssence.Dungeon.LayeredBG, RogueEssence','Layers':entries}
 doc=json.loads(v.support('refs/crooked.rsground').decode('utf-8-sig'));o=doc['Object'];o.update(AssetName=ident,Name={'DefaultText':rec['id'],'LocalTexts':{}},Released=False,Comment='D22 Ground editing asset. Collisions/warps/gameplay not authored. See README.',TexSize=1,Layers=layers,Background=bg,EdgeView=1,ViewCenter=None,ViewOffset=dict(zip(['X','Y'],rec['offset'])),ActiveChar=None,Music='',Status={});o['obstacles']=[[{'Bounds':{'X':x*8,'Y':y*8,'Width':8,'Height':8},'Tags':0} for y in range(H//8)]for x in range(W//8)]
 x,y=rec['spawn'];o['Entities']=[{'Name':'Entree indicative','Visible':True,'MapChars':[],'GroundObjects':[],'Spawners':[],'Markers':[{'EntName':'entrance','Direction':0,'EntEnabled':True,'triggerType':0,'Collider':{'X':x-8,'Y':y-8,'Width':16,'Height':16}}]}];o['Decorations']=[{'Name':'Eclairage separe','Layer':0,'Visible':True,'Anims':decos}]
 save(dest/f'Data/Ground/{ident}.rsground',jb(doc));save(dest/f'Data/Script/ground/{ident}/init.lua',f'local {ident} = {{}}\nreturn {ident}\n'.encode());im=render(rec,rec['tick']);view,rect=v.crop_camera(im,rec['spawn'],rec['offset']);save(dest/f'Apercus/{ident}.png',png(im));save(dest/f'Apercus/{ident}_viewport.png',png(view))
 return {'id':rec['id'],'asset':ident,'size':size,'layers':[{'title':l['title'],'frames':len(l['frames']),'ticks':l['dt']}for l in rec['layers']],'light':{'frames':len(rec['light']['frames']),'ticks':rec['light']['dt']}if 'light'in rec else None,'viewport':rect,'notes':rec['notes']}

def serialized(dest,o,tick):
 out=v.serialized_scene(dest,o,tick)
 for layer in o['Decorations']:
  for d in layer['Anims']:
   a=d['ObjectAnim'];im=v.decode_dir(dest/f'Content/Object/{a["AnimIndex"]}.dir',tick,a['FrameTime']);out.alpha_composite(im,(d['MapLoc']['X'],d['MapLoc']['Y']))
 return out

def build(group):
 dest=ST/group
 if dest.exists():shutil.rmtree(dest)
 O.mkdir(parents=True,exist_ok=True);days=[r for r in records() if r['duo']==group];assert len(days)==2,(group,len(days));chosen=days+[night_record(r) for r in days];metas=[]
 for r in chosen:
  print('EXPORT',r['id'],flush=True);metas.append(export(r,dest))
 manifest={'duo':group,'maps':metas,'day_maps':2,'night_maps':2,'runtime_PMDO':False,'collision':'editor scaffolds, all free; author gameplay before playing','night':'Day copies untouched; Abyss night copies; logical emission/illumination, separate effects and native moon where sky exists','scope':'22 day and22 night maps when all11 duo packs are present; does not complete canonical ice arena IB2','source_warning':'The first10 DB1 maps retain their historical visible-surface layers; no hidden-floor reconstruction claimed.'}
 save(dest/'manifest.json',jb(manifest));save(dest/'README.md',(S/'README.md').read_bytes());save(dest/'INSTALLER.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes());checks=[]
 for r,meta in zip(chosen,metas):
  doc=json.loads((dest/f'Data/Ground/{meta["asset"]}.rsground').read_text());assert doc['Object']['EdgeView']==1 and not doc['Object']['Released']
  for t in [0,97]:
   a=np.array(serialized(dest,doc['Object'],t));b=np.array(render(r,t));assert np.max(np.abs(a.astype(int)-b.astype(int)))<=(2 if 'light' in r else 1),(r['id'],t,np.max(np.abs(a.astype(int)-b.astype(int))));assert np.array_equal(a[:,:,3],b[:,:,3])
  checks.append(r['id']+': all references decode, exact alpha, RGB<=2 night /1 day premult tolerance,320x240 crop, independent effects')
 save(dest/'verification.json',jb({'checks':checks,'runtime_PMDO':False}));board=Image.new('RGB',(960,744),'#111c2b');d=ImageDraw.Draw(board)
 for i,r in enumerate(chosen):
  im=render(r,r['tick']).convert('RGB');x=(i%2)*480;y=(i//2)*372;board.paste(im,(x,y+28));d.text((x+12,y+8),r['id'],fill='#dce9ff')
 save(O/f'D22_{group}.png',png(board));frames=[]
 for t in range(0,288,12):
  im=Image.new('RGB',(640,268),'#101b2b');draw=ImageDraw.Draw(im)
  for i,r in enumerate(chosen[2:]):im.paste(v.crop_camera(render(r,t),r['spawn'],r['offset'])[0].convert('RGB'),(i*320,28));draw.text((i*320+8,8),r['id'],fill='#dce9ff')
  frames.append(im)
 frames[0].save(O/f'D22_{group}_nuit.webp',save_all=True,append_images=frames[1:],duration=200,loop=1,lossless=True,method=3)
 save(dest/f'Apercus/D22_{group}.png',png(board));save(dest/f'Apercus/D22_{group}_nuit.webp',(O/f'D22_{group}_nuit.webp').read_bytes())
 with zipfile.ZipFile(O/f'D22_{group}_PMDO.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(dest.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo(str(p.relative_to(dest)),(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=6)
 with zipfile.ZipFile(O/f'D22_{group}_PMDO.zip') as z:assert z.testzip() is None
 print('PASS / PACK',group,len(chosen),'maps',flush=True)
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('duo');a=p.parse_args();build(a.duo)
