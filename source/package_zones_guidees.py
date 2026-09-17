"""Build the offline viewer and portable art pack after build + verification."""
from pathlib import Path
from PIL import Image
import json,base64,io,zipfile
R=Path(__file__).resolve().parents[1];O=R/'sprites/zones_guidees';m=json.loads((O/'provenance.json').read_text())
assert json.loads((O/'verification.json').read_text())['status']=='PASS'
def png(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
def guide(path):
    # Lossy lightweight preview ONLY for the noncanonical proposal. Original generated PNG is preserved.
    b=io.BytesIO();Image.open(path).convert('RGB').save(b,format='JPEG',quality=90);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
data=[]
for z in m['zones']:
    p=O/z['id'];data.append({'id':z['id'],'guide':guide(R/z['guide']),'dry':png(p/'canonique_sec.png'),'banks':png(p/'berges.png'),'water':[png(p/f'eau_{f}.png') for f in range(1,5)]})
template=(R/'source/zones_guidees/viewer.html').read_text();html=template.replace('__DATA__',json.dumps(data)).replace('9 731',f"{m['atlas']['used']:,}".replace(',',' '));viewer=R/'apercu_zones_guidees.html';viewer.write_text(html)
with zipfile.ZipFile(R/'zones_guidees_metano_pack.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(R))
    z.write(viewer,viewer.name)
print('Viewer MiB:',round(viewer.stat().st_size/1048576,2));print('Pack MiB:',round((R/'zones_guidees_metano_pack.zip').stat().st_size/1048576,2))
