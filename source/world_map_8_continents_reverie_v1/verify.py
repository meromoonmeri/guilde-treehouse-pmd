from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_8_continents_reverie_v1'; size=Image.open(ROOT/'source/user_committed_map_background.png').size
assert Image.open(OUT/'WorldMap_8_Continents_ReverieTown_UserBackground.png').size==size
assert Image.open(OUT/'layers/00_fond_utilisateur_original.png').size==size
assert Image.open(OUT/'layers/01_8_continents_reverie_town.png').size==size
s=json.loads((OUT/'world_map_state.json').read_text()); assert s['continents']==8 and 'Reverie' in s['landmark']
m=json.loads((OUT/'manifest.json').read_text())
for r,i in m['files'].items():
 if r=='manifest.json': continue
 p=OUT/r; assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==i['sha256']
print('PASS 8 separated continents + Reverie Town tree + exact user background + 2 layers')
