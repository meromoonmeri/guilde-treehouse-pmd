from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from sample import decode
p=ROOT/'source/falaises_metano';meta=json.loads((p/'provenance.json').read_text());banks=[decode(p/'natifs'/f'Metano_Town_{n}.tile') for n in ['Base','Cliffs']]
base=Image.new('RGBA',(max(x.shape[1] for x in banks),max(x.shape[0] for x in banks)))
for a in banks:base.alpha_composite(Image.fromarray(a))
roles={};checks=[]
for n in ['herbe','roche','rebord','pied']:
 patch=Image.open(p/'patches'/f'{n}.png').convert('RGBA');assert patch.tobytes()==base.crop(meta['patches_from_composed_Base_and_Cliffs_xyxy_px'][n]).tobytes()
 a=np.array(patch);roles[n]=np.unique(a[a[:,:,3]==255,:3],axis=0).tolist();checks.append({'role':n,'source_rect':meta['patches_from_composed_Base_and_Cliffs_xyxy_px'][n],'rgba_equal_to_native_banks':True,'palette_colors':len(roles[n])})
# Dark mauve physically present in the canonical cliff bank, outside the small flat-face patch.
shadow=np.array([96,56,88],dtype=np.uint8);where=np.argwhere((banks[1][:,:,:3]==shadow).all(axis=2)&(banks[1][:,:,3]==255));assert len(where)
roles['ombre_falaise']=[shadow.tolist()];yy,xx=where[0];checks.append({'role':'ombre_falaise','source_bank':'Metano_Town_Cliffs.tile','source_pixel_xy':[int(xx),int(yy)],'native_rgba':[96,56,88,255],'rgb_found_in_native_cliffs':True,'palette_colors':1})
allowed=np.unique(np.concatenate([np.array(v) for v in roles.values()]),axis=0).tolist()
report={'reference_commit':meta['commit'],'reference_repo':meta['reference'],'roles':roles,'allowed_rgb':allowed,'patch_checks':checks,'source_files':[{ 'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [p/'natifs/Metano_Town_Base.tile',p/'natifs/Metano_Town_Cliffs.tile',ROOT/'source/falaises_generees/reference_canonique.png']]}
(HERE/'palette_canonique.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Magnified examples are labelled reference-only; nearest-neighbor, no source recoloring.
im=Image.new('RGB',(1080,432),'#ff00ff');d=ImageDraw.Draw(im)
for n,x,y,scale in [('herbe',8,35,2),('rebord',292,35,4),('roche',568,35,4),('pied',568,280,4)]:
 patch=Image.open(p/'patches'/f'{n}.png').convert('RGBA');patch=patch.resize((patch.width*scale,patch.height*scale),Image.Resampling.NEAREST);im.paste(patch,(x,y),patch);d.text((x,y-22),n+' / native pixels x'+str(scale),fill='black')
d.text((12,385),'REFERENCE MATIERE UNIQUEMENT - ne pas copier les labels ni cette composition',fill='black')
im.save(HERE/'reference_matiere_stricte.png')
print('Native patch equality PASS; allowed colors:',len(allowed))
