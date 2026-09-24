from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[2];REF=ROOT/'source/world_map_layers_v2_reference.png';RAW=ROOT/'source/world_map_layers_v2/raws/continents_lieux_strict.png';OUT=ROOT/'renders/world_map_layers_v2';LAY=OUT/'layers'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
base=Image.open(REF).convert('RGBA').resize((1008,672),Image.Resampling.NEAREST)
base.save(LAY/'00_fond_canonique_sans_motifs.png')
raw=Image.open(RAW).convert('RGBA');a=np.array(raw);sample=a[4,4,:3].astype(int);dist=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(dist<34,0,a[:,:,3]);fg=Image.fromarray(a).resize((1008,672),Image.Resampling.NEAREST);fg.save(LAY/'01_continents_et_lieux_dessines.png')
full=base.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_7Continents_DA_Strict.png')
# Engine state: all static art is exactly two layers; future state can swap the foreground.
state={'format':'WorldMapTwoLayerDA','canvas_px':[1008,672],'layers':['layers/00_fond_canonique_sans_motifs.png','layers/01_continents_et_lieux_dessines.png'],'departure_place':'Reverie Town','places':['Reverie Town - arbre monde et cascades','port','sanctuaire sakura','portail des iles volantes','tour en ruine celeste','donjon volcanique','observatoire neige','ruines anciennes','village marais'],'note':'Le fond canonique ne contient aucun motif ajouté; continents et lieux sont dessinés ensemble sur le second calque généré.'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':[1008,672],'layer_count':2,'generated_source':str(RAW.relative_to(ROOT)),'reference_background':str(REF.relative_to(ROOT)),'files':files},ensure_ascii=False,indent=2))
print('built strict two-layer map',base.size)
