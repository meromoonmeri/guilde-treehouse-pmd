from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_layers_v2'
assert Image.open(OUT/'layers/00_fond_canonique_sans_motifs.png').size==(1008,672)
assert Image.open(OUT/'layers/01_continents_et_lieux_dessines.png').size==(1008,672)
assert Image.open(OUT/'WorldMap_7Continents_DA_Strict.png').size==(1008,672)
state=json.loads((OUT/'world_map_state.json').read_text());assert state['layers'] and len(state['layers'])==2
m=json.loads((OUT/'manifest.json').read_text())
for rel,info in m['files'].items():
 if rel=='manifest.json':continue
 p=OUT/rel;assert p.exists(),p;assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS strict DA map: fond canonique sans motifs + foreground continents/lieux, 2 layers, SHA')
