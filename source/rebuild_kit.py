from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageFont
from scipy.ndimage import binary_fill_holes
from zipfile import ZipFile
import numpy as np,cv2,math,json,struct,zlib,io,os
D=Path(__file__).resolve().parents[1];R=D;ROOT=D.parent
OUT=D;OUT.mkdir(exist_ok=True)
for x in ['salles','calques','fenetres_exterieur','exterieur','sprites','apercus','source','tiled']:(OUT/x).mkdir(exist_ok=True)
OLD=json.loads((R/'source/base_kit.json').read_text());BY={r['id']:r for r in OLD['salles']}
RULES=json.loads((D/'source/regles_acces.json').read_text())
BASE={'01':'01','02':'02','03':'03','04':'04','05':'05','06':'06','07':'05','08':'08','09':'09','10':'08','11':'05','12':'12'}
MIRROR={'07','10','11'};MODES=['jour','nuit','crepuscule','aube','soir','orageux']
LABELS=[('00_exterieur','Paysage extérieur interchangeable'),('01_sol','Sol et continuité des passages'),('02_structure','Structure, murs et ouvertures'),('03_cadres_fenetres','Cadres de fenêtres — sans paysage'),('04_tableaux','Contenu des tableaux encastrés'),('05_porte_maitre','Porte nord du bureau — hall uniquement'),('06_decorations','Décorations — vide'),('07_objets','Objets — vide'),('08_ombres_acces','Ombres de contact des accès'),('09_eclairage_fixe','Éclairage complémentaire — vide'),('10_bordure_avant','Bordure avant interrompue aux passages')]

def png(im,path):
 a=np.array(im.convert('RGBA'));colors,idx=np.unique(a.reshape(-1,4),axis=0,return_inverse=True)
 if len(colors)<=256:
  q=Image.fromarray(idx.reshape(a.shape[:2]).astype('uint8'),'P');pal=np.zeros((256,3),np.uint8);pal[:len(colors)]=colors[:,:3];q.putpalette(pal.ravel());q.info['transparency']=bytes(colors[:,3]);q.save(path,optimize=True)
 else:im.save(path,optimize=True)
def night(im):
 a=np.array(im.convert('RGBA'));a[:,:,:3]=np.rint(a[:,:,:3]*[.36,.34,.43]+[9,10,19]).clip(0,255).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a,'RGBA')
def key(im):
 a=np.array(im.convert('RGBA'));r,g,b=[a[:,:,i].astype(int) for i in range(3)];m=(r-g>65)&(b-g>50)&(r>125)&(b>100);near=cv2.dilate(m.astype('uint8'),np.ones((3,3),np.uint8))>0;m|=near&(r-g>25)&(b-g>12)&(b>r*.42);a[m]=0;return Image.fromarray(a,'RGBA')
def cut(im,m):a=np.array(im);a[~m]=0;return Image.fromarray(a,'RGBA')
def astr(s):b=s.encode();return struct.pack('<H',len(b))+b
def chunk(k,d):return struct.pack('<IH',len(d)+6,k)+d
def ase(path,layers,size):
 w,h=size;chunks=[]
 for n,im in layers:chunks.append(chunk(0x2004,struct.pack('<HHHHHHB',3,0,0,0,0,0,255)+b'\0'*3+astr(n)))
 for i,(n,im) in enumerate(layers):
  box=im.getbbox()
  if box:x,y,_,_=box;q=im.crop(box)
  else:x=y=0;q=Image.new('RGBA',(1,1))
  chunks.append(chunk(0x2005,struct.pack('<HhhBHh',i,x,y,255,2,0)+b'\0'*5+struct.pack('<HH',q.width,q.height)+zlib.compress(q.tobytes(),9)))
 data=b''.join(chunks);frame=struct.pack('<IHHH2sI',len(data)+16,0xF1FA,len(chunks),100,b'\0\0',len(chunks))+data
 header=bytearray(128);struct.pack_into('<IHHHHHIH',header,0,len(frame)+128,0xA5E0,1,w,h,32,1,100);struct.pack_into('<HBBhhHH',header,32,0,1,1,0,0,8,8);path.write_bytes(header+frame)
def font(size):
 try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
 except OSError:return ImageFont.load_default()

# Only one real closed door is permitted. Its four-wing identity is an independent retained asset.
logo=Image.open(D/'source/embleme_4_ailes.png').convert('RGBA')
manifest={'titre':'Guilde Treehouse — passages ouverts PMD','grille_px':8,'animation':False,'ambiances':MODES,'regles_acces':RULES,'calques':[{'id':i,'nom':n} for i,n in LABELS],'salles':[]}
for mode in MODES:
 im=Image.open(D/'exterieur'/f'{mode}.png').convert('RGBA');png(im,OUT/'exterieur'/f'{mode}.png')
FILTER=set(filter(None,os.environ.get('GUILDE_ROOMS','').split(',')))
for rid,info in BY.items():
 if FILTER and rid not in FILTER:continue
 im=key(Image.open(D/'source/natives'/f'{BASE[rid]}.png'))
 if rid in MIRROR:im=ImageOps.mirror(im)
 w,h=im.size;a=np.array(im);alpha=a[:,:,3]>0;yy,xx=np.indices((h,w))
 # Small matte-color leftovers are cleaned before any layering.
 # Restore exactly four wings on the one exceptional northern door.
 door=np.zeros((h,w),bool);doorbox=None
 if rid=='02':
  rr,gg,bb=[a[:,:,i].astype(int) for i in range(3)];seed=(gg>rr+5)&(gg>bb*1.35)&(xx>w*.68)&(yy<h*.48)&alpha
  ys,xs=np.where(seed)
  if len(xs):
   bx0,bx1=int(xs.min()),int(xs.max()+1);by0,by1=int(ys.min()),int(ys.max()+1);cx=(bx0+bx1)//2
   # Replace the tiny generator emblem, not the room or door design.
   gx0,gx1=cx-21,cx+22;gy0,gy1=max(0,by0-29),max(1,by0-8)
   mask=np.zeros((h,w),np.uint8);mask[gy0:gy1,gx0:gx1]=255
   rgb=cv2.inpaint(a[:,:,:3].copy(),mask,3,cv2.INPAINT_TELEA);a[mask>0,:3]=rgb[mask>0]
   li=logo.resize((32,28),Image.Resampling.NEAREST);la=np.array(li);lm=(la[:,:,3]>0);ox=cx-16;oy=max(0,by0-32)
   patch=a[oy:oy+28,ox:ox+32];patch[lm,:3]=np.rint(patch[lm,:3]*.30+np.array([191,145,65])*.70).astype('uint8')
   im=Image.fromarray(a,'RGBA');doorbox=[max(0,bx0-15),max(0,by0-39),min(w,bx1+15),min(h,by1+12)]
   dx0,dy0,dx1,dy1=doorbox;dm=Image.new('L',(w,h));ImageDraw.Draw(dm).rounded_rectangle(doorbox,radius=12,fill=255);door=(np.array(dm)>0)&alpha
 # Every enclosed magenta pane is a true aperture, not a scene baked in a window sprite.
 holes=binary_fill_holes(alpha)&~alpha
 nc,lab,stats,cent=cv2.connectedComponentsWithStats(holes.astype('uint8'),8);hole=np.zeros((h,w),bool)
 for k in range(1,nc):
  if stats[k,cv2.CC_STAT_AREA]>=12:hole|=lab==k
 # Frame modules are the surrounding wood, including mullions between panes.
 joined=cv2.dilate(hole.astype('uint8'),np.ones((15,15),np.uint8));nc,lab,stats,cent=cv2.connectedComponentsWithStats(joined,8)
 win=np.zeros((h,w),bool);windows=[]
 for k in range(1,nc):
  hh=(lab==k)&hole
  if hh.sum()<15:continue
  points=cv2.findNonZero(hh.astype('uint8'));hull=cv2.convexHull(points);wm=np.zeros((h,w),np.uint8);cv2.fillConvexPoly(wm,hull,1);wm=cv2.dilate(wm,np.ones((13,13),np.uint8))>0;wm&=alpha;wm&=~door
  win|=wm;ys,xs=np.where(wm)
  if len(xs):windows.append([int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)])
 # Editable notice content. Carved niche frames remain architectural.
 panels=np.zeros((h,w),bool)
 if rid=='02':
  for x0,y0,x1,y1 in [(int(w*.29),int(h*.182),int(w*.405),int(h*.322)),(int(w*.61),int(h*.182),int(w*.724),int(h*.322))]:panels[y0:y1,x0:x1]=True
  panels&=alpha;panels&=~door
 # The low room floor is segmented in its own layer, with cardinal continuations included.
 cx=w*.5;cy=h*(.60 if rid=='02' else .625);rx=w*.443;ry=h*.211
 ell=((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
 gc=np.zeros((h,w),np.uint8);gc[alpha]=cv2.GC_PR_BGD;gc[ell&alpha]=cv2.GC_PR_FGD
 seed=(np.abs(xx-cx)<rx*.56)&(np.abs(yy-cy)<ry*.38)&alpha;gc[seed]=cv2.GC_FGD;gc[win|door|panels]=cv2.GC_BGD
 try:
  cv2.grabCut(a[:,:,:3],gc,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK);floor=((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD))&alpha
 except cv2.error:floor=ell&alpha
 routes=RULES['passages'][rid]
 if rid in {'01','09'}:
  top=np.where(alpha[0])[0]
  if len(top):
   x0,x1=int(top.min()+5),int(top.max()-4);pm=Image.new('L',(w,h));ImageDraw.Draw(pm).polygon([(x0,0),(x1,0),(cx+w*.075,h*.45),(cx-w*.075,h*.45)],fill=255);floor|=(np.array(pm)>0)&alpha
 for direc,side in [('E',w-1),('O',0)]:
  if direc in routes:
   ys=np.where(alpha[:,side])[0]
   if len(ys):floor|=alpha&(yy>=ys.min()+3)&(yy<=ys.max()-3)&((xx>w*.81) if direc=='E' else (xx<w*.19))
 floor&=~win&~door&~panels
 front=alpha&~floor&~win&~door&~panels&(yy>h*.705)
 if 'S' in routes:front&=~((np.abs(xx-cx)<w*.11)&(yy>h*.78))
 walls=alpha&~floor&~win&~door&~panels&~front
 # Independent static contact-shade plane. Algebraic decomposition preserves the generated result.
 region=np.zeros((h,w),bool)
 if 'S' in routes:region|=(np.abs(xx-cx)<w*.14)&(yy>h*.75)
 if 'N' in routes:region|=(np.abs(xx-cx)<w*.14)&(yy<h*.47)
 if 'E' in routes:region|=(xx>w*.80)&(yy>h*.43)&(yy<h*.79)
 if 'O' in routes:region|=(xx<w*.20)&(yy>h*.43)&(yy<h*.79)
 if rid=='02':region|=(np.abs(xx-cx)<w*.055)&(yy>h*.32)&(yy<h*.47)
 lum=.2126*a[:,:,0]+.7152*a[:,:,1]+.0722*a[:,:,2]
 sh=np.rint(np.clip((153-lum)/190,0,.32)*255).astype('uint8');sh[~(region&alpha&~win&~door&~panels)]=0
 sh=np.minimum(sh,255-a[:,:,:3].max(2));sh[sh<6]=0;sh[front]=0
 unsh=a.copy();denom=255-sh.astype(float);unsh[:,:,:3]=np.rint(a[:,:,:3].astype(float)*255/denom[:,:,None]).clip(0,255).astype('uint8')
 unsh[~alpha]=0
 shadow=np.zeros((h,w,4),np.uint8);shadow[:,:,3]=sh
 # Use a static base palette. A nighttime color variant never moves any pixel or aperture.
 fullbase=Image.fromarray(unsh,'RGBA')
 body_day=[cut(fullbase,floor),cut(fullbase,walls),cut(fullbase,win),cut(fullbase,panels),cut(fullbase,door),Image.new('RGBA',(w,h)),Image.new('RGBA',(w,h)),Image.fromarray(shadow,'RGBA'),Image.new('RGBA',(w,h)),cut(fullbase,front)]
 # Ensure the reconstructed visible result is exact (integer blend roundoff can be one level).
 reconstructed=Image.new('RGBA',(w,h))
 for b in body_day:reconstructed.alpha_composite(b)
 # Source RGB, not the backdrop, is the canonical image.
 assert np.abs(np.array(reconstructed).astype(int)-a.astype(int)).max()<=1, 'Shadow decomposition color error'
 assert np.array(reconstructed)[:,:,:3][alpha].mean()>35, 'Unexpected dark export'
 im=reconstructed
 fd=OUT/'salles'/info['dossier'];fd.mkdir(exist_ok=True)
 hd=OUT/'fenetres_exterieur'/rid;hd.mkdir(exist_ok=True)
 Image.fromarray(hole.astype('uint8')*255,'L').save(hd/'masque.png',optimize=True)
 # One continuous panorama sampled behind all panes: no different invented scenery per window.
 scale=w/648;pan_h=round(432*scale);target_y=np.mean([(b[1]+b[3])/2 for b in windows]) if windows else h*.3;oy=round(target_y-215*scale)
 exts={}
 for weather in MODES:
  p=Image.open(OUT/'exterieur'/f'{weather}.png').convert('RGBA').resize((w,pan_h),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(w,h));canvas.alpha_composite(p,(0,oy));pa=np.array(canvas);pa[:,:,3]=hole.astype('uint8')*255;pa[~hole]=0;view=Image.fromarray(pa,'RGBA');png(view,hd/(weather+'.png'));exts[weather]=view
 row={'id':rid,'nom':info['nom'],'dossier':info['dossier'],'dimensions':[w,h],'cellules':[w//8,h//8],'acces':routes,'fenetres':windows,'trous_fenetres':int(hole.sum()),'porte_nord':doorbox,'objets':[],'decorations':[],'fichiers':{}}
 for mode in ['jour','nuit']:
  body=body_day if mode=='jour' else [night(b) if i!=7 else b.copy() for i,b in enumerate(body_day)]
  # Black shadow remains a fixed opacity plane in both modes. No animation or fake door panel.
  body=[q.copy() for q in body];body[7]=Image.fromarray(shadow,'RGBA')
  base_comp=Image.new('RGBA',(w,h))
  for q in body:base_comp.alpha_composite(q)
  assert np.max(np.array(base_comp)[:,:,3][hole],initial=0)==0
  png(base_comp,fd/f'base_{mode}_transparente.png')
  chroma=Image.new('RGBA',(w,h),(255,0,255,255));chroma.alpha_composite(base_comp);png(chroma,fd/f'base_{mode}_magenta.png')
  layer_images=[exts[mode]]+body
  ld=OUT/'calques'/info['dossier']/mode;ld.mkdir(parents=True,exist_ok=True)
  comp=Image.new('RGBA',(w,h));export=[]
  for (name,label_),q in zip(LABELS,layer_images):png(q,ld/(name+'.png'));comp.alpha_composite(q);export.append((label_,q))
  png(comp,fd/f'salle_{mode}.png');ase(fd/f'{rid}_{mode}.aseprite',export,(w,h))
  cols,rows=w//8,h//8;count=cols*rows;sets=[];tls=[]
  for i,((name,label_),q) in enumerate(zip(LABELS,layer_images)):
   qa=np.array(q);occ=qa[:,:,3].reshape(rows,8,cols,8).max((1,3))>0;first=1+i*count;data=np.arange(first,first+count,dtype=np.uint32).reshape(rows,cols);data[~occ]=0
   sets.append({'firstgid':first,'name':name,'tilewidth':8,'tileheight':8,'tilecount':count,'columns':cols,'image':f'../calques/{info["dossier"]}/{mode}/{name}.png','imagewidth':w,'imageheight':h,'margin':0,'spacing':0})
   tls.append({'id':i+1,'name':label_,'type':'tilelayer','width':cols,'height':rows,'x':0,'y':0,'opacity':1,'visible':True,'data':data.ravel().tolist()})
  tm={'type':'map','version':'1.10','tiledversion':'1.11.0','orientation':'orthogonal','renderorder':'right-down','tilewidth':8,'tileheight':8,'width':cols,'height':rows,'infinite':False,'nextlayerid':len(LABELS)+1,'nextobjectid':1,'layers':tls,'tilesets':sets}
  (OUT/'tiled'/f'{rid}_{mode}.tmj').write_text(json.dumps(tm,ensure_ascii=False,separators=(',',':')))
  row['fichiers'][mode]={'png':f'salles/{info["dossier"]}/salle_{mode}.png','base':f'salles/{info["dossier"]}/base_{mode}_transparente.png','magenta':f'salles/{info["dossier"]}/base_{mode}_magenta.png','aseprite':f'salles/{info["dossier"]}/{rid}_{mode}.aseprite'}
 manifest['salles'].append(row)
 print(rid,'windows',len(windows),'apertures',int(hole.sum()),'door',bool(doorbox),'routes',routes)
if FILTER and (OUT/'kit.json').exists():
 old_manifest=json.loads((OUT/'kit.json').read_text());replacements={r['id']:r for r in manifest['salles']};manifest['salles']=[replacements.get(r['id'],r) for r in old_manifest['salles']]
(OUT/'kit.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
for mode in ['jour','nuit']:
 board=Image.new('RGB',(1536,1240),(18,20,47));d=ImageDraw.Draw(board)
 d.text((24,16),'GUILDE TREEHOUSE / PASSAGES OUVERTS / '+mode.upper(),font=font(21),fill=(237,226,190))
 d.text((24,48),'Une seule porte nord vers le bureau · fenêtres évidées · paysage séparé · grille 8 px · images fixes',font=font(13),fill=(178,192,180))
 for i,row in enumerate(manifest['salles']):
  q=Image.open(OUT/row['fichiers'][mode]['png']).convert('RGBA');q.thumbnail((494,250),Image.Resampling.NEAREST);x=i%3*512;y=80+i//3*285;board.paste(q,(x+(512-q.width)//2,y+(250-q.height)//2),q);d.text((x+20,y+255),row['id']+'  '+row['nom'],font=font(13),fill=(237,226,190))
 board.save(OUT/'apercus'/f'planche_{mode}.png',optimize=True)
print('Full new kit built: 12 rooms, 11 independent static layers, 6 interchangeable outdoor views.')
