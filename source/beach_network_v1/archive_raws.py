"""Losslessly archive large generation PNGs; delivered scenes/ZIPs are untouched."""
from pathlib import Path
import hashlib,json
from PIL import Image
P=Path(__file__).resolve().parents[2]/'renders/beach_network_v1/bruts'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def archive():
 report=P/'archive_lossless.json';records=json.loads(report.read_text()) if report.exists() else []
 for p in sorted(P.glob('0*.png')):
  im=Image.open(p).convert('RGBA');q=p.with_suffix('.webp');im.save(q,lossless=True,exact=True,method=6)
  assert Image.open(q).convert('RGBA').tobytes()==im.tobytes()
  records.append({'original':p.name,'original_png_sha256':sha(p),'file':q.name,'webp_sha256':sha(q),'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'size':list(im.size),'lossless_pixels':True})
  print(p.name,p.stat().st_size,'->',q.stat().st_size);p.unlink()
 report.write_text(json.dumps(records,indent=2)+'\n')
def verify_record(path,expected):
 if path.exists():return sha(path)==expected
 if path.parent!=P or not (P/'archive_lossless.json').exists():return False
 record=next((r for r in json.loads((P/'archive_lossless.json').read_text()) if r['original']==path.name),None)
 if not record or record['original_png_sha256']!=expected:return False
 p=P/record['file'];return sha(p)==record['webp_sha256'] and hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest()==record['rgba_sha256']
if __name__=='__main__':archive()
