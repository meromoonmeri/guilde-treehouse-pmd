from pathlib import Path
import sys,json,math
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'source/tours_saisons_v1'));from common import *
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
O=R/'renders/tours_hooh_v1';S=O/'sprites';S.mkdir(exist_ok=True);yy,xx=np.mgrid[:H,:W]
def poly(points):
 im=Image.new('L',(W,H));ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0
# Authored distant panorama: stepped twilight sky and separate mountain silhouettes.
pal=np.array([[45,44,78],[101,70,109],[175,104,133],[230,157,144],[244,193,150]])
sky=np.zeros((H,W,4),dtype='uint8');sky[:,:,3]=255
for y in range(H):
 t=(y//4*4)/(H-1)*4
 for c in range(3):sky[y,:,c]=round(np.interp(t,np.arange(5),pal[:,c]))
background=[('01_ciel_crepusculaire',Image.fromarray(sky))]
for k,(height,color) in enumerate([(166,(127,108,146)),(218,(88,88,121)),(282,(51,70,91))]):
 rng=np.random.default_rng(110+k);xs=np.arange(-80,W+161,80);ys=height+rng.integers(-38,24,len(xs));im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im);pts=list(zip(map(int,xs),map(int,ys)))+[(W,H),(0,H)];d.polygon(pts,fill=(*color,255));mountain_alpha=np.array(im)[:,:,3]
 for i in range(1,len(xs)-1,3):
  x,y=int(xs[i]),int(ys[i]);shade=tuple(max(0,c-12) for c in color);d.polygon([(x,y),(x+105,H),(x+22,H),(x-12,y+18)],fill=(*shade,255))
 ar=np.array(im);ar[mountain_alpha==0]=0;im=Image.fromarray(ar);background.append((f'0{3+2*k}_montagnes_{k}',im))
# Only detached center cloud components are used; border-cut generated clouds are excluded.
raw=np.array(key(load(O/'bruts/nuages_crepuscule_magenta.png')));rh,rw=raw.shape[:2];clouds=[]
for k in range(3):
 a=raw[k*rh//3:(k+1)*rh//3];labs,num=nd.label(a[:,:,3]>0,np.ones((3,3)));objects=[]
 for lab,sl in enumerate(nd.find_objects(labs),1):
  sy,sx=sl
  if sx.start==0 or sx.stop==rw or np.count_nonzero(labs==lab)<150:continue
  objects.append((np.count_nonzero(labs==lab),lab,sl))
 objects.sort(reverse=True);assert len(objects)>=2
 tile=Image.new('RGBA',(W,H))
 for j,(_,lab,sl) in enumerate(objects[:2]):
  sy,sx=sl;arr=a[sy,sx].copy();arr[labs[sy,sx]!=lab]=0;im=Image.fromarray(arr);width=[186,160][j];height=max(12,round(im.height*width/im.width));im=im.resize((width,height),NN);tile.alpha_composite(im,([35,360][j]+k*38,[68,115,159][k]+j*26))
 name=f'0{2+2*k}_nuages_'+['lavande','rose','ambre'][k];clouds.append((name,tile));tile.save(S/f'{name}_wrap.png')
# Interleaved depth, then foreground architecture.
back_order=[background[0],clouds[0],background[1],clouds[1],background[2],clouds[2],background[3]]
for n,im in background:im.save(S/f'{n}.png')
entries=[]
for tower in ['carillon','cendree']:
 # Entrance: partition original generated pixels, reconstruct a hidden ground base for editing.
 a=np.array(load(O/'bruts'/f'{tower}_entree.png').resize((W,H),NN));r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 building=poly([(103,0),(537,0),(550,302),(498,343),(146,343),(96,300)])
 roof=building&(yy<205)&(b>r*1.12)&(b>g*.98);pillar=building&~roof&(r>g*1.35)&(b>g*.72)&(r<130)
 door=building&~(roof|pillar)&(xx>252)&(xx<390)&(yy>158);facade=building&~(roof|pillar|door)
 vegetation=~building&(((g>r*1.2)&(g<125))|((r>g*1.24)&(g<160)&(b<g*.75)));vegetation=nd.binary_closing(vegetation,iterations=1)&~building
 path=~(building|vegetation)&(xx>235)&(xx<405)&(yy>=300)
 hidden=building|vegetation|path;idx=nd.distance_transform_edt(hidden,return_distances=False,return_indices=True);ground=a.copy();ground[hidden]=a[idx[0][hidden],idx[1][hidden]]
 ls=[('01_sol',Image.fromarray(ground)),('02_parvis_chemin',cut(a,path)),('03_facade',cut(a,facade)),('04_porte_escalier',cut(a,door)),('05_poutres_rouge_fonce',cut(a,pillar)),('06_tuiles_toitures',cut(a,roof)),('07_vegetation_fond',cut(a,vegetation&(yy<300))),('08_vegetation_avant_gauche',cut(a,vegetation&(yy>=300)&(xx<320))),('09_vegetation_avant_droite',cut(a,vegetation&(yy>=300)&(xx>=320)))]
 assert np.array_equal(np.array(merge(ls)),a)
 for mode in ['jour','nuit']:export_static(O/f'{tower}_entree'/mode,f'th1_{tower}_entree_{mode}',[(n,night(im) if mode=='nuit' else im) for n,im in ls])
 entries.append(dict(id=f'{tower}_entree',layers=[n for n,im in ls],animated=[],size=[W,H],generated=True))
 # Boss foreground, keyed from generator; no generated magenta or fixed cloud backdrop retained.
 im=key(load(O/'bruts'/f'{tower}_boss_magenta.png')).resize((W,H),NN);a=np.array(im);opaque=a[:,:,3]>0;r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 if tower=='carillon':
  post_polys=[[(0,0),(42,0),(42,480),(0,480)],[(122,0),(163,0),(163,282),(122,282)],[(478,0),(518,0),(518,282),(478,282)],[(597,0),(640,0),(640,480),(597,480)]]
  floor=poly([(158,269),(478,269),(605,480),(35,480)])
 else:
  post_polys=[[(58,122),(98,128),(153,396),(113,396)],[(123,0),(164,0),(198,221),(159,221)],[(490,0),(529,0),(489,222),(449,222)],[(543,124),(583,127),(526,401),(482,393)]]
  floor=poly([(143,192),(496,192),(552,408),(425,480),(237,480),(78,389)])
 masks=[];used=np.zeros((H,W),bool)
 for i,pts in enumerate(post_polys):
  mask=poly(pts)&opaque&~used;used|=mask;masks.append((f'14_poutre_{i+1}',mask))
 roof=opaque&~used&(yy<155)&(b>r*1.08)&(b>g*.95);used|=roof;masks.append(('13_toiture_brisee',roof))
 floor&=opaque&~used;used|=floor;masks.append(('10_plancher_abime',floor))
 glass=opaque&~used&(r>80)&(g>45)&(b>45);used|=glass;masks += [('12_vitraux_gauche',glass&(xx<320)),('12_vitraux_droite',glass&(xx>=320))]
 rest=opaque&~used;masks += [('11_murs_gauche',rest&(xx<220)),('11_traverse_fond',rest&(xx>=220)&(xx<420)),('11_murs_droite',rest&(xx>=420))]
 foreground=[(n,cut(a,mask)) for n,mask in masks];assert np.array_equal(np.array(merge(foreground)),a)
 if tower=='carillon':
  # Repair the generated center-bottom gap with matching generated planks as an independent access layer.
  plank=im.crop((286,374,354,422));access=Image.new('RGBA',(W,H));access.alpha_composite(plank,(286,432));foreground.append(('15_acces_sud',access))
 # Put floor before the walls/pillars; disjoint extraction retains the original pixels.
 foreground.sort(key=lambda pair:pair[0]);order=[n for n,im in back_order+foreground]
 for mode in ['jour','nuit']:
  P=O/f'{tower}_boss'/mode;P.mkdir(parents=True,exist_ok=True);static={n:night(im) if mode=='nuit' else im for n,im in back_order+foreground};frames=[]
  for n,im in static.items():im.save(P/f'th1_{tower}_boss_{mode}_{n}.png')
  for phase in range(256):
   layers=[]
   for n,im in back_order:
    if 'nuages' in n:
     k=[x[0] for x in clouds].index(n);shift=round(phase*W/256*[1,-1,2][k]);current=Image.fromarray(np.roll(np.array(static[n]),shift,axis=1))
    else:current=static[n]
    layers.append((n,current))
   layers += [(n,static[n]) for n,im in foreground];comp=merge(layers);frames.append(comp)
   if phase==0:comp.save(P/'COMPOSITION.png');ora(P/f'th1_{tower}_boss_{mode}.ora',layers)
  frames[0].save(P/'BOUCLE_64S.webp',save_all=True,append_images=frames[1:],duration=250,lossless=True,loop=0,minimize_size=True,method=0,kmin=256,kmax=257)
  # Export each scrolling cloud plane independently with the same exact cycle.
  for k,(n,_) in enumerate(clouds):
   if tower!='carillon':continue
   C=O/'nuages_animes'/mode;C.mkdir(parents=True,exist_ok=True)
   arr=np.array(static[n]);ims=[Image.fromarray(np.roll(arr,round(p*W/256*[1,-1,2][k]),axis=1)) for p in range(256)];ims[0].save(C/f'th1_{mode}_{n}_BOUCLE.webp',save_all=True,append_images=ims[1:],duration=250,lossless=True,loop=0,minimize_size=True,method=0,kmin=256,kmax=257)
 entries.append(dict(id=f'{tower}_boss',size=[W,H],layers=order,animated=[n for n,im in clouds],loop_ms=64000,frames=256,frame_ms=250,period_px=W,multipliers=[1,-1,2],posts=4,generated_foreground=True,background='authored stepped sky and separate mountain silhouettes; generated detached cloud sprites',day_ambience='crepuscule',runtime_validated=False))
 print(tower,'entrance and boss exported')
(O/'manifest.json').write_text(json.dumps(entries,indent=2))
