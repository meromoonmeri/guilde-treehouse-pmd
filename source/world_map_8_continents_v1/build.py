from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_8_continents_v1';LAY=OUT/'layers';RAW=ROOT/'source/world_map_8_continents_v1/raws/continents_8_strict.png';REF=ROOT/'source/world_map_8_continents_reference.png'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
fg_raw=Image.open(RAW).convert('RGBA');W,H=fg_raw.size
fond=Image.open(REF).convert('RGBA').resize((W,H),Image.Resampling.NEAREST);fond.save(LAY/'00_fond_canonique_orange.png')
a=np.array(fg_raw);sample=a[4,4,:3].astype(int);dist=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(dist<30,0,a[:,:,3]);fg=Image.fromarray(a);fg.save(LAY/'01_8_continents_et_lieux.png')
full=fond.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_8_Continents_Orange_DA.png')
state={'format':'WorldMap8ContinentsTwoLayer','canvas_px':[W,H],'layers':['layers/00_fond_canonique_orange.png','layers/01_8_continents_et_lieux.png'],'continents':['Volcan','Marais','Sylve','Dunes','Lacs','Aurore','Sakura','Tropiques'],'notes':'Le fond reprend la référence orange canonique; le second calque contient directement les continents et les lieux.'}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':[W,H],'layer_count':2,'continents':8,'generated_foreground':str(RAW.relative_to(ROOT)),'canonical_background':str(REF.relative_to(ROOT)),'files':files},ensure_ascii=False,indent=2))
print('built 8 continents on canonical orange background',W,H)
