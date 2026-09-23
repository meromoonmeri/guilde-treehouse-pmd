from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_9_continents_v1';LAY=OUT/'layers';FOND=ROOT/'source/user_committed_map_background.png';RAW=ROOT/'source/world_map_9_continents_v1/raws/continents_9_sur_fond.png'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
source_background=Image.open(FOND);base=source_background.convert('RGBA');raw=Image.open(RAW).convert('RGBA').resize(base.size,Image.Resampling.NEAREST)
a=np.array(raw);sample=a[4,4,:3].astype(int);dist=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(dist<26,0,a[:,:,3]);fg=Image.fromarray(a)
shutil.copy2(FOND, LAY/'00_fond_committe_image.png');fg.save(LAY/'01_continents_iles_lieux.png');full=base.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_9_Continents_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'source_background':'source/user_committed_map_background.png','layers':['layers/00_fond_committe_image.png','layers/01_continents_iles_lieux.png'],'continents':9,'elements':['small islands','floating islands','spatial rift','varied biomes']}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'source_background':'source/user_committed_map_background.png','files':files},ensure_ascii=False,indent=2))
print('placed 9-continent foreground on user committed background',base.size)
