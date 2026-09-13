from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/cafe_multietage_v1';SOURCES={}
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
metano=load(P/'Metano_Town_Cafe_Base.png');spinda=load(P/'SpindaCafe1.png')
patchspec={'plancher':('Metano_Town_Cafe_Base.png',(128,160,192,224)),'panneau_bois':('Metano_Town_Cafe_Base.png',(128,48,160,80)),'montant':('Metano_Town_Cafe_Base.png',(104,48,112,80)),'traverse':('Metano_Town_Cafe_Base.png',(120,80,152,88)),'escalier':('SpindaCafe1.png',(320,336,384,392))}
patches={}
for name,(file,box) in patchspec.items():
 patches[name]=load(P/file).crop(box);save(patches[name],O/'materiaux'/f'{name}.png');SOURCES[name]={'file':file,'box':list(box),'rgba_sha256':hashlib.sha256(patches[name].tobytes()).hexdigest()}
def tile(patch,size):
 o=Image.new('RGBA',size)
 for y in range(0,size[1],patch.height):
  for x in range(0,size[0],patch.width):o.alpha_composite(patch,(x,y))
 return o
# Remove ALL furniture silhouettes and counter remnants, keep native room shell.
spmask=Image.new('L',spinda.size);d=ImageDraw.Draw(spmask);d.polygon([(176,144),(520,144),(548,176),(556,212),(553,260),(520,293),(484,314),(400,324),(384,327),(320,327),(311,319),(216,317),(174,291),(143,257),(140,211),(149,174)],fill=255)
spempty=Image.composite(tile(patches['plancher'],spinda.size),spinda,spmask)
# Back-wall fixtures become empty wood panels; not furniture retained from the sheet.
for box in [(224,96,288,144),(416,96,480,144)]:spempty.alpha_composite(tile(patches['panneau_bois'],(box[2]-box[0],box[3]-box[1])),box[:2])
# Upper room's canonical Base is already empty.
mfloor=Image.new('L',metano.size);ImageDraw.Draw(mfloor).polygon([(112,88),(344,88),(429,144),(429,239),(350,296),(109,296),(27,239),(27,144)],fill=255)
# Extend by inserting exact 8px strips; never stretch native texture pixels.
def extend(im,extra_x,extra_y,cx,cy):
 w,h=im.size;mode=im.mode;out=Image.new(mode,(w+extra_x,h))
 out.paste(im.crop((0,0,cx,h)),(0,0));strip=im.crop((cx,0,cx+8,h))
 for x in range(cx,cx+extra_x,8):out.paste(strip,(x,0))
 out.paste(im.crop((cx,0,w,h)),(cx+extra_x,0));res=Image.new(mode,(w+extra_x,h+extra_y));res.paste(out.crop((0,0,out.width,cy)),(0,0));strip=out.crop((0,cy,out.width,cy+8))
 for y in range(cy,cy+extra_y,8):res.paste(strip,(0,y))
 res.paste(out.crop((0,cy,out.width,h)),(0,cy+extra_y));return res

def remove_outside(im):
 a=np.array(im);bg=a[0,0,:3];same=np.all(a[:,:,:3]==bg,axis=2);seen=np.zeros(same.shape,bool);stack=[];h,w=same.shape
 for x in range(w):
  if same[0,x]:stack.append((0,x))
  if same[h-1,x]:stack.append((h-1,x))
 for y in range(h):
  if same[y,0]:stack.append((y,0))
  if same[y,w-1]:stack.append((y,w-1))
 while stack:
  y,x=stack.pop()
  if seen[y,x]:continue
  seen[y,x]=True
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
   ny,nx=y+dy,x+dx
   if 0<=ny<h and 0<=nx<w and same[ny,nx] and not seen[ny,nx]:stack.append((ny,nx))
 a[seen]=0;return Image.fromarray(a)
levels=[('ss2','Sous-sol −2','Spinda',96,24),('ss1','Sous-sol −1','Spinda',16,104),('accueil','Accueil','Metano',112,64),('etage1','Étage +1','Metano',64,128),('etage2','Étage +2','Metano',160,48)]
manifest={'levels':[],'materials':SOURCES,'window_views':'232233.png, paysage canonique fourni précédemment; fenêtres = nouveaux assemblages de poutres natives','native_texture_scale':1,'grid_px':8,'runtime_validated':False,'furniture':False}
for variant in ['A','B']:
 for index,(slug,title,family,ex,ey) in enumerate(levels):
  ex+=64 if variant=='B' else 0;ey+=32 if variant=='B' else 0;underground=family=='Spinda';src=spempty if underground else metano;fm=spmask if underground else mfloor;cx,cy=(344,224) if underground else (224,192)
  room=remove_outside(extend(src,ex,ey,cx,cy));floor_mask=np.array(extend(fm,ex,ey,cx,cy))>0;a=np.array(room);h,w=a.shape[:2]
  floor=a.copy();floor[~floor_mask]=0;shell=a.copy();shell[floor_mask]=0
  # Rock border is a canonical visible partition around the underground shell.
  rock_mask=np.zeros((h,w),bool)
  if underground:
   yy,xx=np.mgrid[:h,:w];left=138;right=558+ex;rock_mask=(yy<66)|(xx<left)|(xx>right)|(yy>315+ey)
  rock=shell.copy();rock[~rock_mask]=0;wood=shell.copy();wood[rock_mask]=0
  frames=Image.new('RGBA',room.size);views_day=Image.new('RGBA',room.size);views_night=Image.new('RGBA',room.size);openings=[]
  if not underground:
   # Round oculi, not rectangular bays. Smaller, widely separated at level +2.
   count=3 if index==3 else 2;diameter=32 if index==4 else 48
   starts=[int(round((w/2+(i-(count-1)/2)*120-diameter/2)/8))*8 for i in range(count)]
   panorama=load(R/'232233.png')
   gy,gx=np.mgrid[:diameter,:diameter];radius=np.sqrt((gx-(diameter-1)/2)**2+(gy-(diameter-1)/2)**2)
   aperture=radius<diameter/2-6;ring=(radius<=diameter/2-1)&(~aperture)
   for i,wx in enumerate(starts):
    wy=48 if index==4 else 32;box=(wx,wy,wx+diameter,wy+diameter);openings.append(list(box));wood[wy:wy+diameter,wx:wx+diameter][aperture]=0
    rim=np.array(tile(patches['panneau_bois'],(diameter,diameter)));rim[~ring]=0
    # Native post/traverse colors add a beveled edge without recoloring pixels.
    hi=np.array(patches['traverse'])[1,8];lo=np.array(patches['montant'])[8,1]
    rim[ring&(radius>diameter/2-3)&(gx+gy<diameter)]=hi
    rim[ring&(radius>diameter/2-3)&(gx+gy>=diameter)]=lo
    frames.alpha_composite(Image.fromarray(rim),(wx,wy))
    view=np.array(panorama.crop((64+i*32,96,64+i*32+diameter,96+diameter)));view[~aperture]=0;view=Image.fromarray(view)
    views_day.alpha_composite(view,(wx,wy));views_night.alpha_composite(night(view),(wx,wy))
  # Native stair treads on an independent structural layer, no furniture.
  stairs=Image.new('RGBA',room.size);ports=[]
  stair=patches['escalier'];sx=(w//2-100)//8*8;sy=(176 if underground else 112)
  if index<4:stairs.alpha_composite(stair,(sx,sy));ports.append({'direction':'monter','xy':[sx+32,sy+24],'target':levels[index+1][0]})
  if index>0:
   sx2=(w//2+40)//8*8;stairs.alpha_composite(stair,(sx2,sy));ports.append({'direction':'descendre','xy':[sx2+32,sy+24],'target':levels[index-1][0]})
  # Full visible shell remains editable; exterior backdrops only occupy actual apertures.
  common={'01_sol_vide':Image.fromarray(floor),'03_bois_murs':Image.fromarray(wood),'04_bordure_rocheuse':Image.fromarray(rock),'05_cadres_fenetres':frames,'06_escaliers':stairs}
  prefix=O/variant/slug
  for n,im in common.items():save(im,prefix/(n+'.png'))
  for mode,view in [('jour',views_day),('nuit',views_night)]:
   save(view,prefix/f'02_vues_exterieures_{mode}.png');comp=Image.new('RGBA',room.size)
   for n in ['01_sol_vide','02_vues','03_bois_murs','04_bordure_rocheuse','05_cadres_fenetres','06_escaliers']:comp.alpha_composite(view if n=='02_vues' else common[n])
   save(comp,prefix/f'composition_{mode}.png')
  schema=Image.new('RGB',room.size,'#1b2430');sd=ImageDraw.Draw(schema);mask_img=Image.fromarray((floor_mask*255).astype('uint8'));schema.paste('#a78c56',(0,0,w,h),mask_img)
  for p in ports:
   x,y=p['xy'];sd.rectangle((x-16,y-12,x+16,y+12),fill='#72bcc4');sd.text((x-25,y+16),p['direction'],fill='white')
  for box in openings:sd.ellipse(box,fill='#b7e2f5')
  sd.text((12,12),variant+' / '+title,fill='white');save(schema,prefix/'schema.png')
  manifest['levels'].append({'id':variant+'_'+slug,'variant':variant,'floor_id':slug,'title':title,'family':family,'size':[w,h],'extension':[ex,ey],'window_shape':'circular','bay_windows':False,'window_diameter':(32 if index==4 else 48) if not underground else 0,'window_boxes':openings,'connections':ports,'layers':list(common),'path':variant+'/'+slug})
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Two plan boards, all rooms are rendered from canonical pixels, proposals remain separate.
for variant in ['A','B']:
 board=Image.new('RGB',(1500,1100),'#1c2634');d=ImageDraw.Draw(board)
 for i,entry in enumerate([e for e in manifest['levels'] if e['variant']==variant]):
  im=load(O/entry['path']/'composition_jour.png');im.thumbnail((490,480),Image.Resampling.NEAREST);x=i%3*500;y=i//3*550;board.paste(im,(x+(500-im.width)//2,y+35),im);d.text((x+12,y+10),entry['title']+' / '+entry['family'],fill='white')
 save(board,O/f'PLANCHE_{variant}.png')
print('10 empty native-material layouts, 5 levels x2, independent windows and stairs')
