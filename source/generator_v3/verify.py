from pathlib import Path
import json,hashlib
from PIL import Image
R=Path('/home/user/guilde-treehouse-pmd'); O=R/'renders/world_map_8_continents_reverie_generator_v3'; s=Image.open(R/'source/generator_v3/background.png').size
assert Image.open(O/'WorldMap_8_Continents_ReverieTown_Generated_UserBackground.png').size==s
assert Image.open(O/'layers/00_fond_utilisateur_original.png').size==s
assert Image.open(O/'layers/01_8_continents_reverie_town_generated.png').size==s
st=json.loads((O/'world_map_state.json').read_text()); assert st['continents']==8
m=json.loads((O/'manifest.json').read_text())
for p,i in m['files'].items():
 if p!='manifest.json': assert hashlib.sha256((O/p).read_bytes()).hexdigest()==i['sha256']
print('PASS generated correction: 8 continents, isolated Reverie Town, exact background, 2 layers')
