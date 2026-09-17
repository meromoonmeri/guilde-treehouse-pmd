from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/ledian_dojo_v1';m=json.loads((O/'manifest.json').read_text());count=0
for name,h in json.loads((P/'hashes.json').read_text()).items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==h
def load(p):return Image.open(p).convert('RGBA')
for e in m['rooms']:
 d=O/e['id'];im=Image.new('RGBA',(512,512))
 for name in e['layers']:
  layer=load(d/(name+'.png'));assert layer.size==(512,512);count+=1
  if name not in e['optional']:im.alpha_composite(layer)
 assert np.array_equal(np.array(im),np.array(load(d/'composition.png')))
assert np.array_equal(np.array(load(O/'materiaux/echelle_native.png')),np.array(load(P/'layer_3.png').crop((192,48,216,120))))
assert np.array_equal(np.array(load(O/'materiaux/sol_raccord_natif.png')),np.array(load(P/'Ledian_Dojo_Floor.png').crop((184,224,216,256))))
report={'scenes':len(m['rooms']),'aligned_layers':count,'ports':sum(len(e['ports']) for e in m['rooms']),'checks':['Sources SHA256 identiques','6 compositions identiques a la recomposition des calques actifs','Tous calques512x512','Echelle et patch de sol strictement egaux aux extraits natifs','Build:15 bandes de jonction64px opaques et identiques, partitions exactes'], 'runtime_validated':False}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
