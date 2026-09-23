from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_layers_v2_reverie'
assert Image.open(OUT/'layers/00_fond_canonique_sans_motifs.png').size==(1008,672)
assert Image.open(OUT/'layers/01_continents_et_lieux_reverie_simple.png').size==(1008,672)
assert Image.open(OUT/'WorldMap_7Continents_ReverieSimple.png').size==(1008,672)
s=json.loads((OUT/'world_map_state.json').read_text());assert s['departure_place']=='Reverie Town'
m=json.loads((OUT/'manifest.json').read_text())
for r,i in m['files'].items():
 if r=='manifest.json':continue
 p=OUT/r;assert p.exists();assert hashlib.sha256(p.read_bytes()).hexdigest()==i['sha256']
print('PASS Reverie simple: 2 layers, small organic motif, manifest SHA')
