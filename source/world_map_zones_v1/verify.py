from pathlib import Path
import hashlib, json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_zones_v1'
assert Image.open(ROOT/'Explorers_of_Sky_-_World_Map.png').size == (504,336)
assert Image.open(OUT/'layers/00_fond_canonique_1x.png').tobytes() == Image.open(ROOT/'Explorers_of_Sky_-_World_Map.png').convert('RGBA').tobytes()
for p in (OUT/'layers').glob('*.png'): assert Image.open(p).size==(504,336), p
for i in range(12): assert Image.open(OUT/f'animations/WorldMap_discover_{i:02d}.png').size==(504,336)
assert Image.open(OUT/'assetsprite/WorldMap_Lieux_AssetSprite.png').size==(336,48)
data=json.loads((OUT/'assetsprite/WorldMap_Lieux_AssetSprite.json').read_text()); assert data['format']=='AssetSprite' and len(data['entries'])==7
manifest=json.loads((OUT/'manifest.json').read_text())
for rel,info in manifest['files'].items():
 if rel == 'manifest.json': continue
 p=OUT/rel; assert p.exists(),p; assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS world map: fond canonique 1x, 5 calques, 12 frames PNG + WebP, 7 AssetSprite, SHA valides')
