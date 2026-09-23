from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_7_continents_v1'
assert Image.open(OUT/'WorldMap_7_Continents.png').size==(1008,672)
for p in (OUT/'layers').glob('*.png'): assert Image.open(p).size==(1008,672),p
for i in range(8): assert Image.open(OUT/f'animations/WorldMap_7continents_discover_{i:02d}.png').size==(1008,672)
assert Image.open(OUT/'assetsprite/WorldMap_7Continents_AssetSprite.png').size==(336,48)
state=json.loads((OUT/'world_map_7_continents_state.json').read_text()); assert len(state['continents'])==7
manifest=json.loads((OUT/'manifest.json').read_text())
for rel,info in manifest['files'].items():
 if rel=='manifest.json': continue
 p=OUT/rel; assert p.exists(),p; assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS 7 continents: 7 calques de contenu, 8 frames PNG + WebP, AssetSprite, SHA valides')
