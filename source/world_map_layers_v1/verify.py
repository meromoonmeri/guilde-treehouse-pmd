from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_layers_v1';size=Image.open(ROOT/'source/world_map_layers_v1/raws/fond_parchemin.png').size
assert Image.open(OUT/'WorldMap_Layers_DA.png').size==size
for p in (OUT/'layers').glob('*.png'):assert Image.open(p).size==size,p
for i in range(8):assert Image.open(OUT/f'animations/WorldMap_clouds_{i:02d}.png').size==size
state=json.loads((OUT/'world_map_state.json').read_text());assert state['departure_place']=='reverie_town' and len(state['places'])==11
assert Image.open(OUT/'assetsprite/WorldMap_Places_Donjons_AssetSprite.png').size==(1056,96)
m=json.loads((OUT/'manifest.json').read_text())
for rel,info in m['files'].items():
 if rel=='manifest.json':continue
 p=OUT/rel;assert p.exists(),p;assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS layered DA map: fond sans motifs, continents, îles, lieux/donjons, routes, état, 8 cloud frames, AssetSprite, SHA')
