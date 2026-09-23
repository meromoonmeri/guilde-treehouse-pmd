from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_9_continents_v1';RAW=ROOT/'source/world_map_9_continents_v1/raws/continents_9_sur_fond.png';FOND=ROOT/'source/world_map_9_continents_fond_orange.png';LAY=OUT/'layers'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
base=Image.open(FOND).convert('RGBA');fg_raw=Image.open(RAW).convert('RGBA');a=np.array(fg_raw);sample=a[4,4,:3].astype(int);dist=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(dist<26,0,a[:,:,3]);fg=Image.fromarray(a);base.save(LAY/'00_fond_parchemin_canonique.png');fg.save(LAY/'01_9_continents_iles_et_lieux.png');full=base.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_9_Continents_Orange.png')
state={'format':'WorldMap9ContinentsTwoLayer','canvas_px':list(base.size),'layers':['layers/00_fond_parchemin_canonique.png','layers/01_9_continents_iles_et_lieux.png'],'continents':9,'elements':['many small islands','floating cloud island','spatial rift','volcanic zone','forest','desert','snow','ruins','mushroom island'],'note':'Fond parchemin déjà canonique; le second calque contient directement les neuf masses et éléments.'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':9,'files':files},ensure_ascii=False,indent=2));print('built 9 continents on existing parchment background')
