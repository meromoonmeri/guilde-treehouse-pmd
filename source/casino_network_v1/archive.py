from pathlib import Path
import json,hashlib,subprocess,io
R=Path(__file__).resolve().parents[2];INDEX=Path(__file__).parent/'archive.json'
def entries():return json.loads(INDEX.read_text())
def data(path):
 p=Path(path).resolve();rec=next((x for x in entries() if (R/x['path']).resolve()==p),None)
 if p.exists():raw=p.read_bytes()
 elif rec:raw=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R)
 else:raise FileNotFoundError(p)
 if rec:assert hashlib.sha256(raw).hexdigest()==rec['sha256']
 return raw

def image(path):
 from PIL import Image
 return Image.open(io.BytesIO(data(path))).convert('RGBA')
if __name__=='__main__':
 import sys
 for r in entries():
  p=R/r['path'];raw=data(p)
  if '--restore' in sys.argv:p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(raw)
  print('PASS',p.name)
