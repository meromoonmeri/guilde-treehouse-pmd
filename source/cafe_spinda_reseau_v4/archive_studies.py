"""Keep superseded study bytes in reachable Git history, never remove active masters."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[2];P=R/'renders/cafe_spinda_reseau_v4/bruts';INDEX=P/'archived_studies.json'
def read_bytes(path):
 path=Path(path)
 if path.exists():return path.read_bytes()
 rec=next((r for r in json.loads(INDEX.read_text()) if r['file']==path.name),None)
 if rec is None:raise FileNotFoundError(path)
 try:data=subprocess.check_output(['git','show',rec['commit']+':'+rec['git_path']],cwd=R)
 except subprocess.CalledProcessError as e:raise RuntimeError('Fetch historical commit '+rec['commit']+' to restore this superseded study') from e
 assert hashlib.sha256(data).hexdigest()==rec['sha256'];return data
def archive():
 active={Path(r['raw']).name for r in json.loads((P.parent/'manifest.json').read_text())['rooms']}
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();records=[]
 for p in sorted(P.glob('*.webp')):
  if p.name in active:continue
  data=p.read_bytes();historical=subprocess.check_output(['git','show',commit+':'+str(p.relative_to(R))],cwd=R);assert data==historical
  records.append({'file':p.name,'commit':commit,'git_path':str(p.relative_to(R)),'sha256':hashlib.sha256(data).hexdigest(),'status':'superseded study, byte-exact archive in reachable Git history'})
 INDEX.write_text(json.dumps(records,indent=2)+'\n')
 for r in records:(P/r['file']).unlink()
 print('Archived',len(records),'superseded studies; five active masters untouched')
if __name__=='__main__':
 import sys
 if '--restore' in sys.argv:
  for r in json.loads(INDEX.read_text()):
   p=P/r['file'];p.write_bytes(read_bytes(p))
 else:archive()
