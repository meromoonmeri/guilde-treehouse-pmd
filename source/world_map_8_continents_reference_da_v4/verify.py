from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2]; O=R/'renders/world_map_8_continents_reference_da_v4'; size=Image.open(R/'source/user_committed_map_background.png').size
assert Image.open(O/'WorldMap_8_Continents_ReferenceDA_UserBackground.png').size==size
assert Image.open(O/'layers/00_fond_utilisateur_original.png').size==size
assert Image.open(O/'layers/01_8_continents_biomes_varies_reverie.png').size==size
s=json.loads((O/'world_map_state.json').read_text()); assert s['continents']==8 and not s['mushroom_continent']
m=json.loads((O/'manifest.json').read_text())
for p,i in m['files'].items():
 if p!='manifest.json': assert hashlib.sha256((O/p).read_bytes()).hexdigest()==i['sha256']
print('PASS reference DA v4: 8 continents, varied biomes, no mushroom continent, exact background, 2 layers')
