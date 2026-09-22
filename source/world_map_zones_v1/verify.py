from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2]/'renders/world_map_zones_v1'
assert Image.open(R/'WorldMap_Zones.png').size==(2048,1536)
assert len(list((R/'layers').glob('*.png')))==7
assert len(list((R/'animations').glob('WorldMap_discover_*.png')))==8
assert Image.open(R/'assetsprite/WorldMap_Lieux_AssetSprite.png').size==(896,128)
m=json.loads((R/'manifest.json').read_text())
for rel,info in m['files'].items():
 if rel=='manifest.json': continue
 p=R/rel;assert p.exists(),p;assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'],rel
print('PASS: grande carte 2048x1536, 7 calques, 8 frames PNG + WebP, AssetSprite et SHA valides')
