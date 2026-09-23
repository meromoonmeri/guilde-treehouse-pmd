"""Lossless original sources retained in Git, with checked hashes and optional restoration."""
from pathlib import Path
import subprocess,hashlib,json,io
R=Path(__file__).resolve().parents[2];INDEX=Path(__file__).parent/'raws/archive.json'
def entries():return json.loads(INDEX.read_text())
def data(path):
 p=Path(path).resolve()
 rec=next((x for x in entries() if (R/x['path']).resolve()==p),None)
 if p.exists():
  raw=p.read_bytes()
  if rec:assert hashlib.sha256(raw).hexdigest()==rec['sha256']
  return raw
 if rec is None:raise FileNotFoundError(p)
 raw=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R)
 assert hashlib.sha256(raw).hexdigest()==rec['sha256'];return raw

def image(path):
 from PIL import Image
 return Image.open(io.BytesIO(data(path))).convert('RGBA')
if __name__=='__main__':
 for rec in entries():
  p=R/rec['path'];raw=data(p)
  if '--restore' in __import__('sys').argv:p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(raw)
  print('PASS',rec['path'],len(raw))
