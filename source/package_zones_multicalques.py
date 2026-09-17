"""Self-contained guild-style layer viewer. Existing archives are left untouched."""
from pathlib import Path
import json,base64
R=Path(__file__).resolve().parents[1];O=R/'sprites/zones_guidees';M=json.loads((O/'multicalques.json').read_text())
assert json.loads((O/'verification_multicalques.json').read_text())['status']=='PASS'
data=[]
for z in M['zones']:
    root=R/z['directory'];layers=[]
    for l in M['layers']:layers.append(['data:image/png;base64,'+base64.b64encode((root/f).read_bytes()).decode() for f in z['files'][l['id']]])
    data.append({'id':z['id'],'name':z['name'],'layers':layers})
s=(R/'source/zones_guidees/viewer_multicalques.html').read_text().replace('__DATA__',json.dumps(data)).replace('__LABELS__',json.dumps([l['name'] for l in M['layers']],ensure_ascii=False))
p=R/'apercu_zones_multicalques.html';p.write_text(s);print('Offline layer viewer MiB:',round(p.stat().st_size/1048576,2))
