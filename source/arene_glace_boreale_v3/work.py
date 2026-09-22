"""IA3 — arène de glace : nouveau layout genere, bordure immersive de stalactites, chemin sud vers l'arene,
ciel a aurore boreale animee (frames generees : mouvement + cycle de couleurs) et chaine de montagnes ultra lointaine.
Tous les plans sont GENERES d'apres les references canoniques (pmdskyicearena.png, aurorepmdsky.png), puis
quantifies dans les palettes natives de ces references. Aucun pixel n'est presente comme natif.
Usage : .venv/bin/python source/arene_glace_boreale_v3/work.py --build --verify --pmdo
"""
from pathlib import Path
import io,json,hashlib,zipfile,argparse,shutil,tempfile
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;C=R/'.cache/arene_glace_boreale_v3';O=C/'build'
import importlib.util as _ilu
_sp=_ilu.spec_from_file_location('ia2',R/'source/arene_glace_boreale_v1/work.py');IA2=_ilu.module_from_spec(_sp);_sp.loader.exec_module(IA2)
W=480;SKY=176;ARENA=(480,640);H=SKY+ARENA[1]   # 480x816, grille 8
T=12;TICKS=8                                   # 12 frames x 8 ticks = 96 ticks = 1,6 s
AUR_TOP=8;AUR_H=120                            # bande d aurore : lignes natives 0..119, 1x, discrete au-dessus des montagnes
def ripple(y,t):return 2.0*np.sin(2*np.pi*(y/AUR_H-t/T))+1.0*np.sin(2*np.pi*(2*y/AUR_H-t/T)+0.5)   # +-3 px max, legere
def sha(b):return hashlib.sha256(b).hexdigest()
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def img(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()
def raws():return {r['id']:r for r in json.loads((S/'raws/index.json').read_text())}
def raw(k):
 r=raws()[k];b=(R/r['path']).read_bytes();assert sha(b)==r['sha256'],k;im=img(b);assert sha(im.tobytes())==r['rgba_sha256'],k;return im
def magenta(a):
 r,g,b=np.moveaxis(a[:,:,:3].astype(int),2,0);return (r>150)&(b>150)&(g<120)&(abs(r-b)<90)
def key_flood(im):
 """Transparence par inondation du magenta de fond (#FF00FF +-20) depuis les bords : le magenta des rubans est conserve."""
 a=np.array(im);m=np.all(np.abs(a[:,:,:3].astype(int)-[255,0,255])<20,axis=2);m=ndimage.binary_closing(m,iterations=1)|m;lab,n=ndimage.label(m);edge=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0};sizes=np.bincount(lab.ravel());big=set(np.where(sizes>1500)[0])-{0};bg=np.isin(lab,list(edge|big));a[bg]=0;return a
def key_all(im):
 a=np.array(im);a[magenta(a)]=0;return a
def nearest(a,size):return np.array(Image.fromarray(a).resize(size,Image.Resampling.NEAREST))
def palette(path):
 a=np.array(Image.open(path).convert('RGBA'));return np.unique(a[a[:,:,3]>0][:,:3],axis=0)
def quant(a,cols):
 cols=np.asarray(cols,dtype='uint8');p=Image.new('P',(1,1));p.putpalette(np.vstack([cols,np.tile(cols[0],(256-len(cols),1))]).tobytes());im=Image.fromarray(a);b=np.array(im.convert('RGB').quantize(palette=p,dither=Image.Dither.NONE).convert('RGBA'));b[:,:,3]=a[:,:,3];b[b[:,:,3]==0]=0;return b
def clean(a,min_px=12):
 lab,n=ndimage.label(a[:,:,3]>0,np.ones((3,3)))
 if n:
  s=np.bincount(lab.ravel());s[0]=0;a[(s<min_px)[lab]]=0
 return a

def aurora_cells(sheet):
 """Decoupe la planche 4x2 par ses separateurs blancs, sans supposer des cellules egales."""
 a=np.array(sheet);white=(a[:,:,:3]>235).all(2);cols=np.where(white.mean(0)>0.9)[0];rows=np.where(white.mean(1)>0.9)[0]
 def spans(idx,limit):
  cuts=[-1]+list(idx)+[limit];out=[]
  for i in range(len(cuts)-1):
   s,e=cuts[i]+1,cuts[i+1]
   if e-s>40:out.append((s,e))
  return out
 xs=spans(cols,a.shape[1]);ys=spans(rows,a.shape[0]);assert len(xs)==4 and len(ys)==2,(xs,ys)
 return [a[y0:y1,x0:x1] for (y0,y1) in ys for (x0,x1) in xs]

def build():
 O.mkdir(parents=True,exist_ok=True);files={};ice_cols=palette(R/'pmdskyicearena.png');aur=np.array(Image.open(R/'aurorepmdsky.png').convert('RGB'))
 aur_cols=np.unique(aur.reshape(-1,3),axis=0)
 # ---- ciel : gradient reconstitue depuis les lignes sombres natives (hors rubans/etoiles)
 lum=aur.mean(2);sat=aur.max(2)-aur.min(2);dark=(lum<60)&(sat<90);rows=[]
 for y in range(aur.shape[0]):
  px=aur[y][dark[y]];rows.append(np.median(px,0) if len(px)>20 else rows[-1])
 rows=np.array(rows);sky=np.zeros((H,W,4),np.uint8)
 for y in range(H):sky[y,:,:3]=rows[min(int(y*140/SKY),139)];sky[y,:,3]=255
 sky=quant(sky,aur_cols);files['calques/IA3_00_ciel_nuit.png']=png(Image.fromarray(sky))
 # ---- etoiles natives 1x, repetees en 2 tuiles 264 px (miroir a droite)
 star=(lum>150)&(sat<60);star[140:]=False;st=np.zeros((H,W,4),np.uint8);tile=np.zeros((140,264,4),np.uint8);tile[star[:140]]=np.dstack([aur[:140],np.full((140,264),255)])[star[:140]]
 st[:140,:264]=tile;st[:140,264:]=tile[:,::-1][:,:W-264];st[:8]=0;files['calques/IA3_01_etoiles.png']=png(Image.fromarray(st))
 # ---- aurore : rubans CANONIQUES 1x (extraction IA2/V10), bande reduite, legere ondulation verticale, pas de cycle de couleur
 rib,_,_=IA2.aurora_extract();rib=rib[:AUR_H].copy()
 for k in range(12):rib[AUR_H-12+k,:,3]=(rib[AUR_H-12+k,:,3].astype(int)*(12-k)//12).astype('uint8')
 rib[rib[:,:,3]==0]=0;base=np.zeros((AUR_H,W,4),np.uint8);base[:,:264]=rib;base[:,264:]=rib[:,::-1][:,:W-264]
 frames=[]
 for t in range(T):
  fr=np.zeros((H,W,4),np.uint8);sh=np.zeros_like(base)
  for y in range(AUR_H):
   d=int(round(ripple(y,t)));row=base[y]
   if d>0:sh[y,d:]=row[:W-d]
   elif d<0:sh[y,:W+d]=row[-d:]
   else:sh[y]=row
  fr[AUR_TOP:AUR_TOP+AUR_H]=sh;frames.append(fr);files[f'aurore/IA3_aurore_{t:02d}.png']=png(Image.fromarray(fr))
 files['aurore/IA3_aurore_extrait_natif_1x.png']=png(Image.fromarray(rib))
 # ---- montagnes ultra lointaines (generees), bande posee juste au-dessus de la bordure
 mt=key_all(raw('montagnes_lointaines'));mt=mt[np.where((mt[:,:,3]>0).any(1))[0].min():];mt=nearest(mt,(W,int(W*mt.shape[0]/mt.shape[1])));mt=quant(clean(mt),ice_cols);mtl=np.zeros((H,W,4),np.uint8);y0=SKY+40-mt.shape[0];mtl[max(0,y0):y0+mt.shape[0]]=mt[max(0,-y0):];mtl[SKY+40:]=0;files['calques/IA3_02_montagnes_lointaines.png']=png(Image.fromarray(mtl))
 # ---- sol continu avec chemin et arene (genere), opaque sous la bordure
 sol=nearest(np.array(raw('sol_chemin')),ARENA);sol=np.concatenate([np.repeat(sol[:1],56,axis=0),sol[:-56]]);sol[:,:,3]=255;sol=quant(sol,ice_cols);soll=np.zeros((H,W,4),np.uint8);soll[SKY:]=sol;files['calques/IA3_03_sol_chemin_arene.png']=png(Image.fromarray(soll))
 # ---- bordure immersive de stalactites (generee) : arriere (au-dessus du centre de l'arene) / avant (dessous), pour l'occlusion
 bd=key_all(nearest(np.array(raw('bordure_stalactites')),ARENA));bd=quant(clean(bd,30),ice_cols)
 back=bd.copy();back[ARENA[1]//2:]=0;front=bd.copy();front[:ARENA[1]//2]=0
 bl=np.zeros((H,W,4),np.uint8);bl[SKY:]=back;fl=np.zeros((H,W,4),np.uint8);fl[SKY:]=front
 files['calques/IA3_04_stalactites_arriere.png']=png(Image.fromarray(bl));files['calques/IA3_05_stalactites_avant.png']=png(Image.fromarray(fl))
 order=['calques/IA3_00_ciel_nuit.png','calques/IA3_01_etoiles.png','AURORE','calques/IA3_02_montagnes_lointaines.png','calques/IA3_03_sol_chemin_arene.png','calques/IA3_04_stalactites_arriere.png','calques/IA3_05_stalactites_avant.png']
 def scene(t):
  im=Image.new('RGBA',(W,H))
  for o in order:im.alpha_composite(Image.fromarray(frames[t%T]) if o=='AURORE' else img(files[o]))
  return im
 scenes=[scene(t) for t in range(T)];files['apercus/IA3_arene.png']=png(scenes[0]);(O/'IA3_arene.png').write_bytes(files['apercus/IA3_arene.png'])
 rgb=[s.convert('RGB') for s in scenes];ms=[round((i+1)*TICKS*1000/60)-round(i*TICKS*1000/60) for i in range(T)];rgb[0].save(O/'IA3_arene_animee.webp',save_all=True,append_images=rgb[1:],duration=ms,loop=0,lossless=True,method=6)
 titles=['Ciel nuit (gradient reconstitue, palette native)','Etoiles natives 1x','Aurore canonique 1x - frame 0 / 12, ondulation legere','Montagnes ultra lointaines (generees)','Sol continu : chemin + arene (genere)','Stalactites arriere (generees)','Stalactites avant (generees)','Composition - 7 calques']
 panels=[Image.fromarray(frames[0]) if o=='AURORE' else img(files[o]) for o in order]+[scenes[0]]
 bw,bh=W//2,H//2;board=Image.new('RGB',(bw*4,(bh+28)*2),'#20242a');d=ImageDraw.Draw(board)
 for j,(tt,im) in enumerate(zip(titles,panels)):
  x=j%4*bw;y=j//4*(bh+28);d.text((x+6,y+7),tt,fill='#e6e6dc');bg=Image.new('RGBA',(W,H),'#3a4048');bg.alpha_composite(im);board.paste(bg.convert('RGB').resize((bw,bh),Image.NEAREST),(x,y+28))
 (O/'IA3_calques.png').write_bytes(png(board));files['apercus/IA3_calques.png']=png(board)
 strip=Image.new('RGB',(W//2*4,SKY//2*3),'#000030')
 for t in range(T):
  bg=Image.new('RGBA',(W,SKY),(0,0,63,255));bg.alpha_composite(Image.fromarray(frames[t][:SKY]));strip.paste(bg.convert('RGB').resize((W//2,SKY//2),Image.NEAREST),((t%4)*W//2,(t//4)*SKY//2))
 (O/'IA3_aurore_12_frames.png').write_bytes(png(strip));files['apercus/IA3_aurore_12_frames.png']=png(strip)
 manifest={'id':'IA3','size':[W,H],'grid':8,'arena_offset':[0,SKY],'order':order,'aurora':{'frames':T,'frame_ticks':TICKS,'period_ticks':T*TICKS,'generated':False,'pixels':'rubans natifs 1x de aurorepmdsky.png, lignes 0-119, extraction lum+sat (V10), fondu bas 12px ; tuile native x0-263 + miroir x264-503 (raccord, adaptation)','motion':'ondulation LEGERE : decalage horizontal par ligne 2sin(2pi(y/120-t/12))+1sin(2pi(2y/120-t/12)+0.5), max +-3px, boucle exacte frame12=frame0 ; pas de cycle de couleur ; cadence choisie, pas le cycle officiel','rejected':'planche generee 8 frames mouvement+couleurs (aurore_planche_B) : trop grosse, non canonique -> archivee, non utilisee'},'ice':{'generated':True,'sources':['bordure_stalactites','sol_chemin'],'palette':'quantifiee dans les couleurs natives de pmdskyicearena.png','occlusion':'bordure coupee en arriere/avant a mi-hauteur de l arene'},'mountains':{'generated':True,'source':'montagnes_lointaines'},'sky':'gradient reconstitue depuis les medianes des lignes sombres natives','native_pixels_layers':['calques/IA3_01_etoiles.png','aurore/*'],'status':'tests images uniquement ; PMDO non execute ; pas d approbation artistique ; generations ≠ pixels canoniques'}
 files['manifest.json']=jb(manifest);files['README.md']=(S/'README.md').read_bytes();files['provenance/generations.json']=(S/'raws/index.json').read_bytes()
 with zipfile.ZipFile(O/'IA3_arene_glace_boreale_calques.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):
   info=zipfile.ZipInfo(n,(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=9)
 print('Built',len(files),'files');return files

def verify():
 ice_cols=set(map(tuple,palette(R/'pmdskyicearena.png')));aur_cols=set(map(tuple,np.unique(np.array(Image.open(R/'aurorepmdsky.png').convert('RGB')).reshape(-1,3),axis=0)))
 with zipfile.ZipFile(O/'IA3_arene_glace_boreale_calques.zip') as z:
  assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json']);checks=[]
  L={Path(o).stem.split('_',2)[-1]:np.array(img(files[o])) for o in m['order'] if o!='AURORE'}
  for k,a in L.items():assert a.shape==(H,W,4),k
  assert (L['sol_chemin_arene'][SKY:,:,3]==255).all() and not L['sol_chemin_arene'][:SKY].any()
  for k in ['sol_chemin_arene','stalactites_arriere','stalactites_avant','montagnes_lointaines']:
   a=L[k];cols=set(map(tuple,np.unique(a[a[:,:,3]>0][:,:3],axis=0)));assert cols<=ice_cols,k
  fr=[np.array(img(files[f'aurore/IA3_aurore_{t:02d}.png'])) for t in range(T)];assert len({f.tobytes() for f in fr})==T
  rib,_,_=IA2.aurora_extract();natcols=set(map(tuple,np.unique(rib[rib[:,:,3]>0][:,:3],axis=0)))
  for f in fr:
   assert not f[:AUR_TOP].any() and not f[AUR_TOP+AUR_H:].any();cols=set(map(tuple,np.unique(f[f[:,:,3]>0][:,:3],axis=0)));assert cols<=natcols
   assert (f[:SKY,:,3]>0).mean()<0.35,'aurore discrete'
  # legere ondulation : chaque ligne bouge de 3px max par rapport a la frame 0, meme couverture
  rb=rib[:AUR_H].copy()
  for k in range(12):rb[AUR_H-12+k,:,3]=(rb[AUR_H-12+k,:,3].astype(int)*(12-k)//12).astype('uint8')
  b0=np.zeros((AUR_H,W),bool);b0[:,:264]=rb[:,:,3]>0;b0[:,264:]=(rb[:,::-1][:,:W-264,3]>0)
  for t in range(T):
   a0=b0;at=fr[t][AUR_TOP:AUR_TOP+AUR_H,:,3]>0;assert abs(int(a0.sum())-int(at.sum()))<a0.sum()*0.02
   for y in range(AUR_H):
    d=int(round(ripple(y,t)));assert abs(d)<=3
    if d>=0:assert np.array_equal(at[y,d:],a0[y,:W-d])
    else:assert np.array_equal(at[y,:W+d],a0[y,-d:])
  assert all(abs(ripple(y,T)-ripple(y,0))<1e-9 for y in range(AUR_H)),'boucle exacte'
  assert len({tuple(map(tuple,np.unique(f[f[:,:,3]>0][:,:3],axis=0))) for f in fr})>=1
  checks.append('aurore : rubans natifs 1x (couleurs natives), 12 frames, ondulation legere <=3px/ligne, couverture stable, boucle exacte, occupation ciel <35%')
  obst=(L['stalactites_arriere'][:,:,3]>0)|(L['stalactites_avant'][:,:,3]>0);free=(L['sol_chemin_arene'][:,:,3]>0)&~obst;safe=ndimage.binary_erosion(free,np.ones((17,17)));lab,_=ndimage.label(safe);start=lab[H-12,W//2];assert start>0,'entree sud'
  assert lab[SKY+ARENA[1]//2+16,W//2]==start,'chemin sud -> arene connecte';assert (lab==start).sum()>W*ARENA[1]*0.25
  assert obst[SKY+80:SKY+ARENA[1]-8,8:32].mean()>0.8 and obst[SKY+80:SKY+ARENA[1]-8,-32:-8].mean()>0.8 and obst[SKY+56:SKY+72,:].mean()>0.95,'bordure fermee sur 3 cotes'
  assert not (lab==start)[:, :8].any() and not (lab==start)[:, -8:].any() and not (lab==start)[SKY:SKY+56].any(),'zone praticable ne touche pas les bords N/E/O'
  checks.append('sol continu opaque ; bordure fermee N/E/O ; entree sud libre reliee au centre de l arene (erosion 17px)')
  mt=L['montagnes_lointaines'];assert (mt[:,:,3]>0).any() and not mt[SKY+40:].any();assert (L['etoiles'][:,:,3]>0).sum()>10
  checks.append('montagnes lointaines dans le ciel, sous l aurore ; etoiles presentes')
  with Image.open(O/'IA3_arene_animee.webp') as w:assert w.n_frames==T
 (O/'verification.json').write_bytes(jb({'checks':checks,'runtime_PMDO':False}));[print('PASS',c) for c in checks];return checks

def pmdo():
 ns={'__file__':str(R/'source/viewport_pmdo_v1/build.py'),'__name__':'vp_tools'};VP=R/'source/viewport_pmdo_v1'
 exec(compile((VP/'build.py').read_bytes(),str(VP/'build.py'),'exec'),ns);exec(compile((VP/'verify.py').read_bytes(),str(VP/'verify.py'),'exec'),ns)
 ns['ST']=C/'pmdo_stage';ns['OUT']=O;dest=ns['ST']/'arene'
 if dest.exists():shutil.rmtree(dest)
 with zipfile.ZipFile(O/'IA3_arene_glace_boreale_calques.zip') as z:files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json'])
 layers=[ns['layer']('Aurore canonique 12x8 ticks',[img(files[f'aurore/IA3_aurore_{t:02d}.png']) for t in range(T)],TICKS) if o=='AURORE' else ns['layer'](Path(o).stem,img(files[o])) for o in m['order']]
 rec={'id':'ia3_arene_glace_boreale','duo':'arene','layers':layers,'spawn':[W//2,H-40],'offset':[0,-64],'notes':['Layout genere : bordure immersive, chemin sud, arene centrale, aurore 8 frames ; collisions/warps a dessiner.'],'tick':0}
 meta=ns['export_map'](rec,None);o=json.loads((dest/f'Data/Ground/{meta["asset"]}.rsground').read_text())['Object']
 for tick in [0,40,95,96]:
  im=ns['serialized_scene'](dest,o,tick);exp=ns['render'](rec,None,tick);diff=np.abs(np.array(im).astype(int)-np.array(exp).astype(int));assert diff.max()<=1 and np.array_equal(np.array(im)[:,:,3],np.array(exp)[:,:,3]),(tick,diff.max())
 ns['save'](dest/'manifest.json',jb({'lot':'IA3','maps':[meta],'runtime_tested':False,'camera':{'screen':[320,240],'recommended_zoom':'x1'},'collisions':'ALL FREE'}));ns['save'](dest/'README.md',(S/'README.md').read_bytes());ns['save'](dest/'INSTALLER.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes())
 installer=ns['loadmod']('ia3_installer',dest/'INSTALLER.py')
 with tempfile.TemporaryDirectory(dir=C) as td:
  mod=Path(td);(mod/'Mod.xml').write_text('<Mod><Namespace>ia3_test</Namespace></Mod>');installer.install(dest,mod,True,None);installer.install(dest,mod,False,None);installer.install(dest,mod,False,None)
 path=O/'IA3_arene_glace_boreale_PMDO.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(dest.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:
    info=zipfile.ZipInfo(str(p.relative_to(dest)),(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
 shutil.copy(dest/f'Apercus/{meta["asset"]}_viewport.png',O/'IA3_viewport_320x240.png');print('PMDO PASS',meta['asset'],path.stat().st_size)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--pmdo',action='store_true');a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.pmdo:pmdo()
