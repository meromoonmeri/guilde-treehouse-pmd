from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_8_continents_reverie_v1'; LAY=OUT/'layers'
FOND=ROOT/'source/user_committed_map_background.png'; REF8=ROOT/'source/latest_references/IMG_4984.jpeg'; TREE=ROOT/'source/latest_references/IMG_4986.jpeg'
if OUT.exists(): shutil.rmtree(OUT)
LAY.mkdir(parents=True)
shutil.copy2(FOND,LAY/'00_fond_utilisateur_original.png')
base=Image.open(FOND).convert('RGBA')
def key_image(im,threshold=14):
    a=np.array(im.convert('RGBA')).astype(np.int16); key=a[0,0,:3].copy(); dist=np.sqrt(((a[:,:,:3]-key)**2).sum(axis=2)); a[:,:,3]=np.clip((dist-threshold)*14,0,255).astype(np.uint8); return Image.fromarray(a.astype(np.uint8),'RGBA')
# The latest IMG_4984 is the eight-continent separated layout, preserved as the main foreground.
fg=key_image(Image.open(REF8).resize(base.size,Image.Resampling.LANCZOS))
# Extract the generated Reverie Town tree landmark from IMG_4986 and place it in a clear sea gap.
t=Image.open(TREE).crop((430,130,700,400)).resize((105,105),Image.Resampling.LANCZOS)
t=key_image(t,threshold=18)
fg.alpha_composite(t,(224,128))
fg.save(LAY/'01_8_continents_reverie_town.png')
full=base.copy(); full.alpha_composite(fg); full.save(OUT/'WorldMap_8_Continents_ReverieTown_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'source_background':'source/user_committed_map_background.png','sources':['source/latest_references/IMG_4984.jpeg','source/latest_references/IMG_4986.jpeg'],'layers':['layers/00_fond_utilisateur_original.png','layers/01_8_continents_reverie_town.png'],'continents':8,'landmark':'Reverie Town tree from IMG_4986.jpeg','art_direction':'latest committed pixel-art/parchment references'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'continents':8,'landmark':'Reverie Town tree','files':files},ensure_ascii=False,indent=2))
print('composed eight separated continents with Reverie Town tree',base.size)
