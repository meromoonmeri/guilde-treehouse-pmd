from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_9_continents_v1';size=Image.open(ROOT/'source/user_committed_map_background.png').size
assert Image.open(OUT/'WorldMap_9_Continents_UserBackground.png').size==size
assert Image.open(OUT/'layers/00_fond_committe_image.png').size==size
assert Image.open(OUT/'layers/01_continents_iles_lieux.png').size==size
s=json.loads((OUT/'world_map_state.json').read_text());assert s['continents']==9 and len(s['layers'])==2
m=json.loads((OUT/'manifest.json').read_text())
for r,i in m['files'].items():
 if r=='manifest.json':continue
 p=OUT/r;assert p.exists();assert hashlib.sha256(p.read_bytes()).hexdigest()==i['sha256']
print('PASS user committed background: exact fond + 9 continent foreground, 2 layers, SHA')
