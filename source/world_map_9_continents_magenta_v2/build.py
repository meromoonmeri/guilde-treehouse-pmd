from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/world_map_9_continents_magenta_v2'; LAY=OUT/'layers'
FOND=ROOT/'source/user_committed_map_background.png'
RAW=ROOT/'source/world_map_9_continents_magenta_v2/raws/continents_9_iles_10_magenta.png'
if OUT.exists(): shutil.rmtree(OUT)
LAY.mkdir(parents=True)
# Preserve the user's map background byte-for-byte.
shutil.copy2(FOND, LAY/'00_fond_utilisateur_original.png')
base=Image.open(FOND).convert('RGBA')
raw=Image.open(RAW).convert('RGBA').resize(base.size,Image.Resampling.LANCZOS)
a=np.array(raw).astype(np.int16)
# Remove only the uniform hot-magenta production background, including antialias fringe.
key=a[0,0,:3].copy()  # exact chroma sampled from the generated magenta field
dist=np.sqrt(((a[:,:,:3]-key)**2).sum(axis=2))
alpha=np.clip((dist-35)*5,0,255).astype(np.uint8)
a[:,:,3]=np.minimum(a[:,:,3].astype(np.uint8),alpha)
fg=Image.fromarray(a.astype(np.uint8),'RGBA')
fg.save(LAY/'01_9_continents_10_iles.png')
full=base.copy(); full.alpha_composite(fg); full.save(OUT/'WorldMap_9_Continents_10_Iles_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'source_background':'source/user_committed_map_background.png','source_magenta_foreground':'source/world_map_9_continents_magenta_v2/raws/continents_9_iles_10_magenta.png','layers':['layers/00_fond_utilisateur_original.png','layers/01_9_continents_10_iles.png'],'continents':9,'small_islands':10,'chromakey':'hot magenta removed from foreground','elements':['snow','ruins','forest','volcano','desert','lakes','swamp','sakura tropical','mushrooms']}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
    if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':9,'small_islands':10,'source_background':'source/user_committed_map_background.png','files':files},ensure_ascii=False,indent=2))
print('composed 9 continents + 10 islands on exact user background',base.size)
