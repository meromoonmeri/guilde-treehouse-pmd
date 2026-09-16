"""Complete 16-emotion candidate, keeping all user-approved portraits byte-identical."""
from pathlib import Path
import json,hashlib,shutil,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).parent;OUT=ROOT/'exports/pokemon_custom/tirtouga_portraits_v4';OLD=ROOT/'exports/pokemon_custom/tirtouga_portraits_v3'
for n in ['portraits_individual','portrait_sheet','editable','review']:(OUT/n).mkdir(parents=True,exist_ok=True)
contract=json.load(open(ROOT/'source/pmd_character_pipeline/contract.json'));names=contract['portrait']['emotions'];required=contract['portrait']['required_full'];bgall=Image.open(ROOT/'template.png').convert('RGBA')
approval=json.load(open(ROOT/'source/pokemon_custom/tirtouga_portraits_v3/approval.json'));sheet=Image.new('RGBA',(200,160));report={}
core=[(38,47,54),(48,58,74),(60,73,92),(76,90,116),(94,113,146),(67,106,166),(83,129,202),(116,166,232),(158,200,212),(255,255,255)]
for file,sha in approval['sha256'].items():
 assert hashlib.sha256((OLD/'portraits_individual'/file).read_bytes()).hexdigest()==sha
 shutil.copyfile(OLD/'portraits_individual'/file,OUT/'portraits_individual'/file)
 name=Path(file).stem;i=names.index(name);sheet.paste(Image.open(OLD/'portraits_individual'/file),(i%5*40,i//5*40));report[name]={'user_approved_preserved':True,'sha256':sha}
newgen=['Pain','Worried','Crying','Joyous','Inspired','Dizzy'];adapt={'Teary-Eyed':'Sad','Determined':'Angry','Sigh':'Sad','Stunned':'Surprised'}
for name in newgen+list(adapt):
 i=names.index(name);bg=bgall.crop((i%5*40,i//5*40,i%5*40+40,i//5*40+40));budget=15-len(set(bg.getdata()));pal=core.copy()
 if name in ['Pain','Crying','Joyous','Dizzy']:pal += [(119,61,83),(230,134,150)]
 if len(pal)>budget:pal.remove((94,113,146)) # sacrifice a redundant slate shade, not the pink mouth
 edits=[]
 if name in newgen:
  raw=Image.open(SRC/'generation'/f'{name}.png').convert('RGBA');a=np.array(raw);r,g,b=[a[:,:,j].astype(float) for j in range(3)]
  a[((r>150)&(b>150)&(g<90)&(r>2*g)&(b>2*g))|((r>60)&(b>60)&(r>1.8*g)&(b>1.5*g))]=0
  im=Image.fromarray(a).resize((40,40),Image.Resampling.NEAREST);a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>127,255,0)
  if name=='Inspired':
   # Blue generated pupil restored to dark pupil, with a crisp white catchlight.
   edits=[(18,21,core[0]),(18,22,core[0]),(17,20,core[9])]
  if name=='Worried':edits=[(15,18,core[0]),(16,18,core[0]),(17,19,core[0])]
 else:
  im=Image.open(OLD/'editable'/f'{adapt[name]}_subject.png').convert('RGBA');a=np.array(im)
  if name=='Teary-Eyed':
   edits=[(13,26,core[8]),(14,27,core[9]),(15,27,core[8]),(14,28,core[8]),(14,29,core[8]),(14,30,core[9]),(15,30,core[8]),(15,31,core[8])]
  elif name=='Determined':
   edits=[(13,19,core[0]),(14,19,core[0]),(15,20,core[0]),(16,20,core[0]),(17,21,core[0]),(18,21,core[0]),(29,29,core[0]),(30,28,core[0]),(31,28,core[0])]
  elif name=='Sigh':
   for y in range(20,28):
    for x in range(12,18):
     if a[y,x,3]>0:a[y,x,:3]=core[2]
   edits=[(12,23,core[0]),(13,24,core[0]),(14,24,core[0]),(15,24,core[0]),(16,23,core[0]),(29,29,core[0]),(30,29,core[0]),(30,30,core[0])]
  elif name=='Stunned':
   # Half-lidded fixed stare and slack mouth, rather than Surprised's wide round eye.
   edits=[(13,17,core[0]),(14,17,core[0]),(15,17,core[0]),(16,17,core[0]),(17,17,core[0]),(18,18,core[0]),(17,20,core[0]),(17,21,core[0]),(23,29,core[0]),(24,29,core[0])]
 for x,y,col in edits:
  if a[y,x,3]>0:a[y,x,:3]=col
 pp=np.array(pal,dtype=np.int32);rgb=a[:,:,:3].astype(np.int32);inds=np.argmin(((rgb[:,:,None,:]-pp[None,None,:,:])**2).sum(axis=3),axis=2);a[:,:,:3]=pp[inds];a[a[:,:,3]==0]=0
 subject=Image.fromarray(a);subject.save(OUT/'editable'/f'{name}_subject.png');bg.save(OUT/'editable'/f'{name}_canonical_background.png')
 final=bg.copy();final.alpha_composite(subject);count=len(set(final.getdata()));assert count<=15;assert set(final.getchannel('A').getdata())=={255}
 empty=a[:,:,3]==0;assert np.array_equal(np.array(final)[empty],np.array(bg)[empty]);final.save(OUT/'portraits_individual'/f'{name}.png');sheet.paste(final,(i%5*40,i//5*40))
 report[name]={'source':'individual generated pose' if name in newgen else 'pixel-authored adaptation of approved '+adapt[name],'colors':count,'background_slot':i,'visible_background_pixels_unchanged':int(empty.sum()),'pixel_edits':edits,'approved':False}
sheet.save(OUT/'portrait_sheet/portraits.png');sheet.resize((800,640),Image.Resampling.NEAREST).save(OUT/'review/sheet_x4.png')
contact=Image.new('RGB',(40*8,40*2),(20,30,40))
for j,n in enumerate(required):contact.paste(Image.open(OUT/'portraits_individual'/f'{n}.png').convert('RGB'),(j%8*40,j//8*40))
contact.resize((960,240),Image.Resampling.NEAREST).save(OUT/'review/expressions_x3.png')
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'));import validate
result=validate.run('portrait',OUT/'portrait_sheet/portraits.png','full');assert result['technical_precheck']=='PASS'
(OUT/'review/validation.json').write_text(json.dumps({'full':result,'portraits':report,'approved_existing_preserved':True,'new_portraits_status':'art review candidates, not covered by earlier user approval'},indent=2)+'\n')
print('16 emotions: full technical PASS; six approved/original PNG files preserved.')
