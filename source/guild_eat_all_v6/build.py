"""Eat for all nine members: three native, two retained, four new pixel-cleaned cycles.
Generated studies guide gestures; native anatomy, accessories and palette are authoritative.
No food/emote baked into character frames; no automatic mirror or form substitution.
"""
from pathlib import Path
import sys,json,copy,shutil,hashlib,math,bisect
import xml.etree.ElementTree as ET
import numpy as np
from scipy.ndimage import binary_dilation
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent;OUT=ROOT/'exports/guild_eat_all_v6';REF=ROOT/'source/guild_members_audit/references'
sys.path.insert(0,str(ROOT))
from source.guild_scene_recovery_v5.build import native,points,markers,lerp,export_action,EASE,EAT_TICKS,DIRS
MEMBERS=[('0282','Gardevoir'),('0083','Canarticho'),('0674','Pandespiègle'),('0371','Draby'),('0285','Balignon'),('0440','Ptiravi'),('0417','Pachirisu'),('0461','Dimoret'),('0186','Tarpaud')]
NEW={'0083','0674','0461','0186'}
NEW_TICKS={
 '0083':[6,4,4,3,3,4,5,4,5,4,3,3,4,4,4,6],
 '0674':[6,4,3,3,4,4,5,4,5,4,4,3,3,4,5,8],
 '0461':[8,4,3,3,3,3,4,5,6,4,3,3,3,4,5,8],
 '0186':[8,4,4,4,4,5,7,4,7,4,5,4,4,4,5,10],
}
DUCK_HEAD=[(6,2,16,15),(8,2,19,14),(10,2,21,12),(9,2,20,12),(7,1,18,12),(4,2,15,12),(3,2,14,14),(5,2,16,14)]
DUCK_PITCH=[0,0,0,1,1,2,2,1,2,1,1,0,0,0,0,0]
# Separate anatomy-specific, per-view trajectories. No direction is manufactured by mirroring.
PAWS={
 '0674':[
  [('right',(9,20),(9,18)),('left',(15,20),(15,18))],
  [('right',(10,20),(12,19))], [('right',(12,20),(15,19))],
  [('right',(14,20),(17,19))],
  [('right',(15,20),(15,18)),('left',(9,20),(9,18))],
  [('left',(9,20),(8,19))], [('left',(11,20),(8,19))], [('left',(13,20),(11,19))]],
 '0461':[
  [('right',(11,22),(13,22))], [('left',(12,23),(17,22))], [('left',(18,22),(22,22))],
  [('left',(20,21),(22,20))], [('right',(22,21),(22,20))], [('left',(11,21),(9,20))],
  [('left',(14,22),(9,22))], [('left',(19,23),(14,22))]],
 '0186':[
  [('right',(11,30),(13,30)),('left',(21,30),(19,30))],
  [('right',(15,31),(19,30))], [('left',(19,30),(23,29))], [('left',(22,29),(23,27))],
  [('right',(22,28),(21,25)),('left',(10,28),(11,25))],
  [('left',(10,29),(9,27))], [('left',(13,30),(9,29))], [('left',(17,31),(13,30))]],
}
SHADE={'0674':(74,73,82,255),'0461':(79,95,151,255),'0186':(95,183,39,255)}
FOOT_START={'0674':23,'0461':28,'0186':35}

def accessory_mask(slot,a):
 rgb=a[:,:,:3].astype(int);opaque=a[:,:,3]>0
 if slot in ['0083','0674']:
  green=(rgb[:,:,1]>rgb[:,:,0]*1.2)&(rgb[:,:,1]>rgb[:,:,2]*1.25)&opaque
  return binary_dilation(green)&opaque
 if slot=='0186':
  blue=(rgb[:,:,2]>rgb[:,:,0]*1.1)&(rgb[:,:,2]>rgb[:,:,1]*1.1)&opaque
  return binary_dilation(blue)&opaque
 return np.zeros(a.shape[:2],bool)

def duck_cycle(views):
 rows=[];masks=[]
 for di,(normal,offset,shadow) in enumerate(views):
  a=np.array(normal);p=points(offset);protected=accessory_mask('0083',a);masks.append(protected)
  box=DUCK_HEAD[di];l,t,r,b=box;row=[]
  for fi,pitch in enumerate(DUCK_PITCH):
   im=normal.copy();q=copy.deepcopy(p)
   if pitch:
    head=normal.crop(box).resize((r-l,b-t-pitch),Image.Resampling.NEAREST)
    im.paste((0,0,0,0),box);im.alpha_composite(head,(l,t+pitch))
    hx,hy=p['head'];q['head']=(hx,min(b-1,t+pitch+round((hy-t)*(b-t-pitch)/(b-t))))
    if fi in [6,8] and di!=4:
     x,y=q['head'];d=ImageDraw.Draw(im);d.point((x,y),fill=(119,63,0,255))
     if di in [0,1,7]:d.point((min(r-1,x+1),y),fill=(119,63,0,255))
    ar=np.array(im);ar[protected]=a[protected];im=Image.fromarray(ar)
   off,_=markers(im.size,q);row.append([im,off,shadow.copy()])
  rows.append(row)
 return rows,masks

def limb_masks(slot,a,p,di):
 h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];protected=accessory_mask(slot,a);items=[]
 for part,shoulder,target in PAWS[slot][di]:
  wx,wy=p[part];radius=2 if slot!='0461' else 5
  circle=(xx-wx)**2+(yy-wy)**2<=radius**2
  if slot=='0461':
   rgb=a[:,:,:3].astype(int);claw=(rgb[:,:,0]>150)&(rgb[:,:,1]>150)&(rgb[:,:,2]>180)&(a[:,:,3]>0)
   patchmask=binary_dilation(claw&circle)&circle&(a[:,:,3]>0)
  else:patchmask=circle&(a[:,:,3]>0)
  patchmask[FOOT_START[slot]:]=False;patchmask&=~protected
  patch=a.copy();patch[~patchmask]=0
  line=Image.new('L',(w,h));ImageDraw.Draw(line).line([shoulder,(wx,wy)],fill=255,width=3)
  erase=(patchmask|(np.array(line)>0))&(a[:,:,3]>0)&~protected
  erase[FOOT_START[slot]:]=False
  # Do not erase the cream head, muzzle/leaf, collar, crest or belly markings as if they were arms.
  if slot=='0674':erase[:19]=False
  if slot=='0461':
   rgb=a[:,:,:3].astype(int);red=(rgb[:,:,0]>rgb[:,:,1]*1.5)&(rgb[:,:,0]>80);erase&=~red;erase[:19]=False
  if slot=='0186':erase[:28]=False
  items.append((part,shoulder,target,Image.fromarray(patch),erase))
 return items,protected

def frog_swallow(im,p,amount,protected,original):
 if not amount:return im,p
 # Back-view swallowing is a restrained deformation of the green upper body, not a face on the back.
 a=np.array(im);out=a.copy();mapping=[y+round(amount*max(0,math.sin(math.pi*(y-19)/15))) for y in range(19,35)]
 for y in range(19,35):
  sy=min(range(19,35),key=lambda v:abs(mapping[v-19]-y));out[y]=a[sy]
 out[protected]=original[protected]
 q={k:(x,y+round(amount*max(0,math.sin(math.pi*(y-19)/15)))) if 19<=y<35 else (x,y) for k,(x,y) in p.items()}
 return Image.fromarray(out),q

def paw_cycle(slot,views):
 rows=[];masks=[]
 for di,(normal,offset,shadow) in enumerate(views):
  a=np.array(normal);p=points(offset);items,protected=limb_masks(slot,a,p,di);masks.append(protected);erase=np.logical_or.reduce([item[4] for item in items]);body=a.copy();body[erase]=0;row=[]
  for fi,t in enumerate(EASE):
   im=normal.copy();q=copy.deepcopy(p)
   if t:
    im=Image.fromarray(body)
    for part,shoulder,target,patch,e in items:
     hand=lerp(p[part],target,t);dx=hand[0]-p[part][0];dy=hand[1]-p[part][1]
     layer=Image.new('RGBA',normal.size);d=ImageDraw.Draw(layer);d.line([shoulder,hand],fill=(0,0,0,255),width=3);d.line([shoulder,hand],fill=SHADE[slot],width=1)
     layer.alpha_composite(patch,(dx,dy));im.alpha_composite(layer);q[part]=hand
    ar=np.array(im)
    if di in [3,4,5]:
     occlusion=(a[:,:,3]>0)&~erase;ar[occlusion]=a[occlusion]
    ar[protected]=a[protected];ar[FOOT_START[slot]:]=a[FOOT_START[slot]:];im=Image.fromarray(ar)
    if slot=='0186':
     if di in [3,4,5]:im,q=frog_swallow(im,q,1 if fi in [6,8,10] else 0,protected,a)
     elif fi in [6,8]:
      x,y=p['head'];ImageDraw.Draw(im).line([(x-1,y-1),(x,y-1)],fill=(39,135,0,255))
   off,_=markers(im.size,q);row.append([im,off,shadow.copy()])
  rows.append(row)
 return rows,masks

def normalize_identical_frames(rows):
 # PMDO shares offset data when art is deduplicated. Hidden limb motion cannot assign
 # conflicting offsets to an identical rendered frame. Keep the first anatomical placement.
 seen={};changes=0
 for row in rows:
  for frame in row:
   key=(frame[0].tobytes(),frame[2].tobytes())
   if key in seen:
    if frame[1].tobytes()!=seen[key].tobytes():changes+=1;frame[1]=seen[key].copy()
   else:seen[key]=frame[1].copy()
 return changes

def read_action(folder,name='Eat'):
 root=ET.parse(folder/'AnimData.xml').getroot();nodes={n.findtext('Name'):n for n in root.findall('./Anims/Anim')};node=nodes[name];seen=set()
 while node.findtext('CopyOf'):
  target=node.findtext('CopyOf');assert target not in seen;seen.add(target);node=nodes[target]
 target=node.findtext('Name');w=int(node.findtext('FrameWidth'));h=int(node.findtext('FrameHeight'));ticks=[int(t.text) for t in node.findall('./Durations/Duration')]
 sheets=[Image.open(folder/f'{target}-{k}.png').convert('RGBA') for k in ['Anim','Offsets','Shadow']]
 assert sheets[0].width==w*len(ticks) and sheets[0].height%h==0
 rows=[[[s.crop((f*w,d*h,(f+1)*w,(d+1)*h)) for s in sheets] for f in range(len(ticks))] for d in range(sheets[0].height//h)]
 return rows,ticks

def tile(triple):
 art,off,shadow=triple;a=np.array(shadow);pts=np.argwhere(np.all(a==[255,255,255,255],axis=2));assert len(pts)==1
 y,x=pts[0];im=Image.new('RGBA',(64,64),(35,47,60,255));im.alpha_composite(art,(32-int(x),50-int(y)));return im.convert('RGB')

def previews(slot,rows,ticks):
 out=OUT/'review';out.mkdir(exist_ok=True);ends=np.cumsum(ticks)*1000/60;rounded=[round(x/10)*10 for x in ends];duration=np.diff([0]+rounded).tolist()
 # Fixed common crop over the whole action, all views/frames: no camera bob or per-frame auto-fit.
 bounds=[]
 for row in rows:
  for triple in row:
   a=np.array(tile(triple));ys,xs=np.where(np.any(a!=[35,47,60],axis=2));bounds.append((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
 crop=(max(0,min(b[0] for b in bounds)-3),max(0,min(b[1] for b in bounds)-3),min(64,max(b[2] for b in bounds)+3),min(64,max(b[3] for b in bounds)+3))
 def zoom(triple,scale):
  im=tile(triple).crop(crop);return im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)

 for d,row in enumerate(rows):
  images=[zoom(t,6) for t in row];images[0].save(out/f'{slot}_Eat_{DIRS[d]}.gif',save_all=True,append_images=images[1:],duration=duration,loop=0,disposal=2)
 if len(rows)==8:
  boards=[]
  for f in range(len(ticks)):
   b=Image.new('RGB',(512,304),(35,47,60));draw=ImageDraw.Draw(b)
   for d,row in enumerate(rows):
    x=d%4*128;y=d//4*152;b.paste(zoom(row[f],3),(x,y+24));draw.text((x+5,y+5),DIRS[d],fill='white')
   boards.append(b)
  boards[0].save(out/f'{slot}_Eat_8directions.gif',save_all=True,append_images=boards[1:],duration=duration,loop=0,disposal=2)
 board=Image.new('RGB',(640,152*len(rows)),(35,47,60));draw=ImageDraw.Draw(board)
 phases=[0,4,7,11,15] if len(ticks)==16 else [0,1,2,3]
 for d,row in enumerate(rows):
  for col,f in enumerate(phases):
   board.paste(zoom(row[f],3),(col*128,d*152+24));draw.text((col*128+4,d*152+5),DIRS[d]+'/'+str(f),fill='white')
 board.save(out/f'{slot}_Eat_keyframes.png')

def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'credits').mkdir(exist_ok=True);(OUT/'masks').mkdir(exist_ok=True)
 report={'scope':'Eat available for nine guild members; not all other guild actions completed.','food_in_sprite':False,'runtime_PMDO':'NOT TESTED','new_art_approved':False,'user_selection':'All previously presented guild proposals retained; not automatic approval of these previously unseen four drawings.','source_pin':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','members':[],'method':'Four new gesture studies on magenta, followed by explicit pixel-authored native-part articulation. Raw generated facial/accessory/proportion errors not accepted as finished sprites.'}
 sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'));from validate import run
 for slot,name in MEMBERS:
  base=REF/slot/'sprite';status='native_preserved'
  if slot in ['0282','0285']:base=ROOT/'exports/guild_scene_recovery_v5'/('gardevoir_candidate' if slot=='0282' else 'shroomish_candidate');status='v5_cycle_retained'
  elif slot=='0461':base=ROOT/'exports/guild_scene_animations_v1/weavile_canonical'
  pack=OUT/'characters'/slot;pack.mkdir(parents=True,exist_ok=True)
  for p in base.iterdir():
   if p.suffix in ['.png','.xml']:shutil.copyfile(p,pack/p.name)
  adjustments=0
  if slot in NEW:
   views=native(slot);rows,masks=duck_cycle(views) if slot=='0083' else paw_cycle(slot,views);adjustments=normalize_identical_frames(rows)
   export_action(pack,ET.parse(base/'AnimData.xml').getroot(),'Eat',rows,NEW_TICKS[slot]);status='new_technical_candidate'
   for d,mask in enumerate(masks):Image.fromarray(np.uint8(mask)*255).save(OUT/'masks'/f'{slot}_{DIRS[d]}_protected.png')
  rows,ticks=read_action(pack);previews(slot,rows,ticks)
  check=run('sprite',pack,'dungeon');assert check['technical_precheck']=='PASS',(slot,check['errors'])
  preserved={}
  for p in (REF/slot/'sprite').glob('*.png'):
   assert p.read_bytes()==(pack/p.name).read_bytes();preserved[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  shutil.copyfile(REF/slot/'sprite/credits.txt',OUT/'credits'/f'{slot}_native.txt')
  if slot in ['0282','0461']:shutil.copyfile(REF/slot/('0002' if slot=='0282' else '0001')/'sprite/credits.txt',OUT/'credits'/f'{slot}_cutscene.txt')
  unique=[len({t[0].tobytes() for t in row}) for row in rows]
  if slot in NEW:
   for row in rows:assert row[0][0].tobytes()==row[-1][0].tobytes()
   assert min(unique)>=2,(slot,unique)
  report['members'].append({'slot':slot,'name':name,'state':status,'directions':len(rows),'frames_per_direction':len(ticks),'ticks':ticks,'unique_drawings':unique,'hidden_marker_normalizations':adjustments,'native_hashes':preserved,'technical_check':check})
 report['coverage']={'members_with_Eat':9,'new_cycles':4,'retained_v5_cycles':2,'native_Eat_preserved':3,'eight_direction_cycles':6,'native_single_view_cycles':3,'gif_count':len(list((OUT/'review').glob('*.gif')))}
 (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(report['coverage'])
if __name__=='__main__':main()
