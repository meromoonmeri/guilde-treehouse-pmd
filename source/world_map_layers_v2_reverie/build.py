from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_layers_v2_reverie';LAY=OUT/'layers';RAW=ROOT/'source/world_map_layers_v2/raws/reverie_town_simple.png';REF=ROOT/'source/world_map_layers_v2_reverie/refs'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
def key(im,tol=34):
 a=np.array(im.convert('RGBA')); sample=a[4,4,:3].astype(int);d=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(d<tol,0,a[:,:,3]);return Image.fromarray(a)
base=Image.open(REF/'fond.png').convert('RGBA');fg=Image.open(REF/'foreground.png').convert('RGBA')
# Keep the two-layer contract: simple Reverie Town is placed directly onto the foreground layer.
town=key(Image.open(RAW)); town=town.resize((220,145),Image.Resampling.NEAREST)
fg.alpha_composite(town,(95,475));base.save(LAY/'00_fond_canonique_sans_motifs.png');fg.save(LAY/'01_continents_et_lieux_reverie_simple.png')
full=base.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_7Continents_ReverieSimple.png')
state={'format':'WorldMapTwoLayerDA','layers':['layers/00_fond_canonique_sans_motifs.png','layers/01_continents_et_lieux_reverie_simple.png'],'departure_place':'Reverie Town','reverie_town_design':'small organic world-tree village with two waterfalls; simple map motif, no human town block'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'layer_count':2,'raw_motif':str(RAW.relative_to(ROOT)),'files':files},ensure_ascii=False,indent=2))
print('built simple Reverie Town two-layer correction')
