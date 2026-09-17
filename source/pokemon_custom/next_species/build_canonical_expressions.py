"""Anatomy-locked expression candidates on exact canonical emotion backgrounds.
Generated facial acting is constrained to native landmarks. Approved portraits are copied,
never reconstructed. No user/runtime approval is inferred from mechanical assertions.
"""
from pathlib import Path
import sys, json, hashlib, shutil, base64
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).parent))
from portrait_identity import constrained_expression, PROFILES, ROOT, SRC

OUT=ROOT/'exports/pokemon_custom/canonical_expressions_v1'
GALLERY=ROOT/'apercu_expressions_canoniques_v1.html'
CONTRACT=json.loads((ROOT/'source/pmd_character_pipeline/contract.json').read_text())
BG=Image.open(ROOT/'template.png').convert('RGBA')
OLD=ROOT/'exports/pokemon_custom/tirtouga_portraits_v3'
CONFIG={
 'mega_raichu_x':{'normal':SRC/'references/mega_raichu_x/Normal.png','bg':[(119,199,215),(178,221,201),(239,255,200)],'mouth':(16,27,30,31),'mouth_palette':[(59,53,59),(175,119,71),(183,143,71),(223,167,71),(255,215,79),(255,239,111)],'emotions':['Happy','Angry','Sad','Surprised','Pain']},
 'mega_raichu_y':{'normal':SRC/'references/mega_raichu_y/Normal.png','bg':[(125,200,213),(193,223,184),(234,242,186)],'mouth':(15,22,29,27),'mouth_palette':[(71,47,24),(107,84,52),(185,122,44),(247,151,47),(255,179,61),(255,214,138)],'emotions':['Happy','Angry','Sad','Surprised','Pain']},
 'tirtouga':{'normal':OLD/'portraits_individual/Normal.png','bg':[(118,198,214),(177,220,201),(238,254,200)],'emotions':['Pain','Worried']},
}
TIRT_PROFILE={'editable':[(11,17,19,29)],'protected':[(19,0,40,40)]}

def quantize(im,palette):
 a=np.array(im.convert('RGB')).astype(np.int32);p=np.array(palette,dtype=np.int32)
 ids=np.argmin(((a[:,:,None,:]-p[None,None,:,:])**2).sum(axis=3),axis=2)
 return Image.fromarray(p[ids].astype(np.uint8))

def source_file(name,emotion):
 if name=='tirtouga':return SRC/'generation'/f'tirtouga_{emotion}_locked_v1.png'
 if emotion=='Happy':return SRC/'generation'/f'{name}_happy_locked_v1.png'
 if emotion=='Pain':return SRC/'generation'/f'{name}_Pain_animal_v3.png'
 return SRC/'generation'/f'{name}_{emotion}_locked_v2.png'

def build():
 OUT.mkdir(parents=True,exist_ok=True);report={'status':'generated and constrained candidates, not art-approved or PMDO-tested','subjects':{}}
 template_sha=hashlib.sha256((ROOT/'template.png').read_bytes()).hexdigest()
 rows=[]
 for name,cfg in CONFIG.items():
  folder=OUT/name
  for part in ['portraits_individual','editable','review']:(folder/part).mkdir(parents=True,exist_ok=True)
  normal=Image.open(cfg['normal']).convert('RGBA');a=np.array(normal)
  bgmask=np.zeros((40,40),bool)
  for color in cfg['bg']:bgmask|=np.all(a[:,:,:3]==color,axis=2)
  fg=~bgmask;palette=np.unique(a[fg,:3],axis=0)
  profile=TIRT_PROFILE if name=='tirtouga' else PROFILES[name]
  entries={}
  keep={'Normal.png':hashlib.sha256(cfg['normal'].read_bytes()).hexdigest()}
  if name=='tirtouga':keep=json.loads((ROOT/'source/pokemon_custom/tirtouga_portraits_v3/approval.json').read_text())['sha256']
  for file,digest in keep.items():
   src=OLD/'portraits_individual'/file if name=='tirtouga' else cfg['normal']
   assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
   shutil.copyfile(src,folder/'portraits_individual'/file)
   entries[Path(file).stem]={'preserved_original':True,'sha256':digest}
  for emotion in cfg['emotions']:
   src=source_file(name,emotion);proposal=Image.open(src).resize((40,40),Image.Resampling.NEAREST)
   proposal=quantize(proposal,palette)
   draft,mask=constrained_expression(normal,proposal,profile)
   d=np.array(draft)
   if 'mouth' in cfg:
    x1,y1,x2,y2=cfg['mouth'];area=draft.crop((x1,y1,x2,y2))
    mapped=np.array(quantize(area,cfg['mouth_palette']))
    allowed=mask[y1:y2,x1:x2]
    d[y1:y2,x1:x2,:3][allowed]=mapped[allowed]
   assert np.array_equal(d[fg & ~mask],a[fg & ~mask]),(name,emotion,'anatomy changed outside expression')
   assert np.any(d!=a),(name,emotion,'not a new expression')
   d[:,:,3]=np.uint8(fg)*255;d[~fg]=0
   subject=Image.fromarray(d)
   idx=CONTRACT['portrait']['emotions'].index(emotion)
   bg=BG.crop((idx%5*40,idx//5*40,idx%5*40+40,idx//5*40+40))
   final=bg.copy();final.alpha_composite(subject)
   colors=len(final.getcolors(10000));palette_changes=[]
   # Never hide a >15-color issue by silently recoloring immutable facial pixels.
   technical='PASS' if colors<=15 else 'BLOCKED_PALETTE_BUDGET'
   destination='portraits_individual' if technical=='PASS' else 'review'
   if technical!='PASS':(folder/'portraits_individual'/f'{emotion}.png').unlink(missing_ok=True)
   final.save(folder/destination/f'{emotion}.png')
   subject.save(folder/'editable'/f'{emotion}_subject.png');bg.save(folder/'editable'/f'{emotion}_canonical_background.png')
   assert np.array_equal(np.array(final)[~fg],np.array(bg)[~fg])
   assert np.all(np.array(final)[:,:,3]==255)
   entries[emotion]={'source':str(src.relative_to(ROOT)),'technical_status':technical,'colors':colors,'outside_expression_subject_pixels_changed':0,'canonical_background_slot':idx,'visible_background_pixels_preserved':int(bgmask.sum()),'art_approval':False,'mouth_policy':'No human lips, lip-biting or visible teeth; restricted mouth palette' if name!='tirtouga' else 'Entire beak and nostril untouched; expression uses visible eye only'}
  # Export only supplied cells; missing emotions remain transparent and explicitly pending.
  sheet=Image.new('RGBA',(200,160))
  for emotion in CONTRACT['portrait']['emotions']:
   p=folder/'portraits_individual'/f'{emotion}.png'
   if p.exists():
    idx=CONTRACT['portrait']['emotions'].index(emotion);sheet.paste(Image.open(p),(idx%5*40,idx//5*40))
  sheet.save(folder/'portraits_partial.png')
  order=CONTRACT['portrait']['required_full'] if cfg.get('show_preserved') else ['Normal']+cfg['emotions']
  columns=4 if cfg.get('show_preserved') else len(order)
  contact=Image.new('RGB',(columns*160,((len(order)+columns-1)//columns)*198),(20,29,43));draw=ImageDraw.Draw(contact)
  for i,emotion in enumerate(order):
   p=folder/'portraits_individual'/f'{emotion}.png'
   if not p.exists():p=folder/'review'/f'{emotion}.png'
   ox=i%columns*160;oy=i//columns*198
   contact.paste(Image.open(p).resize((160,160),Image.Resampling.NEAREST),(ox,oy+24))
   label=emotion+(' [conserve]' if entries[emotion].get('preserved_original') else '')+(' [16c / revue]' if entries[emotion].get('technical_status')=='BLOCKED_PALETTE_BUDGET' else '')
   draw.text((ox+6,oy+6),label,fill='white')
  contact.save(folder/'review/expressions_x4.png');rows.append((name,folder/'review/expressions_x4.png'))
  report['subjects'][name]={'expressions':entries,'missing_required':[e for e in CONTRACT['portrait']['required_full'] if not (folder/'portraits_individual'/f'{e}.png').exists()],'normal_sha256':keep['Normal.png'],'face_mask':profile,'background_colors_removed':cfg['bg']}
 assert hashlib.sha256((ROOT/'template.png').read_bytes()).hexdigest()==template_sha
 report['canonical_template_sha256']=template_sha
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Expressions anatomiques • fonds canoniques</title><style>body{background:#141d2b;color:#edf5fa;max-width:1100px;margin:32px auto;padding:0 20px;font:16px system-ui}p{line-height:1.6;color:#b9ccda}img{max-width:100%;image-rendering:pixelated}section{margin:30px 0;padding:20px;background:#1c293b;border-radius:12px}small{color:#e9c482}</style><h1>Expressions naturelles, anatomie conservée</h1><p>Raichu : ni lèvres humaines, ni mordillement, ni dents visibles. Carapagos : bec et narine intacts, expression portée par l’œil. Fonds des nouvelles expressions extraits de leur case exacte dans template.png.</p><p>Ce lot est partiel. Les Normal natifs et les six portraits déjà approuvés de Carapagos sont conservés à l’identique. Les nouvelles expressions sont des propositions, pas une validation artistique ou en jeu.</p>'''
 for name,p in rows:
  html+='<section><h2>'+name+'</h2><img alt="Comparaison des expressions" src="data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()+'"><p>Manquants dans ce lot : '+', '.join(report['subjects'][name]['missing_required'])+'</p></section>'
 html+='<small>La préservation des pixels hors zones d’expression et des fonds est testée ; la justesse anatomique de l’expression elle-même exige une revue visuelle. Voir exports/pokemon_custom/canonical_expressions_v1/verification.json.</small></html>'
 GALLERY.write_text(html)
 print(json.dumps({n:{e:v.get('technical_status','ORIGINAL_PRESERVED') for e,v in r['expressions'].items()} for n,r in report['subjects'].items()},indent=2))

if __name__=='__main__':build()
