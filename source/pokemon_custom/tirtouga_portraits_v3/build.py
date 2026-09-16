"""Individual generated portrait sources -> edited pixel portraits + EXACT canonical backgrounds."""
from pathlib import Path
import json,hashlib,shutil,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).parent;OUT=ROOT/'exports/pokemon_custom/tirtouga_portraits_v3'
for n in ['portraits_individual','portrait_sheet','review','editable']:(OUT/n).mkdir(parents=True,exist_ok=True)
slots={'Normal':0,'Happy':1,'Angry':3,'Sad':5,'Shouting':7,'Surprised':12}
normal=ROOT/'source/pokemon_custom/tirtouga_v2/references/Normal.png';template=Image.open(ROOT/'template.png').convert('RGBA')
sheet=Image.new('RGBA',(200,160));reports={};subjects={}
shutil.copyfile(normal,OUT/'portraits_individual/Normal.png');sheet.paste(Image.open(normal).convert('RGBA'),(0,0))
for name,slot in slots.items():
 if name=='Normal':continue
 raw=Image.open(SRC/'generation'/f'{name}.png').convert('RGBA');a=np.array(raw);r,g,b=[a[:,:,i].astype(float) for i in range(3)]
 mask=(r>150)&(b>150)&(g<90)&(r>2*g)&(b>2*g);a[mask]=0
 subject=Image.fromarray(a).resize((40,40),Image.Resampling.NEAREST);a=np.array(subject);a[:,:,3]=np.where(a[:,:,3]>=128,255,0)
 # No bilinear fringe: generator's large pixel clusters are sampled to the 40px drawing grid.
 subject=Image.fromarray(a);box=((slot%5)*40,(slot//5)*40,(slot%5+1)*40,(slot//5+1)*40);bg=template.crop(box)
 assert set(bg.getchannel('A').getdata())=={255}
 bg_colors=set(bg.getdata());budget=15-len(bg_colors)
 assert budget>=8
 # Authored semantic palette: median-cut alone mixed the pink mouth into blue-grey.
 # Reserve eye whites and warm mouth colors explicitly, then map each opaque pixel.
 core=[(38,47,54),(48,58,74),(60,73,92),(76,90,116),(94,113,146),
       (67,106,166),(83,129,202),(116,166,232),(158,200,212),(255,255,255)]
 chosen=core+([(119,61,83),(230,134,150)] if name in ['Happy','Shouting'] else [(119,61,83)] if name=='Surprised' else [])
 assert len(chosen)<=budget
 rgba=np.array(subject);visible=rgba[:,:,3]>0;rgb=rgba[:,:,:3].astype(np.int32)
 palette=np.array(chosen,dtype=np.int32);indices=np.argmin(np.sum((rgb[:,:,None,:]-palette[None,None,:,:])**2,axis=3),axis=2)
 rgba[:,:,:3]=palette[indices];rgba[~visible]=0;subject=Image.fromarray(rgba)
 # Pixel-authored brow corrections after native-size review (not a color filter).
 edits={'Angry':[(14,19,0),(15,20,0),(16,20,0),(17,21,0),(18,21,0)],
        'Sad':[(13,19,0),(14,19,0),(15,20,0)]}.get(name,[])
 for x,y,index in edits:
  if subject.getpixel((x,y))[3]:subject.putpixel((x,y),chosen[index]+(255,))
 subject.save(OUT/'editable'/f'{name}_subject.png');bg.save(OUT/'editable'/f'{name}_canonical_background.png')
 result=bg.copy();result.alpha_composite(subject)
 result.save(OUT/'portraits_individual'/f'{name}.png');sheet.paste(result,((slot%5)*40,(slot//5)*40));subjects[name]=subject
 arr=np.array(result);bgarr=np.array(bg);empty=np.array(subject)[:,:,3]==0
 assert np.array_equal(arr[empty],bgarr[empty]);count=len(set(result.getdata()));assert count<=15
 reports[name]={'size':[40,40],'visible_colors':count,'subject_palette_budget':budget,'canonical_background_colors':len(bg_colors),'canonical_slot':slot,'unchanged_visible_background_pixels':int(empty.sum()),'opaque':True,'authored_subject_palette':chosen,'manual_pixel_edits':edits,'source_sha256':hashlib.sha256((SRC/'generation'/f'{name}.png').read_bytes()).hexdigest()}
sheet.save(OUT/'portrait_sheet/portraits.png');sheet.resize((800,640),Image.Resampling.NEAREST).save(OUT/'review/sheet_x4.png')
contact=Image.new('RGB',(40*len(slots),40),(18,25,39))
for i,name in enumerate(slots):contact.paste(Image.open(OUT/'portraits_individual'/f'{name}.png').convert('RGB'),(40*i,0))
contact.save(OUT/'review/portraits_native.png');contact.resize((240*4,160),Image.Resampling.NEAREST).save(OUT/'review/portraits_x4.png')
# Labeled comparison of old pixel adaptations vs regenerated expressions.
compare=Image.new('RGB',(40*3,80),(18,25,39))
for i,name in enumerate(['Happy','Angry','Sad']):
 compare.paste(Image.open(ROOT/'exports/pokemon_custom/tirtouga_v2/portraits_individual'/f'{name}.png').convert('RGB'),(i*40,0));compare.paste(Image.open(OUT/'portraits_individual'/f'{name}.png').convert('RGB'),(i*40,40))
compare.resize((480,320),Image.Resampling.NEAREST).save(OUT/'review/before_after_x4.png')
assert normal.read_bytes()==(OUT/'portraits_individual/Normal.png').read_bytes()
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'));import validate
report={'portraits':reports,'normal_original_preserved_byte_for_byte':True,'minimum':validate.run('portrait',OUT/'portrait_sheet/portraits.png'),'full':validate.run('portrait',OUT/'portrait_sheet/portraits.png','full'),'artistic_review':'Initial expressions inspected; approval by user/SpriteCollab not obtained','PMDO_runtime':'NOT TESTED'}
(OUT/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
