from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path('/home/user/guilde-treehouse-pmd'); OUT=ROOT/'renders/world_map_8_continents_reverie_generator_v3'; LAY=OUT/'layers'
FOND=ROOT/'source/generator_v3/background.png'; REF8=ROOT/'source/generator_v3/ref8.jpeg'; GEN=ROOT/'source/generator_v3/foreground_magenta_corrected.png'
if OUT.exists(): shutil.rmtree(OUT)
LAY.mkdir(parents=True)
shutil.copy2(FOND,LAY/'00_fond_utilisateur_original.png'); base=Image.open(FOND).convert('RGBA')
def key(im,thr=14,keycolor=None):
 a=np.array(im.convert('RGBA')).astype(np.int32); k=np.array(keycolor if keycolor is not None else a[0,0,:3],dtype=np.int32); d=np.sqrt(((a[:,:,:3]-k)**2).sum(axis=2)); a[:,:,3]=np.clip((d-thr)*14,0,255).astype(np.uint8); return Image.fromarray(a.astype(np.uint8),'RGBA')
fg=key(Image.open(REF8).resize(base.size,Image.Resampling.LANCZOS))
# Generated Reverie Town landmark, isolated as a compact island in the open center sea.
t=Image.open(GEN).crop((610,175,900,465)).resize((92,92),Image.Resampling.LANCZOS); t=key(t,80,keycolor=Image.open(GEN).getpixel((0,0))[:3]); fg.alpha_composite(t,(232,136))
fg.save(LAY/'01_8_continents_reverie_town_generated.png'); full=base.copy(); full.alpha_composite(fg); full.save(OUT/'WorldMap_8_Continents_ReverieTown_Generated_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'sources':['source/generator_v3/ref8.jpeg','source/generator_v3/foreground_magenta_corrected.png'],'layers':['layers/00_fond_utilisateur_original.png','layers/01_8_continents_reverie_town_generated.png'],'continents':8,'landmark':'generated Reverie Town tree isolated on its own small island','art_direction':'PMD-inspired pixel-art/parchment generator correction'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)); files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':8,'files':files},ensure_ascii=False,indent=2))
