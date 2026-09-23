"""Verify/recover interrupted studies. None of these are approved map exports."""
from pathlib import Path
import json,hashlib,subprocess,argparse,io
R=Path(__file__).resolve().parents[2]
INDEX=Path(__file__).parent/'drafts/archive.json'
def entries():return json.loads(INDEX.read_text())
def data(record):
 p=R/record['path']
 raw=p.read_bytes() if p.exists() else subprocess.check_output(['git','show',record['commit']+':'+record['path']],cwd=R)
 assert hashlib.sha256(raw).hexdigest()==record['sha256'],record['id']
 return raw
if __name__=='__main__':
 from PIL import Image
 parser=argparse.ArgumentParser();parser.add_argument('--materialize',action='store_true');args=parser.parse_args()
 for record in entries():
  raw=data(record);im=Image.open(io.BytesIO(raw)).convert('RGBA')
  assert hashlib.sha256(im.tobytes()).hexdigest()==record['rgba_sha256']
  assert not record['approved']
  if args.materialize:
   out=R/'.cache/dungeon_biomes_v2/review'/f"{record['id']}.webp";out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
  print('PASS draft',record['id'],record['status'])
