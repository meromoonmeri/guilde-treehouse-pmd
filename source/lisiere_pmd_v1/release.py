"""Immutable large deliverables are in Git, not lost or stored outside the repo.
They are byte-checked and materialized in the ignored cache on demand.
"""
from pathlib import Path
import json,hashlib,subprocess,threading
R=Path(__file__).resolve().parents[2];INDEX=Path(__file__).parent/'release.json';LOCK=threading.Lock()
LARGE={'LE1_lisiere_calques_et_effets.zip','LE1_lisiere_animee.webp'}
def entries():return json.loads(INDEX.read_text())
def output_path(name):
 p=R/('.cache/lisiere_pmd_v1/releases' if name in LARGE else 'renders/lisiere_pmd_v1')/name;p.parent.mkdir(parents=True,exist_ok=True);return p

def materialize(name):
 rec=next(r for r in entries() if r['name']==name);p=output_path(name)
 with LOCK:
  if not p.exists():
   raw=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R)
   assert hashlib.sha256(raw).hexdigest()==rec['sha256'];tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(p)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'], 'Rebuilt asset differs from pinned release; publish a new asset revision explicitly.'
 return p
if __name__=='__main__':
 for r in entries():print('PASS',materialize(r['name']),r['sha256'])
