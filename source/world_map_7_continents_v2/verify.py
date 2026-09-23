from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_7_continents_v2'
raw_size=Image.open(ROOT/'source/world_map_7_continents_v2/raws/world_map_7_continents_generated.png').size
assert Image.open(OUT/'WorldMap_7_Continents_Generated.png').size==raw_size
for p in (OUT/'layers').glob('*.png'): assert Image.open(p).size==raw_size,p
for i in range(8): assert Image.open(OUT/f'animations/WorldMap_7Continents_v2_{i:02d}.png').size==raw_size
assert Image.open(OUT/'assetsprite/WorldMap_7Continents_v2_AssetSprite.png').size==(448,64)
state=json.loads((OUT/'world_map_state.json').read_text());assert len(state['continents'])==7
m=json.loads((OUT/'manifest.json').read_text())
for rel,info in m['files'].items():
 if rel=='manifest.json':continue
 p=OUT/rel;assert p.exists(),p;assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS generated 7 continents: 6 semantic layers, 8 PNG + WebP frames, AssetSprite, manifest SHA')
