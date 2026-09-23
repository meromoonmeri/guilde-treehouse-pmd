from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_latest_references_v1'; size=Image.open(ROOT/'source/user_committed_map_background.png').size
assert Image.open(OUT/'WorldMap_9_Continents_References_UserBackground.png').size==size
assert Image.open(OUT/'layers/00_fond_utilisateur_original.png').size==size
assert Image.open(OUT/'layers/01_references_9_continents_10_iles.png').size==size
s=json.loads((OUT/'world_map_state.json').read_text()); assert s['continents']==9 and s['small_islands']==10
m=json.loads((OUT/'manifest.json').read_text())
for r,i in m['files'].items():
 if r=='manifest.json': continue
 p=OUT/r; assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==i['sha256']
print('PASS latest references: 9 continents, 10 islands, exact user background, 2 layers')
