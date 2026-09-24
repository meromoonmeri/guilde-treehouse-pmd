from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_8_continents_reference_da_v4'; LAY=OUT/'layers'; FOND=ROOT/'source/user_committed_map_background.png'; RAW=ROOT/'source/world_map_8_continents_reference_da_v4/raws/foreground_magenta.png'
if OUT.exists(): shutil.rmtree(OUT)
LAY.mkdir(parents=True)
shutil.copy2(FOND,LAY/'00_fond_utilisateur_original.png'); base=Image.open(FOND).convert('RGBA')
r=Image.open(RAW).convert('RGBA').resize(base.size,Image.Resampling.LANCZOS); a=np.array(r).astype(np.int32); key=a[0,0,:3].copy(); dist=np.sqrt(((a[:,:,:3]-key)**2).sum(axis=2)); a[:,:,3]=np.clip((dist-45)*6,0,255).astype(np.uint8); fg=Image.fromarray(a.astype(np.uint8),'RGBA'); fg.save(LAY/'01_8_continents_biomes_varies_reverie.png'); full=base.copy(); full.alpha_composite(fg); full.save(OUT/'WorldMap_8_Continents_ReferenceDA_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'sources':['source/world_map_8_continents_reference.png','source/reverie_town_reference.png','source/world_map_8_continents_reference_da_v4/raws/foreground_magenta.png'],'layers':['layers/00_fond_utilisateur_original.png','layers/01_8_continents_biomes_varies_reverie.png'],'continents':8,'reverie_town':'separate tree island','mushroom_continent':False,'art_direction':'reference files palette, texture and pixel treatment','biomes':['volcano with ash/hot springs','desert with oasis/canyon/dry scrub','mountain with foothills/pine/alpine lake','forest with dry woodland/river/waterfalls','marsh with mangrove/reeds/pools','lake country with rivers/grasslands','tropical-sakura with palms/bamboo/shrine','ancient ruins with dry grass/olive grove/river']}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)); files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':8,'mushroom_continent':False,'files':files},ensure_ascii=False,indent=2))
