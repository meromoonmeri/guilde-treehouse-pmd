"""Prove the lighter repository viewer and re-embedded portable viewer preserve every image."""
from pathlib import Path
import json,base64,io,sys,zipfile,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.beach_layers_v1.package import portable_viewer
P=R/'renders/beach_layers_v1';archive=P/'BeachV1_pack.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(page):return json.JSONDecoder().raw_decode(page.split('const DATA=',1)[1])[0]
def images(d):return [l['uri'] for l in d['layers']]+d['surface']+d['foam']+[d['reference']]
def rgba(uri):
 payload=io.BytesIO(base64.b64decode(uri.split(',',1)[1])) if uri.startswith('data:') else R/uri
 im=Image.open(payload).convert('RGBA');return im.size,im.tobytes()
original_hash=sha(archive)
with zipfile.ZipFile(archive) as z:old=data(z.read('apercu_beach_calques_v1.html').decode())
page=(R/'apercu_beach_calques_v1.html').read_text();current=data(page);portable=data(portable_viewer(page));count=0
for a,b,c in zip(images(old),images(current),images(portable),strict=True):
 assert not b.startswith('data:') and c.startswith('data:image/png;base64,');assert rgba(a)==rgba(b)==rgba(c);count+=1
assert count==138 and sha(archive)==original_hash
report={'pass':True,'images':count,'checks':['repository paths match all 138 old archived embedded images RGBA-exactly','portable_viewer re-embeds all 138 PNGs without changing pixels','existing BeachV1 ZIP byte-identical; no replacement'],'existing_zip_sha256':original_hash}
(P/'verification_compact.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',count,'old ZIP / compact viewer / future portable viewer images exact; existing ZIP unchanged')
