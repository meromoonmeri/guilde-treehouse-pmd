"""Custom draft: 8 directions, independently articulated flipper Walk, new expressions.
Original Normal remains byte-for-byte unchanged; adaptations credited separately.
"""
from pathlib import Path
import json,sys,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).parent;OUT=ROOT/'exports/pokemon_custom/tirtouga_v2'
for n in ['sprite_multisheet','portraits_individual','portrait_sheet','review']:(OUT/n).mkdir(parents=True,exist_ok=True)
palette=[(22,29,41),(36,47,61),(53,67,83),(72,87,104),(96,115,127),(133,155,163),(185,206,203),(236,248,239),(39,77,108),(48,107,147),(72,143,182),(111,190,213),(161,224,232),(112,64,75),(196,117,133)]
pal=Image.new('P',(1,1));pal.putpalette(sum((list(c) for c in palette),[])+[0]*(768-len(palette)*3))
raw=Image.open(SRC/'generated_magenta.png').convert('RGB'); cw=raw.width//4;ch=raw.height//2;poses=[]
for k in range(8):
 im=raw.crop(((k%4)*cw+8,(k//4)*ch+8,(k%4+1)*cw-8,(k//4+1)*ch-8)).convert('RGBA');a=np.array(im);r,g,b=[a[:,:,i].astype(float) for i in range(3)];a[(r>60)&(b>60)&(r>1.6*g)&(b>1.5*g),3]=0;im=Image.fromarray(a);im=im.crop(im.getbbox());im.thumbnail((34,30),Image.Resampling.NEAREST)
 alpha=im.getchannel('A').point(lambda x:255 if x>=128 else 0); im=im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA');im.putalpha(alpha)
 if k==1:im=ImageOps.mirror(im) # generated cell faced southwest, repair its direction
 canvas=Image.new('RGBA',(48,48));canvas.alpha_composite(im,((48-im.width)//2,36-im.height));poses.append(canvas)
# Reviewable manually defined head/body/right/left limb anchors, refined below after pixel inspection.
heads=[(24,32),(31,29),(35,25),(32,14),(24,10),(14,14),(11,25),(17,29)]
# Hand-selected COMPLETE flipper polygons include their outlines; selecting only blue
# pixels would tear the outlines off during movement (rejected after inspection).
fin_polygons=[
 [[(6,24),(16,28),(19,29),(17,34),(7,34)],[(29,29),(40,24),(41,34),(30,34)]],
 [[(10,33),(19,29),(24,28),(24,34),(14,37)],[(35,17),(40,16),(41,26),(35,27)]],
 [[(8,28),(15,28),(15,33),(7,34)],[(26,29),(30,28),(30,33),(25,36),(20,36)]],
 [[(7,21),(12,19),(12,25),(7,28)],[(33,20),(38,18),(40,30),(35,30)]],
 [[(8,13),(16,13),(17,16),(9,21),(6,21)],[(29,14),(33,13),(40,21),(36,21),(30,17)]],
 [[(8,19),(12,19),(12,27),(7,30),(6,25)],[(34,23),(39,23),(40,28),(36,28)]],
 [[(17,28),(21,29),(24,35),(18,36),(15,33)],[(31,29),(38,29),(39,34),(34,34)]],
 [[(7,18),(11,21),(13,24),(13,27),(8,27)],[(24,29),(28,29),(35,33),(35,36),(26,35),(23,33)]]]
eye_pixels={0:[(21,31),(25,31)],1:[(32,29)],2:[(35,25)],6:[(12,25)],7:[(16,29)]}
for di,coords in eye_pixels.items():
 for xy in coords:
  if poses[di].getpixel(xy)[3]:poses[di].putpixel(xy,palette[7]+(255,))
# Explicit masks select blue flippers outside the shell, not a global sprite deformation.
# Keep shell/head fixed; translate detached distal paddle pixels one pixel through 4 phases.
frames_by_action={}
for action in ['Idle','Walk']:
 rows=[]
 for direction,base in enumerate(poses):
  frames=[]; a=np.array(base); masks=[]
  for polygon in fin_polygons[direction]:
   m=Image.new('1',(48,48));ImageDraw.Draw(m).polygon(polygon,fill=1);masks.append(np.array(m)&(a[:,:,3]>0))
  eligible=masks[0]|masks[1]
  for phase in range(4):
   frame=base.copy()
   if action=='Walk':
    body=np.array(base);body[eligible]=0;frame=Image.fromarray(body)
    for side,mask in enumerate(masks):
     part=np.zeros_like(a);part[mask]=a[mask]
     dy=([0,-1,0,1] if side else [0,1,0,-1])[phase]
     frame.alpha_composite(Image.fromarray(part),(0,dy))
   elif phase==3:
    for xy in eye_pixels.get(direction,[]):
     if frame.getpixel(xy)[3]:frame.putpixel(xy,palette[1]+(255,))
   frames.append(frame)
  rows.append(frames)
 frames_by_action[action]=rows
root=ET.Element('AnimData');ET.SubElement(root,'ShadowSize').text='0';anims=ET.SubElement(root,'Anims')
limb_targets=[[(13,30),(34,30)],[(19,32),(37,22)],[(26,32),(30,25)],[(36,24),(19,9)],[(33,16),(12,16)],[(30,9),(9,24)],[(17,25),(20,32)],[(9,24),(29,33)]]
landmarks=[]
for action,rows in frames_by_action.items():
 node=ET.SubElement(anims,'Anim')
 for k,v in [('Name',action),('Index',7 if action=='Idle' else 0),('FrameWidth',48),('FrameHeight',48)]:ET.SubElement(node,k).text=str(v)
 durations=ET.SubElement(node,'Durations')
 for tick in ([12]*4 if action=='Walk' else [18]*4):ET.SubElement(durations,'Duration').text=str(tick)
 sheets={k:Image.new('RGBA',(192,384)) for k in ['Anim','Offsets','Shadow']}
 for direction,row in enumerate(rows):
  for phase,frame in enumerate(row):
   # Mark nearest opaque pixel to stable authored anatomical landmark.
   a=np.array(frame);ys,xs=np.where(a[:,:,3]>0)
   def nearest(p,used):
    order=np.argsort((xs-p[0])**2+(ys-p[1])**2)
    return next((int(xs[i]),int(ys[i])) for i in order if (int(xs[i]),int(ys[i])) not in used)
   off=Image.new('RGBA',(48,48));od=ImageDraw.Draw(off);used=[]
   for target,color in [(heads[direction],(0,0,0,255)),((24,23),(0,255,0,255)),(limb_targets[direction][0],(255,0,0,255)),(limb_targets[direction][1],(0,0,255,255))]:
    p=nearest(target,used);used.append(p);od.point(p,fill=color)
   sh=Image.new('RGBA',(48,48));sd=ImageDraw.Draw(sh)
   # Combined additive RGB masks, nested red/green/blue sizes.
   sd.ellipse((13,24,35,32),fill=(255,0,0,255));sd.ellipse((16,25,32,31),fill=(255,255,0,255));sd.ellipse((19,26,29,30),fill=(255,255,255,255))
   # Only center white is allowed; blue region must use blue without all three channels.
   sd.ellipse((19,26,29,30),fill=(0,0,255,255));sd.point((24,28),fill=(255,255,255,255))
   for kind,img in [('Anim',frame),('Offsets',off),('Shadow',sh)]:sheets[kind].paste(img,(phase*48,direction*48))
   landmarks.append({'action':action,'direction':direction,'phase':phase,'head_center_right_left':used})
 for kind,im in sheets.items():im.save(OUT/'sprite_multisheet'/f'{action}-{kind}.png')
ET.indent(root);ET.ElementTree(root).write(OUT/'sprite_multisheet/AnimData.xml',encoding='utf-8',xml_declaration=True)
(OUT/'review/landmarks.json').write_text(json.dumps(landmarks,indent=2)+'\n')
# Expressions: pixel-authored adaptations of credited existing portrait, not new Normal art.
normal=Image.open(SRC/'references/Normal.png').convert('RGBA');templates=Image.open(ROOT/'template.png').convert('RGBA');sheet=Image.new('RGBA',(200,160));sheet.paste(normal,(0,0));normal.save(OUT/'portraits_individual/Normal.png')
colors={'dark':(38,47,54,255),'face':(60,73,92,255),'mid':(76,90,116,255),'light':(94,113,146,255),'white':(255,255,255,255),'blue':(158,200,212,255)}
for name,slot in [('Happy',1),('Angry',3),('Sad',5)]:
 im=normal.copy();a=np.array(im);bg=np.zeros((40,40),bool)
 for c in [(238,254,200),(118,198,214),(177,220,201)]:bg|=np.all(a[:,:,:3]==c,axis=2)
 tb=templates.crop(((slot%5)*40,(slot//5)*40,(slot%5+1)*40,(slot//5+1)*40)).convert('RGB').quantize(colors=3,dither=Image.Dither.NONE).convert('RGBA');ta=np.array(tb);a[bg]=ta[bg];im=Image.fromarray(a);d=ImageDraw.Draw(im)
 if name=='Happy':
  d.polygon([(12,19),(14,19),(15,21),(17,22),(17,28),(13,27),(12,25)],fill=colors['face'])
  d.line([(12,24),(13,22),(15,22),(17,24)],fill=colors['dark'],width=1)
  d.line([(13,26),(15,27),(17,26)],fill=colors['blue'],width=1)
  d.line([(28,29),(29,30),(31,29),(32,27)],fill=colors['dark'],width=1)
 elif name=='Angry':
  d.polygon([(11,18),(13,19),(17,22),(18,24),(14,21),(12,21)],fill=colors['dark'])
  d.line([(13,18),(16,19),(18,21)],fill=colors['light'],width=1)
  d.line([(29,29),(31,28),(32,29)],fill=colors['dark'],width=1)
 elif name=='Sad':
  d.polygon([(12,19),(14,19),(17,22),(17,24),(14,22),(12,22)],fill=colors['face'])
  d.line([(11,20),(13,19),(16,21)],fill=colors['dark'],width=1)
  d.line([(13,27),(15,28),(17,27)],fill=colors['blue'],width=1)
  d.line([(28,30),(30,28),(32,29)],fill=colors['dark'],width=1)
 im.save(OUT/'portraits_individual'/f'{name}.png');sheet.paste(im,((slot%5)*40,(slot//5)*40))
sheet.save(OUT/'portrait_sheet/portraits.png');sheet.resize((800,640),Image.Resampling.NEAREST).save(OUT/'review/portraits_zoom.png')
review=Image.new('RGBA',(48*8,48*2),(235,223,199,255))
for d in range(8):
 review.alpha_composite(poses[d],(48*d,0));review.alpha_composite(frames_by_action['Walk'][d][1],(48*d,48))
review.resize((1152,288),Image.Resampling.NEAREST).save(OUT/'review/sprites_zoom.png')
for action,rows in frames_by_action.items():
 fs=[]
 for phase in range(4):
  tile=Image.new('RGBA',(48*8,48),(235,223,199,255))
  for di,row in enumerate(rows):tile.alpha_composite(row[phase],(48*di,0))
  fs.append(tile.resize((1152,144),Image.Resampling.NEAREST).convert('RGB'))
 fs[0].save(OUT/'review'/f'{action}.webp',save_all=True,append_images=fs[1:],duration=200 if action=='Idle' else 133,loop=0,lossless=True)
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'));import validate
reports={'sprite_minimum':validate.run('sprite',OUT/'sprite_multisheet'),'sprite_dungeon':validate.run('sprite',OUT/'sprite_multisheet','dungeon'),'portrait_minimum':validate.run('portrait',OUT/'portrait_sheet/portraits.png'),'portrait_full':validate.run('portrait',OUT/'portrait_sheet/portraits.png','full')}
(OUT/'review/validation.json').write_text(json.dumps(reports,indent=2)+'\n');print({k:v['technical_precheck'] for k,v in reports.items()})
