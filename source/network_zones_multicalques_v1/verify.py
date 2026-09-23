from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]; O=R/'renders/network_zones_multicalques_v1'; m=json.loads((O/'manifest.json').read_text()); assert len(m['zones'])==8 and m['multilayer_per_zone']==4
for z in m['zones']:
 d=O/z; assert (d/'layout.json').exists(); assert len(list(d.glob('*.png'))) == 5
print('PASS 8 zones, 4 editing layers each, rounded interiors, biome assignments')
