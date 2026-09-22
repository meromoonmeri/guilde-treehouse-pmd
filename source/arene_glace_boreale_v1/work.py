"""IA2 — arène de glace canonique + aurore boréale canonique en frames verticales, multicalque.
Glace : pmdskyicearena.png (PMD Sky, 504x408) pixels 1x inchangés, découpés en arrière / sol continu / avant.
Aurore : rubans lumineux extraits de aurorepmdsky.png (méthode V10, sans ciel ni étoiles), 1x, animés par une
onde VERTICALE (cisaillement horizontal par ligne dont la phase descend), boucle exacte, chaque frame = calque.
Usage : .venv/bin/python source/arene_glace_boreale_v1/work.py --build --verify --pmdo
"""
from pathlib import Path
import io,json,hashlib,sys,zipfile,argparse,importlib.util,shutil,tempfile
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;C=R/'.cache/arene_glace_boreale_v1';O=C/'build'
ICE=R/'pmdskyicearena.png';AUR=R/'aurorepmdsky.png'
W,AH=504,408;SKY=96;GAP=96;H=SKY+AH+GAP;CUT=144;T=12;TICKS=6   # 12 frames x 6 ticks = 72 ticks = 1,2 s
SKY_RGB=(55,175,215);FLOOR_TOP=40   # le sol n existe pas derriere le ciel/la brume ; il commence sous la crete arriere
def sha(b):return hashlib.sha256(b).hexdigest()
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def img(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()

def ice_layers():
 a=np.array(Image.open(ICE).convert('RGBA'));assert a.shape==(AH,W,4)
 sky=np.all(a[:,:,:3]==SKY_RGB,axis=2);assert not sky[32:].any()
 # brume d horizon de jour (lignes 28-39, cyan clair peu detaille) : traitee comme ciel, alpha degressif
 haze=np.zeros(sky.shape,bool);haze[:40]=(a[:40,:,1].astype(int)>=183)&(a[:40,:,2].astype(int)<=239)&(a[:40,:,0]<=135);sky|=haze;sky[:32]=True
 AH2=AH+GAP;back=np.zeros((AH2,W,4),np.uint8);back[:248]=a[:248];back[:248][sky[:248]]=0
 floor_tile=a[248:280].copy();assert (floor_tile[:,:,3]==255).all()
 floor=np.zeros((AH2,W,4),np.uint8)
 for y in range(0,AH2,32):floor[y:y+32]=floor_tile[:min(32,AH2-y)]
 floor[:FLOOR_TOP]=0
 front=np.zeros((AH2,W,4),np.uint8);front[280+GAP:]=a[280:]
 return {'arriere':back,'sol':floor,'avant':front,'native':a,'sky_mask':sky}

def aurora_extract():
 """Rubans lumineux 1x de la texture canonique ; ciel sombre et étoiles exclus (règles V10, sans x2)."""
 ref=np.array(Image.open(AUR).convert('RGB')).astype(float);lum=ref.mean(axis=2);sat=ref.max(axis=2)-ref.min(axis=2)
 alpha=np.clip(np.clip((sat-75)*3.0,0,255)+np.clip((lum-105)*2.0,0,255),0,255)
 alpha[:CUT-10][alpha[:CUT-10]<34]=0;fondu=np.ones(ref.shape[0]);fondu[CUT-10:CUT]=np.linspace(1,0,10);fondu[CUT:]=0;alpha=alpha*fondu[:,None]
 lab,n=ndimage.label(alpha>0)
 if n:
  t=np.bincount(lab.ravel());t[0]=0;alpha[(t<6)[lab]]=0
  lab2,n2=ndimage.label(alpha>0)
  if n2:
   ms=ndimage.mean(sat,lab2,range(1,n2+1));sz=np.bincount(lab2.ravel());sz[0]=0;stars=np.array([k+1 for k in range(n2) if ms[k]<70 and sz[k+1]<40]);alpha[np.isin(lab2,stars)]=0
 core=(alpha>=100)&(sat>=70);d=ndimage.distance_transform_edt(~core);alpha[(alpha>=100)&(sat<50)&(d>10)]=0
 rgba=np.dstack([ref,alpha]).astype('uint8');rgba[rgba[:,:,3]==0]=0;rgba=rgba[:CUT]
 # étoiles : points clairs peu saturés hors rubans, pixels natifs
 star=((lum>150)&(sat<60)&(alpha==0))[:CUT];stars=np.zeros_like(rgba);full=np.dstack([ref,np.full(lum.shape,255)])[:CUT].astype('uint8');stars[star]=full[star]
 dark=(alpha==0);dark[:CUT]&=~star;rows=[]
 for y in range(CUT):
  px=ref[y][dark[y]];rows.append(np.median(px,axis=0) if len(px) else rows[-1])
 return rgba,stars,np.array(rows).astype('uint8')

def wide(tile):
 """Tuile native à gauche, copie MIROIR à droite (raccord central) ; adaptation explicite, pas native."""
 out=np.zeros((tile.shape[0],W,4),np.uint8);out[:,:264]=tile;out[:,264:]=tile[:,::-1][:,:W-264];return out

def shear(y,t):return 4.0*np.sin(2*np.pi*(1*y/CUT-t/T))+2.0*np.sin(2*np.pi*(3*y/CUT-t/T)+0.7)
def aurora_frame(base,t):
 out=np.zeros_like(base)
 for y in range(base.shape[0]):
  d=int(round(shear(y,t)));row=base[y]
  if d>0:out[y,d:]=row[:W-d]
  elif d<0:out[y,:W+d]=row[-d:]
  else:out[y]=row
 return out

def build():
 O.mkdir(parents=True,exist_ok=True);ice=ice_layers();rib,stars,skyrows=aurora_extract();files={}
 sky=np.zeros((H,W,4),np.uint8)
 for y in range(H):sky[y,:,:3]=skyrows[min(y,CUT-1)];sky[y,:,3]=255
 files['calques/IA2_00_ciel_nuit.png']=png(Image.fromarray(sky))
 st=np.zeros((H,W,4),np.uint8);st[:CUT]=wide(stars);files['calques/IA2_01_etoiles.png']=png(Image.fromarray(st))
 base=wide(rib);frames=[]
 for t in range(T):
  fr=np.zeros((H,W,4),np.uint8);fr[:CUT]=aurora_frame(base,t);frames.append(fr);files[f'aurore/IA2_aurore_{t:02d}.png']=png(Image.fromarray(fr))
 files['aurore/IA2_aurore_extrait_1x.png']=png(Image.fromarray(rib))
 for k,name in [('arriere','03_glace_arriere'),('sol','02_sol_glace_continu'),('avant','04_glace_avant')]:
  full=np.zeros((H,W,4),np.uint8);full[SKY:]=ice[k];files[f'calques/IA2_{name}.png']=png(Image.fromarray(full))
 order=['calques/IA2_00_ciel_nuit.png','calques/IA2_01_etoiles.png','AURORE','calques/IA2_02_sol_glace_continu.png','calques/IA2_03_glace_arriere.png','calques/IA2_04_glace_avant.png']
 def scene(t):
  im=Image.new('RGBA',(W,H))
  for o in order:im.alpha_composite(img(files[o]) if o!='AURORE' else Image.fromarray(frames[t%T]))
  return im
 scenes=[scene(t) for t in range(T)];files['apercus/IA2_arene.png']=png(scenes[0]);(O/'IA2_arene.png').write_bytes(files['apercus/IA2_arene.png'])
 rgb=[s.convert('RGB') for s in scenes];ms=[round((i+1)*TICKS*1000/60)-round(i*TICKS*1000/60) for i in range(T)];rgb[0].save(O/'IA2_arene_animee.webp',save_all=True,append_images=rgb[1:],duration=ms,loop=0,lossless=True,method=6)
 # planche des calques
 titles=['Ciel nuit (couleurs natives par ligne, champ reconstitue)','Etoiles natives 1x','Aurore canonique 1x - frame 0 (12 frames)','Sol de glace continu (lignes natives 248-279 repetees)','Glace arriere native 1x','Glace avant native 1x','Composition']
 panels=[img(files[o]) if o!='AURORE' else Image.fromarray(frames[0]) for o in order]+[scenes[0]]
 bw=W//2;bh=H//2;board=Image.new('RGB',(bw*4,(bh+28)*2),'#20242a');d=ImageDraw.Draw(board)
 for j,(tt,im) in enumerate(zip(titles,panels)):
  x=j%4*bw;y=j//4*(bh+28);d.text((x+6,y+7),tt[:60],fill='#e6e6dc');bg=Image.new('RGBA',(W,H),'#3a4048');bg.alpha_composite(im);board.paste(bg.convert('RGB').resize((bw,bh),Image.NEAREST),(x,y+28))
 (O/'IA2_calques.png').write_bytes(png(board));files['apercus/IA2_calques.png']=png(board)
 strip=Image.new('RGB',(264*6,CUT*2),'#000030')
 for t in range(T):
  fr=Image.fromarray(frames[t][:CUT,:264]);bg=Image.new('RGBA',(264,CUT),(0,0,63,255));bg.alpha_composite(fr);strip.paste(bg.convert('RGB'),((t%6)*264,(t//6)*CUT))
 (O/'IA2_aurore_12_frames.png').write_bytes(png(strip));files['apercus/IA2_aurore_12_frames.png']=png(strip)
 manifest={'id':'IA2','size':[W,H],'grid':8,'arena_offset':[0,SKY],'order':order,'aurora':{'frames':T,'frame_ticks':TICKS,'period_ticks':T*TICKS,'ms_per_frame':100,'source':'aurorepmdsky.png','source_sha256':sha(AUR.read_bytes()),'pixels':'rubans natifs 1x, extraction lum+sat (V10) sans x2 ; ciel/etoiles/nuages exclus','motion':'onde verticale : decalage horizontal par ligne d(y,t)=4sin(2pi(y/144-t/12))+2sin(2pi(3y/144-t/12)+0.7), phase descendante, boucle exacte frame12=frame0 ; cadence choisie, pas le cycle officiel','tiling':'tuile native x0-263 + copie miroir x264-503 (adaptation de raccord, non native)'},'ice':{'source':'pmdskyicearena.png','source_sha256':sha(ICE.read_bytes()),'pixels':'1x inchanges ; ciel de jour (55,175,215) et brume d horizon claire des lignes 28-39 retires ; arriere = lignes 0-247, sol = lignes 248-279 repetees sur toute la hauteur, avant = lignes 280-407 descendues de 96 px pour elargir l arene (adaptation de layout)','note':'glace de jour conservee telle quelle sous un ciel nocturne : choix de composition, pas une scene native'},'sky':'gradient nocturne reconstitue a partir des medianes natives par ligne (non ruban, non etoile) ; pas une image source inchangee','status':'tests images uniquement ; PMDO non execute ; pas d approbation artistique'}
 files['manifest.json']=jb(manifest);files['README.md']=(S/'README.md').read_bytes()
 with zipfile.ZipFile(O/'IA2_arene_glace_boreale_calques.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):
   info=zipfile.ZipInfo(n,(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=9)
 print('Built',len(files),'files');return files,frames

def verify():
 ice=ice_layers();rib,stars,_=aurora_extract()
 with zipfile.ZipFile(O/'IA2_arene_glace_boreale_calques.zip') as z:
  assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json'])
  nat=ice['native'];checks=[]
  for name,arr in [('calques/IA2_03_glace_arriere.png',ice['arriere']),('calques/IA2_04_glace_avant.png',ice['avant']),('calques/IA2_02_sol_glace_continu.png',ice['sol'])]:
   a=np.array(img(files[name]));assert a.shape==(H,W,4);assert np.array_equal(a[SKY:],arr)
   if 'arriere' in name:mask=a[SKY:SKY+248,:,3]>0;assert np.array_equal(a[SKY:SKY+248][mask],nat[:248][mask])
   if 'avant' in name:mask=a[SKY+280+GAP:,:,3]>0;assert np.array_equal(a[SKY+280+GAP:][mask],nat[280:][mask])
  sol=np.array(img(files['calques/IA2_02_sol_glace_continu.png']));assert (sol[SKY+FLOOR_TOP:,:,3]==255).all() and not sol[:SKY+FLOOR_TOP].any()
  for y in range(SKY+FLOOR_TOP,H):assert np.array_equal(sol[y],nat[248+(y-SKY)%32])
  checks.append('glace arriere/avant : pixels natifs 1x exacts, ciel de jour retire ; sol continu opaque = lignes natives 248-279 repetees')
  fr=[np.array(img(files[f'aurore/IA2_aurore_{t:02d}.png'])) for t in range(T)]
  assert len({f.tobytes() for f in fr})==T
  base=wide(rib);assert np.array_equal(aurora_frame(base,T),aurora_frame(base,0)),'boucle exacte'
  assert np.array_equal(fr[0][:CUT],aurora_frame(base,0))
  for f in fr:
   assert not f[CUT:].any()
   vis=f[:CUT,:264][f[:CUT,:264,:,3]>0] if False else None
  # les couleurs des frames sont un sous-ensemble des couleurs natives des rubans
  natcols=set(map(tuple,np.unique(rib[rib[:,:,3]>0][:,:3],axis=0)))
  for f in fr:cols=set(map(tuple,np.unique(f[f[:,:,3]>0][:,:3],axis=0)));assert cols<=natcols
  # onde verticale : les lignes bougent horizontalement, pas de translation de masse
  for t in range(T):
   s0=base[:,:,3]>0;st=fr[t][:CUT,:,3]>0;assert abs(int(s0.sum())-int(st.sum()))<s0.sum()*0.03
   cx0=np.where(s0.any(1),(s0*np.arange(W)).sum(1)/np.maximum(s0.sum(1),1),0);cxt=np.where(st.any(1),(st*np.arange(W)).sum(1)/np.maximum(st.sum(1),1),0);assert np.abs(cx0-cxt).max()<=7
  checks.append('aurore : 12 frames distinctes, couleurs natives seulement, boucle exacte, deplacement horizontal par ligne <=7px vs base non cisaillee (max theorique 6), alpha total stable')
  st=np.array(img(files['calques/IA2_01_etoiles.png']));assert (st[:,:,3]>0).sum()>10 and not st[CUT:].any()
  # compostion : sol visible entre les glaces, zone praticable
  obst=(np.array(img(files['calques/IA2_03_glace_arriere.png']))[:,:,3]>0)|(np.array(img(files['calques/IA2_04_glace_avant.png']))[:,:,3]>0);free=(sol[:,:,3]>0)&~obst;safe=ndimage.binary_erosion(free,np.ones((17,17)));lab,_=ndimage.label(safe);main=np.bincount(lab.ravel())[1:].argmax()+1;assert (lab==main).sum()>W*40
  checks.append('etoiles presentes au-dessus de 144 ; bande de sol libre continue entre glaces arriere/avant')
  with Image.open(O/'IA2_arene_animee.webp') as w:assert w.n_frames==T
 (O/'verification.json').write_bytes(jb({'checks':checks,'runtime_PMDO':False}));[print('PASS',c) for c in checks];return checks

def pmdo():
 ns={'__file__':str(R/'source/viewport_pmdo_v1/build.py'),'__name__':'vp_tools'};VP=R/'source/viewport_pmdo_v1'
 exec(compile((VP/'build.py').read_bytes(),str(VP/'build.py'),'exec'),ns);exec(compile((VP/'verify.py').read_bytes(),str(VP/'verify.py'),'exec'),ns)
 ns['ST']=C/'pmdo_stage';ns['OUT']=O;dest=ns['ST']/'arene'
 if dest.exists():shutil.rmtree(dest)
 with zipfile.ZipFile(O/'IA2_arene_glace_boreale_calques.zip') as z:files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json'])
 layers=[]
 for o in m['order']:
  if o=='AURORE':layers.append(ns['layer']('Aurore canonique 12x6 ticks',[img(files[f'aurore/IA2_aurore_{t:02d}.png']) for t in range(T)],TICKS))
  else:layers.append(ns['layer'](Path(o).stem,img(files[o])))
 rec={'id':'ia2_arene_glace_boreale','duo':'arene','layers':layers,'spawn':[W//2,SKY+300],'offset':[0,-48],'notes':['Arene glace canonique + aurore 12 frames sur calque anime ; collisions/warps a dessiner.'],'tick':0}
 meta=ns['export_map'](rec,None);o=json.loads((dest/f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object']
 for tick in [0,30,66,72]:
  im=ns['serialized_scene'](dest,o,tick);exp=ns['render'](rec,None,tick);diff=np.abs(np.array(im).astype(int)-np.array(exp).astype(int));assert diff.max()<=1 and np.array_equal(np.array(im)[:,:,3],np.array(exp)[:,:,3]),(tick,diff.max())
 ns['save'](dest/'manifest.json',jb({'lot':'IA2','maps':[meta],'runtime_tested':False,'camera':{'screen':[320,240],'recommended_zoom':'x1'},'collisions':'ALL FREE'}));ns['save'](dest/'README.md',(S/'README.md').read_bytes());ns['save'](dest/'INSTALLER.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes())
 installer=ns['loadmod']('ia2_installer',dest/'INSTALLER.py')
 with tempfile.TemporaryDirectory(dir=C) as td:
  mod=Path(td);(mod/'Mod.xml').write_text('<Mod><Namespace>ia2_test</Namespace></Mod>');installer.install(dest,mod,True,None);installer.install(dest,mod,False,None);installer.install(dest,mod,False,None)
 path=O/'IA2_arene_glace_boreale_PMDO.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(dest.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:
    info=zipfile.ZipInfo(str(p.relative_to(dest)),(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
 shutil.copy(dest/f'Apercus/{meta["asset"]}_viewport.png',O/'IA2_viewport_320x240.png');print('PMDO PASS',meta['asset'],path.stat().st_size)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--pmdo',action='store_true');a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.pmdo:pmdo()
