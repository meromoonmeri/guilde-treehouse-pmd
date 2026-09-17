"""Keep the user's preferred V1 portraits; update Dizzy and add applause Special0."""
from pathlib import Path
import sys,json,shutil,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).parent
sys.path.insert(0,str(ROOT))
from source.pokemon_custom.politoed_portraits_v1.build import key_magenta,native_subject,NATIVE,C
OLD=ROOT/'exports/pokemon_custom/politoed_portraits_v1'
OUT=ROOT/'exports/pokemon_custom/politoed_portraits_v3'

def main():
 for part in ['portraits_individual','editable','review']:(OUT/part).mkdir(parents=True,exist_ok=True)
 preferred={}
 for p in (OLD/'portraits_individual').glob('*.png'):
  if p.stem=='Dizzy':continue
  shutil.copyfile(p,OUT/'portraits_individual'/p.name);preferred[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 report={'preferred_base':'ac15d0fa / politoed_portraits_v1','preserved_preferred_hashes':preferred,'not_selected':'politoed_portraits_v2 whole-face trials kept as unused studies','new':{},'art_approval_of_additions':False}
 normal=native_subject(Image.open(NATIVE/'Normal.png'))
 for emotion in ['Dizzy','Special0']:
  keyed,_=key_magenta(Image.open(SRC/'generation'/f'{emotion}.png'));keyed.save(OUT/'editable'/f'{emotion}_keyed.png')
  small=keyed.resize((40,40),Image.Resampling.NEAREST)
  if emotion=='Dizzy':
   # Generator drew concentric rings. Make an actual connected inward spiral at native size.
   small=normal.copy();d=ImageDraw.Draw(small)
   d.rectangle((12,11,18,17),fill=(228,243,185,255))
   d.line([(12,11),(18,11),(18,17),(12,17),(12,13),(16,13),(16,15),(14,15)],fill=(65,70,45,255),width=1)
  i=C['portrait']['emotions'].index(emotion);template=Image.open(ROOT/'template.png').convert('RGBA');bg=template.crop((i%5*40,i//5*40,i%5*40+40,i//5*40+40))
  if emotion=='Special0':
   # Optional slot: explicit applause mapping to the warm celebratory rays, not template placeholders.
   bg=Image.open(ROOT/'Extra_Backgrounds.png').convert('RGBA').crop((40,0,80,40))
  a=np.array(small);opaque=a[:,:,3]>127
  if emotion=='Special0':
   # Semantic palette sampled from the guide: retain cheek/tongue pink and yellow jaw.
   # Frequency quantization over-allocates near-identical greens and loses these features.
   palette=np.array([(20,50,25),(75,120,48),(97,162,45),(128,197,70),(169,218,90),(254,222,83),(218,173,65),(223,133,180),(190,90,111),(96,37,10),(139,104,35)],dtype=np.int32)
   rgb=a[:,:,:3].astype(np.int32);indices=np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3),axis=2);a[:,:,:3]=palette[indices]
  a[:,:,3]=np.uint8(opaque)*255;a[~opaque]=0;small=Image.fromarray(a)
  final=bg.copy();final.alpha_composite(small)
  colors=len(final.getcolors(9999));assert colors<=15,(emotion,colors)
  assert np.array_equal(np.array(final)[~opaque],np.array(bg)[~opaque])
  small.save(OUT/'editable'/f'{emotion}_subject.png');bg.save(OUT/'editable'/f'{emotion}_canonical_background.png');final.save(OUT/'portraits_individual'/f'{emotion}.png')
  report['new'][emotion]={'colors':colors,'technical_precheck':'PASS','source':str((SRC/'generation'/f'{emotion}.png').relative_to(ROOT)),'method':'Generated guide plus explicitly pixel-authored connected spiral on preferred native face' if emotion=='Dizzy' else 'Whole generated applause portrait keyed from magenta, reduced and palette-cleaned; no native-face paste','background_slot':i}
 for p,sha in preferred.items():assert hashlib.sha256((OUT/'portraits_individual'/p).read_bytes()).hexdigest()==sha
 sheet=Image.new('RGBA',(200,160));board=Image.new('RGB',(800,198),(20,29,43));d=ImageDraw.Draw(board)
 for emotion in C['portrait']['emotions']:
  p=OUT/'portraits_individual'/f'{emotion}.png'
  if p.exists():
   i=C['portrait']['emotions'].index(emotion);sheet.paste(Image.open(p),(i%5*40,i//5*40))
 for j,emotion in enumerate(['Normal','Dizzy','Special0','Happy','Shouting']):
  board.paste(Image.open(OUT/'portraits_individual'/f'{emotion}.png').resize((160,160),Image.Resampling.NEAREST),(j*160,25));d.text((j*160+5,6),emotion+(' / conserve' if emotion in ['Normal','Happy','Shouting'] else ''),fill='white')
 sheet.save(OUT/'portraits_partial.png');board.save(OUT/'review/changes_x4.png')
 report['missing_required']=[e for e in C['portrait']['required_full'] if not (OUT/'portraits_individual'/f'{e}.png').exists()]
 report['background_mapping']={'Dizzy':{'file':'template.png','slot':13},'Special0':{'file':'Extra_Backgrounds.png','rectangle':[40,0,80,40]}}
 report['runtime_PMDO']='NOT TESTED'
 shutil.copyfile(NATIVE/'credits.txt',OUT/'native_credits.txt')
 sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
 from validate import run
 report['minimum_precheck']=run('portrait',OUT/'portraits_partial.png','minimum')
 report['full_precheck']=run('portrait',OUT/'portraits_partial.png','full')
 assert report['minimum_precheck']['technical_precheck']=='PASS'
 assert report['full_precheck']['errors']==['Missing required emotion: Sigh','Missing required emotion: Stunned']
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Preferred portraits preserved:',len(preferred),'additions:',list(report['new']),'missing:',report['missing_required'])

if __name__=='__main__':main()
