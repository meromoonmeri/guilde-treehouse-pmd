from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent/'references';O.mkdir(exist_ok=True);refs=json.loads((R/'source/zones_pmd_20_v1/references/sources.json').read_text());config=[]
for name,idx in [('cote',13),('cristal',10),('foret',12),('sables',9)]:
 ref=next(x for x in refs if x['id']==idx);source=R/ref['source'];im=Image.open(source);frames=[];dur=[]
 for fi in range(getattr(im,'n_frames',1)):im.seek(fi);frames.append(np.array(im.convert('RGBA')));dur.append(im.info.get('duration',100))
 a=frames[0];h,w=a.shape[:2];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);anim=np.zeros((h,w),bool)
 for frame in frames[1:]:anim|=np.any(frame!=a,axis=2)
 if name=='cote':fluid=(b>r*1.2)&(b>g*1.03)
 elif name=='cristal':
  p=Image.new('L',(w,h));ImageDraw.Draw(p).polygon([(int(x*w),int(y*h)) for x,y in [(.39,0),(.60,0),(.60,.23),(.70,.45),(.6,.62),(.65,.84),(.59,1),(.35,1),(.35,.81),(.40,.62),(.25,.45),(.39,.25)]],fill=255);fluid=np.array(p)==0
 else:fluid=np.zeros((h,w),bool)
 preserve=nd.binary_fill_holes(fluid|anim);Image.fromarray(a).save(O/(name+'_reference.png'));cut=a.copy();cut[preserve]=[255,0,255,255];Image.fromarray(cut).save(O/(name+'_magenta.png'));Image.fromarray(preserve.astype('uint8')*255).save(O/(name+'_preserve.png'));config.append({'id':name,'reference_index':idx,'source':ref['source'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'size':[w,h],'frames':len(frames),'durations_ms':dur,'protected_pixels':int(preserve.sum())})
(O/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
