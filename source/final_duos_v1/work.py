"""FD1 — three remaining duos: secret forest H07P08, Mt Discipline H16P01, burned plains H06P05.
Native references decoded from the pinned Red port bank; generated planes are explicit and quantized
to the native palette of their place. Nothing here is claimed pixel-native unless flagged native_pixels.
Usage: python source/final_duos_v1/work.py --build --verify [--pmdo]
"""
from pathlib import Path
from functools import lru_cache
import io,json,hashlib,subprocess,sys,zipfile,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=R/'source/final_duos_v1';C=R/'.cache/final_duos_v1';O=C/'build';N=C/'native/data/map_bg'
sys.path.insert(0,str(R/'source/dungeon_biomes_v1'))
from red import decode,palettes
from native_archive import native_source_archive
SECRET_REV='90fa7e2814e15aa25d1ab417ddbf60067f7a875e'
PLACES={'secrete':{'ref':'H07P08','size':(456,312),'title':'FORET SECRETE'},'discipline':{'ref':'H16P01','size':(480,336),'title':'MONT DISCIPLINE'},'brulees':{'ref':'H06P05','size':(456,336),'title':'PLAINES BRULEES'}}
def sha(b):return hashlib.sha256(b).hexdigest()
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def img(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()
def gitdata(path,rev):return subprocess.check_output(['git','show',rev+':'+path],cwd=R)

@lru_cache(maxsize=None)
def raws():
 idx={}
 for r in json.loads((S/'raws/index.json').read_text()):idx[r['id']]=dict(r,rev=None)
 for r in json.loads((R/'source/secrete_pmd_v1/raws/index.json').read_text()):idx['secrete_'+r['id']]=dict(r,rev=r['commit'])
 return idx
@lru_cache(maxsize=None)
def raw(k):
 r=raws()[k];p=R/r['path'];b=p.read_bytes() if (p.exists() and r['rev'] is None) else gitdata(r['path'],r['rev'] or 'HEAD')
 assert sha(b)==r['sha256'],k;im=img(b);assert sha(im.tobytes())==r['rgba_sha256'],k;return im
def keyed(im,size):
 a=np.array(im.resize(size,Image.Resampling.NEAREST));r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);a[(r>120)&(b>100)&(g<130)&(r>g*1.6)&(b>g*1.5)]=0;a[a[:,:,3]==0]=0;return Image.fromarray(a)
def quant(im,cols):
 cols=np.asarray(cols,dtype='uint8');p=Image.new('P',(1,1));p.putpalette(np.vstack([cols,np.tile(cols[0],(256-len(cols),1))]).tobytes());a=np.array(im);b=np.array(im.convert('RGB').quantize(palette=p,dither=Image.Dither.NONE).convert('RGBA'));b[:,:,3]=a[:,:,3];b[b[:,:,3]==0]=0;return Image.fromarray(b)
def fit(im,size):
 im=im.crop(im.getbbox());s=min(size[0]/im.width,size[1]/im.height);return im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.NEAREST)
def place(size,pieces):
 out=Image.new('RGBA',size)
 for im,xy in pieces:out.alpha_composite(im,xy)
 return out

def native_init():
 N.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(native_source_archive()) as z:
  for n in z.namelist():
   if n.startswith('data/map_bg/') and any(n[12:].startswith(p['ref']) for p in PLACES.values()):(N/n[12:]).write_bytes(z.read(n))
@lru_cache(maxsize=None)
def native(ref,tick=0):
 ims,meta,ix,tid=decode(ref,tick,N);return np.array(ims[0]),meta,ix[0],tid[0]
def native_colors(ref):
 a=native(ref)[0];return np.unique(a[a[:,:,3]>0][:,:3],axis=0)
def subset(cols,pred):
 c=cols.astype(int);return cols[pred(c[:,0],c[:,1],c[:,2])]

# ---------------------------------------------------------------- secret forest
def build_secrete(files):
 ref='H07P08';size=PLACES['secrete']['size'];a,meta,idx,_=native(ref);cols=native_colors(ref)
 stump=a.copy();stump[(idx>>4)!=4]=0;stump=Image.fromarray(stump[120:168,192:264]);assert stump.getbbox()==(0,0,72,48)
 files['native/FD1_souche_H07P08_1x.png']=png(stump)
 webs=keyed(raw('secrete_toiles'),size);wa=np.array(webs);labels,n=ndimage.label(wa[:,:,3]>0,np.ones((3,3)));objs=ndimage.find_objects(labels);webs_list=[]
 for i,s in enumerate(objs,1):
  y,x=s
  if (labels==i).sum()<200:continue
  piece=wa[y,x].copy();piece[labels[y,x]!=i]=0;webs_list.append(Image.fromarray(piece))
 assert len(webs_list)==5,len(webs_list)
 maps=[]
 for mode,tag in [('entree','E'),('fin','F')]:
  sol=quant(keyed(raw('secrete_sol_entree_corrige' if mode=='entree' else 'secrete_sol_fin'),size),cols);sa=np.array(sol);sa[:,:,3]=255;sol=Image.fromarray(sa)
  trees=quant(keyed(raw('secrete_arbres_entree_corrige' if mode=='entree' else 'secrete_arbres_fin'),size),cols)
  fol=quant(keyed(raw('secrete_feuillage_fin'),size),cols)
  if mode=='entree':fol=fol.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  wp=[(fit(webs_list[0],(56,56)),(96,8)),(fit(webs_list[1],(56,56)),(148,20)),(fit(webs_list[2],(56,56)),(300,8)),(fit(webs_list[3],(40,40)),(20,120)),(fit(webs_list[4],(40,40)),(396,120))] if mode=='entree' else [(fit(webs_list[1],(64,64)),(48,16)),(fit(webs_list[2],(56,56)),(344,12)),(fit(webs_list[0],(48,48)),(204,4)),(fit(webs_list[3],(40,40)),(8,150)),(fit(webs_list[4],(40,40)),(408,150))]
  toiles=quant(place(size,wp),cols)
  layers=[{'id':'sol','title':'Sol continu (genere, palette native)','file':None,'im':sol,'native_pixels':False},{'id':'arbres','title':'Troncs et canopee (generes)','im':trees,'native_pixels':False},{'id':'toiles','title':'Toiles (generees, redimensionnees)','im':toiles,'native_pixels':False},{'id':'feuillage','title':'Vegetation basse avant (generee)','im':fol,'native_pixels':False}]
  if mode=='fin':layers.insert(2,{'id':'souche','title':'Souche native H07P08 1x','im':place(size,[(stump,(192,140))]),'native_pixels':True})
  maps.append(register(files,'secrete',mode,tag,size,layers,{'south':'arrivee libre','north':'fond forestier ferme, pas de ciel','stump':'native pixels, unmodified, repositioned'}))
 return maps,{'native_animation':None,'note':'H07P08 has no BPA/BPL animation; no motion invented.'}

# ---------------------------------------------------------------- Mt Discipline
def build_discipline(files):
 ref='H16P01';size=PLACES['discipline']['size'];cols=native_colors(ref)
 greens_sand=subset(cols,lambda r,g,b:((g>r)&(g>b))|((r>200)&(g>190)&(b>110)));stone=cols
 maps=[]
 acc=quant(fit(keyed(raw('discipline_acces'),size),(112,80)),stone)
 acces_pos=(size[0]//2-acc.width//2,0)
 for mode,tag in [('entree','E'),('fin','F')]:
  sol=quant(keyed(raw('discipline_sable_entree'),size),greens_sand);sa=np.array(sol);sa[:,:,3]=255
  if mode=='fin':sa=sa[:,::-1]
  sol=Image.fromarray(sa)
  dal=keyed(raw('discipline_dalles_entree' if mode=='entree' else 'discipline_dalles_fin'),size);dal=quant(fit(dal,(280,300) if mode=='entree' else (352,272)),stone);dalles=place(size,[(dal,((size[0]-dal.width)//2,20 if mode=='entree' else 40))])
  veg=quant(keyed(raw('discipline_vegetation_entree' if mode=='entree' else 'discipline_vegetation_fin'),size),cols);va=np.array(veg)
  # Wooden posts/logs are a separate accessory group: tan colours, connected, away from the green frame.
  woody=(va[:,:,3]>0)&(va[:,:,0].astype(int)>va[:,:,1].astype(int)-10)&(va[:,:,2]<170)&(va[:,:,0]>120)
  lab,n=ndimage.label(ndimage.binary_closing(woody,np.ones((3,3))),np.ones((3,3)));acc_mask=np.zeros(woody.shape,bool)
  for i,sl in enumerate(ndimage.find_objects(lab),1):
   cnt=(lab==i).sum();y,x=sl
   if 60<=cnt<=1500 and (y.stop-y.start)<=64 and (x.stop-x.start)<=48 and y.start>40:acc_mask|=lab==i
  acc_mask=ndimage.binary_dilation(acc_mask,iterations=1)&(va[:,:,3]>0);acs=va.copy();acs[~acc_mask]=0;va=va.copy();va[acc_mask]=0;veg=Image.fromarray(va);accessoires=Image.fromarray(acs)
  acces=place(size,[(acc,acces_pos)]) if mode=='entree' else Image.new('RGBA',size)
  layers=[{'id':'sol','title':'Sol continu sable/herbe (genere, palette native)','im':sol,'native_pixels':False},{'id':'dalles','title':'Dalles d entrainement (generees)','im':dalles,'native_pixels':False}]
  if mode=='entree':layers.append({'id':'acces','title':'Acces nord: portique et marches (genere)','im':acces,'native_pixels':False})
  layers.append({'id':'vegetation','title':'Cadre vegetal (genere)','im':veg,'native_pixels':False});layers.append({'id':'accessoires','title':'Poteaux et rondins d entrainement (generes, separes)','im':accessoires,'native_pixels':False})
  maps.append(register(files,'discipline',mode,tag,size,layers,{'south':'arrivee sable, ouverture basse','north':'portique nord' if mode=='entree' else 'cadre ferme'}))
 return maps,{'native_animation':None,'note':'H16P01 static; no animation invented.'}

# ---------------------------------------------------------------- burned plains
def build_brulees(files):
 ref='H06P05';size=PLACES['brulees']['size'];a,meta,idx,tid=native(ref);pal=idx>>4;cols=native_colors(ref)
 warm=subset(cols,lambda r,g,b:(r>150)&(b<130))
 fond=a.copy();fond[96:]=0;fond=Image.fromarray(fond);loin=a.copy();m=np.zeros(pal.shape,bool);m[96:136]=np.isin(pal[96:136],[1,2]);loin[~m]=0;loin=Image.fromarray(loin)
 frames=[native(ref,t)[0] for t in range(0,30,3)];big_anim=tid>=770;var=np.any(np.stack(frames)!=frames[0],axis=0).any(2)&big_anim
 flame_cols={(239,95,47),(239,127,55),(247,143,47),(247,175,55),(247,223,63),(247,239,111),(215,63,39)}
 flamey=np.zeros(pal.shape,bool)
 for c in flame_cols:flamey|=np.all(a[:,:,:3]==c,axis=2)
 boxes=[(22,94,98,146),(358,94,434,146),(0,286,50,336),(406,286,456,336)];inbox=np.zeros(pal.shape,bool)
 for x0,y0,x1,y1 in boxes:inbox[y0:y1,x0:x1]=True
 lab,n=ndimage.label((var|flamey)&inbox,np.ones((3,3)));keep=np.isin(lab,np.unique(lab[var]));keep&=lab>0
 feux=[]
 for f in frames:b=f.copy();b[~keep]=0;feux.append(Image.fromarray(b))
 phases=[native(ref,t)[0] for t in range(0,36,4)];small=np.isin(pal,[5,6])&np.any(np.stack(phases)!=phases[0],axis=0).any(2);petites=[]
 for f in phases:b=f.copy();b[~small]=0;petites.append(Image.fromarray(b))
 assert len({p.tobytes() for p in petites})==9 and len({f.tobytes() for f in feux})==10
 for i,f in enumerate(feux):files[f'animations/FD1_feux_natifs_{i:02d}.png']=png(f)
 for i,f in enumerate(petites):files[f'animations/FD1_flammeches_natives_{i:02d}.png']=png(f)
 files['native/FD1_fond_H06P05_1x.png']=png(fond);files['native/FD1_lointain_H06P05_1x.png']=png(loin)
 tracks={'feux':{'id':'feux','title':'Grands feux natifs (BPA 10 poses x3 ticks)','frames':[f'animations/FD1_feux_natifs_{i:02d}.png' for i in range(10)],'frame_ticks':3,'native_pixels':True,'isolation':'colour+variation mask inside the 4 native animated blocks; rock/ground of those blocks omitted, not a native standalone sprite'},'flammeches':{'id':'flammeches','title':'Flammeches au sol natives (palettes5/6, 9 phases x4 ticks)','frames':[f'animations/FD1_flammeches_natives_{i:02d}.png' for i in range(9)],'frame_ticks':4,'native_pixels':True}}
 rocks_src=keyed(raw('brulees_rochers'),size);ra=np.array(rocks_src);labels,n=ndimage.label(ra[:,:,3]>0,np.ones((3,3)));pieces=[]
 for i,s in enumerate(ndimage.find_objects(labels),1):
  if (labels==i).sum()<400:continue
  y,x=s;p=ra[y,x].copy();p[labels[y,x]!=i]=0;pieces.append(Image.fromarray(p))
 pieces.sort(key=lambda p:-p.width*p.height);assert len(pieces)>=4
 troncs_src=keyed(raw('brulees_troncs'),size);ta=np.array(troncs_src);labels,n=ndimage.label(ndimage.binary_dilation(ta[:,:,3]>0,iterations=6),np.ones((3,3)));trunks=[]
 for i,s in enumerate(ndimage.find_objects(labels),1):
  y,x=s;p=ta[y,x].copy();p[labels[y,x]!=i]=0;trunks.append(Image.fromarray(p))
 assert len(trunks)==2
 maps=[]
 for mode,tag in [('entree','E'),('fin','F')]:
  sol=keyed(raw('brulees_sol_'+mode),size);sa=np.array(sol);sa[:96]=0;sa[96:,3]=255;sol=quant(Image.fromarray(sa),warm)
  if mode=='entree':rp=[(quant(fit(pieces[0],(96,64)),cols),(0,120)),(quant(fit(pieces[1],(96,64)),cols),(360,120)),(quant(fit(pieces[2],(64,48)),cols),(0,280)),(quant(fit(pieces[3],(64,48)),cols),(392,280))]
  else:rp=[(quant(fit(pieces[0],(88,56)),cols),(8,112)),(quant(fit(pieces[1],(88,56)),cols),(360,112)),(quant(fit(pieces[2],(56,40)),cols),(120,104)),(quant(fit(pieces[3],(56,40)),cols),(280,104))]
  rochers=place(size,rp)
  tp=[(quant(fit(trunks[0],(72,72)),cols),(96,248)),(quant(fit(trunks[1],(72,72)),cols),(288,248))] if mode=='entree' else [(quant(fit(trunks[0],(64,64)),cols),(24,200)),(quant(fit(trunks[1],(64,64)),cols),(368,200))]
  troncs=place(size,tp)
  layers=[{'id':'fond','title':'Ciel natif H06P05 1x','im':fond,'native_pixels':True,'group':'fond'},{'id':'sol','title':'Sol brule continu (genere, palette native)','im':sol,'native_pixels':False},{'id':'lointain','title':'Collines lointaines natives 1x','im':loin,'native_pixels':True,'group':'fond'},{'id':'rochers','title':'Roches chaudes (generees, repositionnees)','im':rochers,'native_pixels':False},{'id':'troncs','title':'Troncs brules (generes)','im':troncs,'native_pixels':False},dict(tracks['flammeches'],im=petites,group='feux'),dict(tracks['feux'],im=feux,group='feux')]
  maps.append(register(files,'brulees',mode,tag,size,layers,{'south':'arrivee libre','north':'horizon natif, pas une sortie moteur','animation':'two native tracks at native positions; joint period 180 ticks'}))
 return maps,{'native_animation':{'bpa':meta['bpa'],'palette_spec':meta['palette_spec']},'note':'Tracks kept separate at native cadence; no invented motion.'}

def register(files,duo,mode,tag,size,layers,extra):
 rec={'id':f'{duo}_{mode}','duo':duo,'tag':tag,'size':list(size),'layers':[],**extra}
 for l in layers:
  im=l.pop('im')
  if isinstance(im,list):
   for path,frame in zip(l['frames'],im):files.setdefault(path,png(frame))
   rec['layers'].append({k:v for k,v in l.items()})
  else:
   name=f'calques/FD1_{duo}_{tag}_{l["id"]}.png';files[name]=png(im);rec['layers'].append({**{k:v for k,v in l.items() if k!='file'},'file':name})
 rec['semantic_groups']=len({l.get('group',l['id']) for l in rec['layers']});return rec

def frame_of(files,l,tick):
 if 'frames' in l:return img(files[l['frames'][(tick//l['frame_ticks'])%len(l['frames'])]])
 return img(files[l['file']])
def scene(files,rec,tick=0):
 im=Image.new('RGBA',tuple(rec['size']))
 for l in rec['layers']:im.alpha_composite(frame_of(files,l,tick))
 return im
def board(files,rec,title):
 panels=[(l['title'],frame_of(files,l,0)) for l in rec['layers']]+[(f'Composition - {rec["semantic_groups"]} groupes',scene(files,rec))]
 w,h=rec['size'];cols=2;rows=(len(panels)+1)//2;out=Image.new('RGB',(cols*w,rows*(h+32)),'#22272b');d=ImageDraw.Draw(out)
 for j,(t,im) in enumerate(panels):
  x=j%cols*w;y=j//cols*(h+32);d.text((x+8,y+8),f'{title} {rec["tag"]} - {t}',fill='#e8e4c8');bg=Image.new('RGBA',(w,h),'#3a3f44');bg.alpha_composite(im);out.paste(bg.convert('RGB'),(x,y+32))
 return out
def duo_img(files,a,b,title,tick=0):
 w=a['size'][0];h=max(a['size'][1],b['size'][1]);out=Image.new('RGB',(w+b['size'][0],h+32),'#22272b');d=ImageDraw.Draw(out);d.text((12,10),title+' / ENTREE',fill='#e8e4c8');d.text((w+12,10),title+' / FINALE',fill='#e8e4c8');out.paste(scene(files,a,tick).convert('RGB'),(0,32));out.paste(scene(files,b,tick).convert('RGB'),(w,32));return out
def animate(frames,path,ticks):
 frames=[f.convert('RGB') for f in frames];dur=[round((i+1)*ticks*1000/60)-round(i*ticks*1000/60) for i in range(len(frames))];frames[0].save(path,save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,method=6,minimize_size=True)

def build():
 O.mkdir(parents=True,exist_ok=True);native_init();result={}
 for duo,fn in [('secrete',build_secrete),('discipline',build_discipline),('brulees',build_brulees)]:
  files={};maps,extra=fn(files);title=PLACES[duo]['title']
  for rec in maps:
   files[f'apercus/FD1_{duo}_{rec["tag"]}_calques.png']=png(board(files,rec,title));(O/f'FD1_{duo}_{rec["tag"]}_calques.png').write_bytes(files[f'apercus/FD1_{duo}_{rec["tag"]}_calques.png'])
  d=duo_img(files,maps[0],maps[1],title);files['apercus/FD1_duo.png']=png(d);(O/f'FD1_{duo}_duo.png').write_bytes(png(d))
  if duo=='brulees':animate([duo_img(files,maps[0],maps[1],title,t) for t in range(0,180,3)],O/'FD1_brulees_duo_anime.webp',3)
  ref=PLACES[duo]['ref'];files[f'references/FD1_{ref}_natif.png']=png(Image.fromarray(native(ref)[0]))
  for p in sorted(N.iterdir()):
   if p.name.startswith(ref):files['native/data/map_bg/'+p.name]=p.read_bytes()
  prov={k:{kk:vv for kk,vv in v.items() if kk!='rev'}|({'git_commit':v['rev']} if v['rev'] else {}) for k,v in raws().items() if k.startswith(duo) or k.startswith('secrete_') and duo=='secrete'}
  manifest={'id':'FD1_'+duo,'canonical_place':ref,'size':list(PLACES[duo]['size']),'grid':8,'maps':maps,'native':extra,'provenance':{'generations':prov,'native_bank':'pinned Red port via dungeon_biomes_v1/native_archive.py'},'method':'Generated planes keyed from magenta, NEAREST fit, quantized to the native palette of the place; native pixels flagged native_pixels=true are 1x unmodified crops (position may differ).','status':'technical checks only; not PMDO-run nor artistically approved'}
  files['manifest.json']=jb(manifest);files['README.md']=(S/'README.md').read_bytes()
  with zipfile.ZipFile(O/f'FD1_{duo}_duo_calques.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for name,b in sorted(files.items()):
    info=zipfile.ZipInfo(name,(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=9)
  result[duo]=(files,maps);print('Built',duo,len(files),'files',flush=True)
 return result

def verify():
 native_init();ok=[]
 for duo in PLACES:
  with zipfile.ZipFile(O/f'FD1_{duo}_duo_calques.zip') as z:
   assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json']);ref=PLACES[duo]['ref']
   assert img(files[f'references/FD1_{ref}_natif.png']).tobytes()==Image.fromarray(native(ref)[0]).tobytes()
   for rec in m['maps']:
    assert 4<=rec['semantic_groups']<=6;arr=[np.array(frame_of(files,l,0)) for l in rec['layers']];sol=arr[[l['id'] for l in rec['layers']].index('sol')]
    y0=96 if duo=='brulees' else 0;assert (sol[y0:,:,3]==255).all(),'continuous ground'
    for l,a in zip(rec['layers'],arr):
     assert a.shape[:2]==(rec['size'][1],rec['size'][0])
     if l['id'] not in ('sol','fond'):assert 0<(a[:,:,3]>0).sum()<a.shape[0]*a.shape[1]*0.8
     if not l['native_pixels'] and l['id']!='sol':
      cols=set(map(tuple,np.unique(a[a[:,:,3]>0][:,:3],axis=0)));assert cols<=set(map(tuple,native_colors(ref))),(duo,l['id'],'palette')
    obstacles=np.zeros(sol.shape[:2],bool)
    for l,a in zip(rec['layers'],arr):
     if l['id'] in ('arbres','feuillage','souche','rochers','troncs','vegetation','acces','lointain','accessoires'):obstacles|=a[:,:,3]>0
    free=(sol[:,:,3]>0)&~obstacles;safe=ndimage.binary_erosion(free,np.ones((17,17)));labels,_=ndimage.label(safe);h,w=sol.shape[:2];start=labels[h-16,w//2];assert start>0,(duo,rec['id'],'south arrival blocked')
    assert (labels==start).sum()>w*h*0.08,(duo,rec['id'],'walkable area')
    if rec['id']=='secrete_entree':assert labels[24,w//2]==start,'north corridor reachable'
    if duo=='brulees':
     for l in rec['layers']:
      if 'frames' in l:
       fr=[np.array(img(files[f])) for f in l['frames']];assert len({f.tobytes() for f in fr})==len(fr)
       nat=native(ref)[0];mask=fr[0][:,:,3]>0;assert np.array_equal(fr[0][mask],nat[mask]),'native frame0 pixels'
   ok.append(f'{duo}: manifest, native reference exact, 4-6 groups, opaque ground, palette continuity of generated planes, south arrival walkable')
  print('PASS',ok[-1],flush=True)
 (O/'verification.json').write_bytes(jb({'checks':ok,'runtime_PMDO':False}));return ok

def pmdo():
 """Serialize the six maps as PMDO Ground editing bases through the viewport_pmdo_v1 codec."""
 import importlib
 ns={'__file__':str(R/'source/viewport_pmdo_v1/build.py'),'__name__':'vp_tools'};VP=R/'source/viewport_pmdo_v1'
 exec(compile((VP/'build.py').read_bytes(),str(VP/'build.py'),'exec'),ns);exec(compile((VP/'verify.py').read_bytes(),str(VP/'verify.py'),'exec'),ns)
 ns['ST']=C/'pmdo_stage';ns['OUT']=O;ST=ns['ST']
 reports={}
 for duo in PLACES:
  with zipfile.ZipFile(O/f'FD1_{duo}_duo_calques.zip') as z:files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json'])
  dest=ST/duo
  if dest.exists():
   import shutil;shutil.rmtree(dest)
  metas=[];recs={}
  for rec in m['maps']:
   layers=[ns['layer'](l['title'],[img(files[f]) for f in l['frames']],l['frame_ticks']) if 'frames' in l else ns['layer'](l['title'],img(files[l['file']])) for l in rec['layers']]
   size=rec['size'];r={'id':'fd1_'+rec['id'],'duo':duo,'layers':layers,'spawn':[size[0]//2,size[1]-40],'offset':[0,-40],'notes':['FD1 base editable 1x; sol continu; collisions/warps a dessiner.'],'tick':0};recs[r['id']]=r;metas.append(ns['export_map'](r,None))
  manifest={'duo':duo,'lot':'FD1','maps':metas,'runtime_tested':False,'schema':'RogueEssence Ground + native8px TileBank','camera':{'screen':[320,240],'recommended_zoom':'x1'},'collisions':'ALL FREE editing scaffolds'}
  ns['save'](dest/'manifest.json',jb(manifest));ns['save'](dest/'README.md',(S/'README.md').read_bytes());ns['save'](dest/'INSTALLER.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes())
  # independent re-read of the serialized ground vs the composition
  for meta in metas:
   o=json.loads((dest/f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object'];r=recs[meta['id']]
   for tick in [0,64,97]:
    im=ns['serialized_scene'](dest,o,tick);exp=ns['render'](r,None,tick);diff=np.abs(np.array(im).astype(int)-np.array(exp).astype(int));assert diff.max()<=1 and np.array_equal(np.array(im)[:,:,3],np.array(exp)[:,:,3]),(meta['id'],tick,diff.max())
  import tempfile
  installer=ns['loadmod']('fd1_installer_'+duo,dest/'INSTALLER.py')
  with tempfile.TemporaryDirectory(dir=C) as td:
   mod=Path(td);(mod/'Mod.xml').write_text('<Mod><Namespace>fd1_test</Namespace></Mod>');installer.install(dest,mod,True,None);assert not (mod/'Data').exists();installer.install(dest,mod,False,None);installer.install(dest,mod,False,None)
   assert len(installer.read_index(mod/'Content/Tile/index.idx'))==len(list((dest/'Content/Tile').glob('*.tile')))
  path=O/f'FD1_{duo}_PMDO.zip'
  with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for p in sorted(dest.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:
     info=zipfile.ZipInfo(str(p.relative_to(dest)),(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
  reports[duo]=[m['asset'] for m in metas];print('PMDO PASS',duo,reports[duo],path.stat().st_size,flush=True)
 (O/'pmdo_verification.json').write_bytes(jb({'maps':reports,'checks':'serialisation re-read RGB<=1/alpha exact at ticks0,64,97; installer dry-run/install/reinstall; runtime_PMDO=false'}));return reports

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--pmdo',action='store_true');a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.pmdo:pmdo()
