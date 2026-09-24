from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_latest_references_v1'; LAY=OUT/'layers'
FOND=ROOT/'source/user_committed_map_background.png'; REF=ROOT/'source/latest_references/IMG_4984.jpeg'; OLD=ROOT/'renders/world_map_9_continents_v1/layers/01_continents_iles_lieux.png'
if OUT.exists(): shutil.rmtree(OUT)
LAY.mkdir(parents=True)
shutil.copy2(FOND,LAY/'00_fond_utilisateur_original.png')
base=Image.open(FOND).convert('RGBA')
# IMG_4984 is the latest separated-continent reference and has nearly the same aspect ratio.
r=Image.open(REF).convert('RGBA').resize(base.size,Image.Resampling.LANCZOS)
a=np.array(r).astype(np.int16); key=a[0,0,:3].copy(); dist=np.sqrt(((a[:,:,:3]-key)**2).sum(axis=2)); a[:,:,3]=np.clip((dist-12)*12,0,255).astype(np.uint8)
fg=Image.fromarray(a.astype(np.uint8),'RGBA')
# Add a ninth compact ruins continent from the prior pixel-art reference, without touching the user background.
old=Image.open(OLD).convert('RGBA').crop((270,292,390,366)).resize((76,47),Image.Resampling.NEAREST)
# clear its old parchment pixels by keeping only non-background pixels
b=np.array(old); d=np.sqrt(((b[:,:,:3].astype(np.int16)-np.array([230,157,73]))**2).sum(axis=2)); b[:,:,3]=np.minimum(b[:,:,3],np.clip((d-20)*10,0,255).astype(np.uint8)); old=Image.fromarray(b)
fg.alpha_composite(old,(242,78))
fg.save(LAY/'01_references_9_continents_10_iles.png')
full=base.copy(); full.alpha_composite(fg); full.save(OUT/'WorldMap_9_Continents_References_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'source_background':'source/user_committed_map_background.png','references':['source/latest_references/IMG_4984.jpeg','source/latest_references/IMG_4985.jpeg','source/latest_references/IMG_4986.jpeg'],'layers':['layers/00_fond_utilisateur_original.png','layers/01_references_9_continents_10_iles.png'],'continents':9,'small_islands':10,'art_direction':'latest committed pixel-art references; IMG_4984 separated continents, IMG_4985 cloud language, IMG_4986 composition language'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':9,'small_islands':10,'files':files},ensure_ascii=False,indent=2))
print('arranged latest references on user background',base.size)
