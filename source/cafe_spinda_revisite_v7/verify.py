"""Independent pixel/atlas/package checks. Not a PMDO or graphical browser test."""
from pathlib import Path
import sys,json,hashlib,zipfile,io,subprocess
from PIL import Image
import numpy as np
S=Path(__file__).resolve().parent;R=S.parents[1];O=R/'renders/cafe_spinda_revisite_v7';sys.path.insert(0,str(S))
from native import decode
from archive import data,entries

def rgba(p):return Image.open(p).convert('RGBA')
def run():
 audit=json.loads((O/'audit/native_sizes.json').read_text());m=json.loads((O/'manifest.json').read_text());banks={k:decode(R/v['file'])[0] for k,v in audit['sources'].items()};scene=banks['SpindaCafe1'].copy();scene.alpha_composite(banks['SpindaCafe2'])
 assert len(audit['objects'])==30
 for a in audit['objects']:
  im=rgba(O/a['file']);assert list(im.size)==a['size'];assert im.width%8==im.height%8==0;assert a['scale']==1 and a['rotation']==0 and not a['recolour'];assert hashlib.sha256(im.tobytes()).hexdigest()==a['rgba_sha256']
  if isinstance(a['source'],list):
   src=np.array(scene.crop(a['source_rect']));out=np.array(im);mask=out[:,:,3]>0;assert np.array_equal(src[mask],out[mask])
  else:
   src=banks[a['source']].crop(a['source_rect']);assert im.crop((0,0,src.width,src.height)).tobytes()==src.tobytes()
 assets={a['id']:a for a in m['assets']};sheets=json.loads((O/'tilesheets/index.json').read_text())
 assert len(sheets)==4
 for sheet in sheets:
  im=rgba(O/sheet['file']);assert im.width%8==im.height%8==0
  occupied=np.zeros((im.height,im.width),bool)
  for obj in sheet['objects']:
   x,y,w,h=obj['rect'];assert x%8==y%8==w%8==h%8==0;assert not occupied[y:y+h,x:x+w].any();occupied[y:y+h,x:x+w]=True
   assert im.crop((x,y,x+w,y+h)).tobytes()==rgba(O/assets[obj['id']]['file']).tobytes()
 window=rgba(O/'assets/SpindaV7_oculus_32.png');assert window.size==(32,32);b=window.getbbox();assert (b[2]-b[0],b[3]-b[1])==(28,28)
 for rec in entries():assert hashlib.sha256(data(R/rec['path'])).hexdigest()==rec['sha256']
 for name in ['SpindaV7_objets_tilesheets.zip','SpindaV7_complet.zip']:
  with zipfile.ZipFile(O/name) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
 with zipfile.ZipFile(O/'SpindaV7_complet.zip') as z:
  portable=json.loads(z.read('manifest.json'));assert not portable['packed_layers'];seen=set()
  for room in portable['rooms']:
   for l in room['layers']:
    im=rgba(io.BytesIO(z.read(l['file'])));assert im.size==(600,448);assert Path(l['file']).name.startswith('SpindaV7_');assert Path(l['file']).name not in seen;seen.add(Path(l['file']).name)
  for a in portable['assets']:assert z.read(a['file'])==(O/a['file']).read_bytes()
 # Previous V6 deliverables remain exact, not just visually similar.
 for name in ['SpindaV6_pack.zip','manifest.json','index.html','assets/SpindaV6_oculus_cafe.png']:
  path='renders/cafe_spinda_revisite_v6/'+name;assert (R/path).read_bytes()==subprocess.check_output(['git','show','fca5cddf:'+path],cwd=R)
 print('PASS: 30 native extractions, 4 exact 8px atlases, 28px window, 11 archived originals, standalone ZIP dependencies and unchanged V6 deliverables')
if __name__=='__main__':run()
