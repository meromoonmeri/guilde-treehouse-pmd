"""Reconstruct PMD sprites from inspected key poses; exports remain an art-review candidate.
No missing action is faked with an Idle alias. Generated invalid directions are rejected.
"""
from pathlib import Path
import math,json,hashlib,sys,xml.etree.ElementTree as ET
import numpy as np
from scipy.ndimage import label
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;SRC=WORK.parent/'tirtouga_v4';OUT=ROOT/'exports/pokemon_custom/tirtouga_v5'
for n in ['sprite_multisheet','review/gifs','review/sheets','work/poses']:(OUT/n).mkdir(parents=True,exist_ok=True)
PAL=[(22,29,41),(38,47,54),(48,58,74),(60,73,92),(76,90,116),(94,113,146),(67,106,166),(83,129,202),(116,166,232),(158,200,212),(235,248,239),(119,61,83),(230,134,150),(109,140,159),(43,78,108)]
P=np.array(PAL,dtype=np.int32);CELL=64;ANCHOR=(32,44);SHELL=(32,36);DIRECTIONS=['D','DR','R','UR','U','UL','L','DL']
TARGET_WIDTH=[36,34,34,30,26];head_targets=[(32,46),(43,42),(46,38),(42,29),(32,25)]
limbs=[[(20,43),(44,43)],[(27,45),(43,33)],[(36,45),(43,33)],[(42,38),(29,27)],[(41,30),(23,30)]]
notes=['Native-scale review found magenta matte fragments mapped to the mouth palette on flipper edges; stricter chroma removal added before palette mapping, preserving true warm mouth colors.']
def quant(im):
 a=np.array(im.convert('RGBA'));mask=a[:,:,3]>0;rgb=a[:,:,:3].astype(np.int32);idx=np.argmin(((rgb[:,:,None,:]-P[None,None,:,:])**2).sum(axis=3),axis=2)
 a[:,:,:3]=P[idx];a[:,:,3]=np.where(mask,255,0);a[~mask]=0;return Image.fromarray(a)
def key(im):
 a=np.array(im.convert('RGBA'));r,g,b=[a[:,:,i].astype(float) for i in range(3)]
 a[((r>140)&(b>140)&(r>g*1.18)&(b>g*1.18)) | ((r>60)&(b>60)&(r>g*1.6)&(b>g*1.5))]=0
 lab,n=label(a[:,:,3]>0)
 if n:
  sizes=np.bincount(lab.ravel());sizes[0]=0;keep=int(sizes.argmax());a[lab!=keep]=0
 im=Image.fromarray(a);box=im.getbbox();assert box;return im.crop(box)
def source_rows(name,rows,cols=4,bounds=None):
 im=Image.open(SRC/'generation'/f'{name}.png').convert('RGBA');w,h=im.size;bounds=bounds or [round(i*h/rows) for i in range(rows+1)];result=[]
 for r in range(rows):
  row=[]
  for c in range(cols):
   box=(round(c*w/cols)+3,bounds[r]+3,round((c+1)*w/cols)-3,bounds[r+1]-3);tile=im.crop(box)
   if name=='Scenes_B' and c==0:
    # Exclude caption band; Faint's caption overlaps its first pose, which is rejected below.
    tile=tile.crop((0,30,tile.width,tile.height))
   row.append(key(tile))
  result.append(row)
 return result

def register(im,scale,dy=0,dx=0,settled=False):
 im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST);im=quant(im)
 a=np.array(im);solid=a[:,:,3]>0
 # Shell material landmark: slate pixels, not all blue limbs/extended neck.
 shell=solid & (a[:,:,0]>=38)&(a[:,:,0]<=100)&(a[:,:,1]<=a[:,:,0]*1.35)&(a[:,:,2]<=a[:,:,1]*1.4)
 yy,xx=np.where(shell)
 if len(xx)<4:yy,xx=np.where(solid)
 pivot=(round((np.percentile(xx,15)+np.percentile(xx,85))/2),round((np.percentile(yy,15)+np.percentile(yy,85))/2))
 if settled:pos=(32-im.width//2+dx,48-im.height+dy)
 else:pos=(SHELL[0]-int(pivot[0])+dx,SHELL[1]-int(pivot[1])+dy)
 assert pos[0]>=0 and pos[1]>=0 and pos[0]+im.width<=64 and pos[1]+im.height<=64,(im.size,pos)
 canvas=Image.new('RGBA',(64,64));canvas.alpha_composite(im,pos);return canvas

def add_left(rows):
 # Tirtouga is bilaterally symmetric. Mirror complete poses, and swap anatomical hand markers later.
 return rows+[[ImageOps.mirror(im) for im in rows[d]] for d in [3,2,1]]
raw={name:source_rows(name,5,6 if name=='Swing' else 4) for name in ['Walk','Attack','Sleep','Hurt','Charge','Swing','Hop']}
# Manual rejections after source review. These are explicitly recorded, never silently relabeled.
raw['Walk'][0]=[raw['Walk'][0][0],raw['Walk'][0][3],raw['Walk'][0][0],ImageOps.mirror(raw['Walk'][0][3])]
notes.append('Walk D: generated phases1/2 faced DR; replaced by valid D contact pose and its symmetric paddle counterpart. 2/3 distinct drawings, not four newly generated D drawings.')
raw['Sleep'][0]=[raw['Charge'][0][2],raw['Charge'][0][3],raw['Charge'][0][2],raw['Charge'][0][3]]
notes.append('Sleep D: all generated views faced sideways; use authored low front crouch from Charge with eyes closed, instead of mislabeling a side view as D.')
raw['Hurt'][0][3]=raw['Hurt'][0][0]
notes.append('Hurt D: side-facing recovery rejected; correct front initial pose reused as recovery.')
for d in range(5):raw['Hop'][d][2]=raw['Hop'][d][1]
notes.append('Hop: generator apex changed facing and invented beige upright undersides; rejected. Two airborne phases share the correct takeoff drawing at different heights, surrounded by distinct crouch and landing drawings.')

animations={};meta={}
# Build Idle from five manually inspected directions, not generator's mislabeled last rows.
rows=[]
for d in range(5):
 base=Image.open(SRC/'references'/f'base_{d}.png');base=key(base);s=TARGET_WIDTH[d]/base.width;im=register(base,s);row=[im.copy() for _ in range(4)]
 # Existing bright eye pixels close for one short phase; never paint in arbitrary off-silhouette coordinates.
 if d<3:
  arr=np.array(row[2]);mask=np.all(arr[:,:,:3]==PAL[10],axis=2)&(arr[:,:,3]>0);arr[mask,:3]=PAL[2];row[2]=Image.fromarray(arr)
 rows.append(row)
animations['Idle']=add_left(rows);meta['Idle']={'durations':[24,8,5,11],'kind':'blink / holds; rear views static'}
for name,rrows in raw.items():
 rows=[]
 for d,source in enumerate(rrows):
  # One scale per direction/action, never recrop-rescale every pose to equal bounding boxes.
  scale=TARGET_WIDTH[d]/source[0].width
  if name=='Swing':scale=min(scale,42/max(im.width for im in source))
  if name=='Hop':scale=min(scale,37/max(im.height for im in source))
  row=[]
  for f,im in enumerate(source):
   dy=([0,-2,-5,0][f] if name=='Hop' else 0)
   c=register(im,scale,dy=dy)
   if name=='Sleep':
    a=np.array(c);bright=np.all(a[:,:,:3]==PAL[10],axis=2)&(a[:,:,3]>0);a[bright,:3]=PAL[2];c=Image.fromarray(a)
   row.append(c)
  rows.append(row)
 animations[name]=add_left(rows)
 durations={'Walk':[8]*4,'Attack':[10,5,7,12],'Sleep':[24,24,24,24],'Hurt':[5,9,7,12],'Charge':[8,10,10,14],'Swing':[7]*6,'Hop':[10,6,8,12]}[name]
 meta[name]={'durations':durations,'kind':'generated key poses registered and palette-retouched'}
# Double really plays two striking cycles; Rotate advances around eight drawn gameplay views.
animations['Double']=[[im.copy() for im in row+row] for row in animations['Attack']]
meta['Double']={'durations':[8,4,5,6,7,4,7,12],'kind':'two Attack strokes, reusable attack artwork; not eight unique drawings'}
animations['Rotate']=[[animations['Idle'][(d+f)%8][0].copy() for f in range(8)] for d in range(8)]
meta['Rotate']={'durations':[4]*8,'kind':'rotation through eight camera-consistent drawn views, no arbitrary image rotation'}

scene_names={'Scenes_A':['EventSleep','Wake','Eat','DeepBreath','Nod','LookUp'],'Scenes_B':['Tumble','Trip','LostBalance','TumbleBack','HitGround','Faint'],'Scenes_C':['Pose','Pull','Pain','Float','Sit','Sink'],'Scenes_D':['Laying','LeapForth','Head','Cringe']}
for sheet,names in scene_names.items():
 bounds={'Scenes_A':[0,175,350,512,691,854,1024],'Scenes_B':[84,245,408,565,717,869,1024]}.get(sheet)
 srows=source_rows(sheet,len(names),4,bounds)
 for rowidx,(name,source) in enumerate(zip(names,srows)):
  # Source A mostly faces SW despite prompt; mirror to DR, except later LookUp poses.
  if sheet=='Scenes_A':source=[ImageOps.mirror(im) if name!='EventSleep' and not(name=='LookUp' and f>0) else im for f,im in enumerate(source)]
  elif sheet=='Scenes_B' and name not in ['HitGround','Faint']:source=[ImageOps.mirror(im) for im in source]
  if name=='Faint':source[0]=raw['Hurt'][1][0]
  # Uniform action scale based on typical whole-character size; bound exceptional upright poses.
  scale=min(34/source[0].width,43/max(im.width for im in source),40/max(im.height for im in source))
  row=[]
  for f,im in enumerate(source):
   dy={'Float':[0,-1,-2,-1],'Sink':[0,1,3,4],'LeapForth':[0,-2,-5,0]}.get(name,[0]*4)[f]
   dx=[0,1,3,3][f] if name=='LeapForth' else 0
   c=register(im,scale,settled=True,dy=dy,dx=dx)
   if name in ['EventSleep','Faint'] and (name=='EventSleep' or f>=2):
    a=np.array(c);m=np.all(a[:,:,:3]==PAL[10],axis=2)&(a[:,:,3]>0);a[m,:3]=PAL[2];c=Image.fromarray(a)
   row.append(c)
  animations[name]=[row];meta[name]={'durations':([24]*4 if name=='EventSleep' else [10,8,10,20]),'kind':'single-direction DR cutscene keys; camera/art consistency still under review'}
notes.extend(['Scene A: first EventSleep row was pixel art but remaining source rows were smooth illustrations; all reconstructed into explicit 15-color native-size candidates, not claimed as hand-drawn native originals.', 'Scene B: unwanted titles, captions, grid and lighter magenta removed. Faint initial pose overlapped caption and was replaced by its correct Hurt anticipation.', 'Cutscene rows provide one DR orientation, not eight. Tilt/roll animations change body orientation intentionally. These require artistic review before engine submission.'])

ids={n.findtext('Name'):int(n.findtext('Index')) for n in ET.parse(SRC/'references/bulbasaur_AnimData.xml').findall('.//Anim') if n.findtext('Index') is not None}
root=ET.Element('AnimData');ET.SubElement(root,'ShadowSize').text='0';anims=ET.SubElement(root,'Anims');landmarks=[];measurements={}
# Remove no files from older versions. This folder contains only the declared action exports.
for name,rows in animations.items():
 dur=meta[name]['durations'];nframes=len(dur);node=ET.SubElement(anims,'Anim')
 for k,v in [('Name',name),('Index',ids[name]),('FrameWidth',64),('FrameHeight',64)]:ET.SubElement(node,k).text=str(v)
 if name in ['Attack','Double','Swing']:
  for k,v in [('RushFrame',1),('HitFrame',2),('ReturnFrame',nframes-1)]:ET.SubElement(node,k).text=str(v)
 ds=ET.SubElement(node,'Durations')
 for tick in dur:ET.SubElement(ds,'Duration').text=str(tick)
 sheets={k:Image.new('RGBA',(64*nframes,64*len(rows))) for k in ['Anim','Offsets','Shadow']}
 uniques=[];gifs=[]
 for d,row in enumerate(rows):
  hashes=[]
  for f,im in enumerate(row):
   hashes.append(hashlib.sha256(im.tobytes()).hexdigest());arr=np.array(im);ys,xs=np.where(arr[:,:,3]>0);used=[]
   direction=(d+f)%8 if name=='Rotate' else d if len(rows)==8 else 1
   canonical=direction if direction<=4 else 8-direction;mirror=direction>4
   hh=head_targets[canonical];ll=limbs[canonical]
   if mirror:hh=(63-hh[0],hh[1]);ll=[(63-ll[1][0],ll[1][1]),(63-ll[0][0],ll[0][1])]
   dy=[0,-2,-5,0][f] if name=='Hop' else 0
   def nearest(target):
    order=np.argsort((xs-target[0])**2+(ys-(target[1]+dy))**2)
    xy=next((int(xs[i]),int(ys[i])) for i in order if (int(xs[i]),int(ys[i])) not in used);used.append(xy);return xy
   off=Image.new('RGBA',(64,64));od=ImageDraw.Draw(off)
   for target,col in [(hh,(0,0,0,255)),(SHELL,(0,255,0,255)),(ll[0],(255,0,0,255)),(ll[1],(0,0,255,255))]:od.point(nearest(target),fill=col)
   sh=Image.new('RGBA',(64,64));sd=ImageDraw.Draw(sh);sd.ellipse((20,40,44,48),fill=(255,0,0,255));sd.ellipse((23,41,41,47),fill=(0,255,0,255));sd.ellipse((26,42,38,46),fill=(0,0,255,255));sd.point(ANCHOR,fill=(255,255,255,255))
   for kind,img in [('Anim',im),('Offsets',off),('Shadow',sh)]:sheets[kind].paste(img,(f*64,d*64))
   landmarks.append({'action':name,'row':d,'frame':f,'head_body_right_left':used,'shadow':ANCHOR})
  uniques.append(len(set(hashes)))
 for kind,img in sheets.items():img.save(OUT/'sprite_multisheet'/f'{name}-{kind}.png')
 sheets['Anim'].resize((sheets['Anim'].width*2,sheets['Anim'].height*2),Image.Resampling.NEAREST).save(OUT/'review/sheets'/f'{name}_x2.png')
 # Actual 1/60 tick durations, rounded cumulatively to GIF's 10ms granularity.
 ends=[round(sum(dur[:i+1])*100/60)*10 for i in range(len(dur))];gifdur=[ends[i]-(ends[i-1] if i else 0) for i in range(len(dur))]
 for f in range(nframes):
  cols=4 if len(rows)==8 else 1;nr=2 if len(rows)==8 else 1;canvas=Image.new('RGB',(64*cols,72*nr),(233,222,198));dd=ImageDraw.Draw(canvas)
  for d,row in enumerate(rows):
   dx=(d%cols)*64;dy=(d//cols)*72;canvas.paste(row[f],(dx,dy),row[f]);dd.text((dx+3,dy+60),DIRECTIONS[d] if len(rows)==8 else 'DR',fill=(50,60,75))
  gifs.append(canvas.resize((canvas.width*2,canvas.height*2),Image.Resampling.NEAREST))
 # A single authored global palette, plus static preview background/labels, prevents GIF palette flicker.
 palette=Image.new('P',(1,1));colors=PAL+[(233,222,198),(50,60,75)];palette.putpalette(sum((list(c) for c in colors),[])+[0]*(768-len(colors)*3))
 frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in gifs]
 frames[0].save(OUT/'review/gifs'/f'{name}.gif',save_all=True,append_images=frames[1:],duration=gifdur,loop=0,disposal=2,optimize=False)
 measurements[name]={'directions':len(rows),'columns':nframes,'unique_drawings_per_direction':uniques,'ticks':sum(dur),'gif_ms':sum(gifdur),**meta[name]}
ET.indent(root);ET.ElementTree(root).write(OUT/'sprite_multisheet/AnimData.xml',encoding='utf-8',xml_declaration=True)
(OUT/'review/landmarks.json').write_text(json.dumps(landmarks,indent=2)+'\n')
# Contact sheet: first useful pose from every action, with names, native-scale and zoom.
cols=6;contact=Image.new('RGB',(cols*80,math.ceil(len(animations)/cols)*84),(233,222,198));cd=ImageDraw.Draw(contact)
for i,(name,rows) in enumerate(animations.items()):
 im=rows[1 if len(rows)==8 else 0][min(1,len(rows[0])-1)];x=(i%cols)*80;y=(i//cols)*84;contact.paste(im,(x+8,y),im);cd.text((x+3,y+65),name,fill=(30,40,50))
contact.save(OUT/'review/contact_native.png');contact.resize((contact.width*2,contact.height*2),Image.Resampling.NEAREST).save(OUT/'review/contact_x2.png')
model=Image.new('RGBA',(64*8,64),(233,222,198,255))
for d,row in enumerate(animations['Idle']):model.alpha_composite(row[0],(64*d,0))
model.resize((1024,128),Image.Resampling.NEAREST).save(OUT/'review/model_x2.png')
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'));import validate
reports={level:validate.run('sprite',OUT/'sprite_multisheet',level) for level in ['minimum','dungeon','full']}
plan=json.loads((SRC/'production_plan.json').read_text())
for name in plan['actions']:
 plan['actions'][name]={'status':'exported_candidate_requires_art_review' if name in animations else 'not_generated_limit_reached','exported':name in animations}
plan['generation_limit_note']='Ten sources in V4, two remaining scene sources in V5; no failed generations passed off as files';plan['actions_exported']=len(animations);plan['actions_missing']=[n for n in plan['actions'] if n not in animations];(WORK/'production_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
report={'technical':reports,'actions':measurements,'manual_source_rejections_and_corrections':notes,'palette':PAL,'user_approved':'PORTRAITS ONLY; new sprite model and animations not yet approved','runtime':'NOT TESTED','artistic_status':'REVIEW CANDIDATE, not certified qualitative/final SpriteCollab art'}
(OUT/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:v['technical_precheck'] for k,v in reports.items()},'actions',len(animations),'missing',plan['actions_missing'])
