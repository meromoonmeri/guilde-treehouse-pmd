"""Immutable, SHA-checked Git assets; no external storage or unverified cache."""
from pathlib import Path
import hashlib,json,subprocess,threading
S=Path(__file__).parent;R=S.parents[1];C=R/'.cache/suite_foret_cafe_v1';LOCK=threading.RLock()
def sha(b):return hashlib.sha256(b).hexdigest()
def records(kind='release'):return json.loads((S/('raws/archive.json' if kind=='raw' else 'release.json')).read_text())
def data(rec):
 b=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R)
 assert sha(b)==rec['sha256'];return b
def raw(ident):return data(next(r for r in records('raw') if r['id']==ident))
def materialize(name):
 rec=next(r for r in records() if r['name']==name);p=C/'releases'/name
 with LOCK:
  if not p.exists():
   p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(data(rec));tmp.replace(p)
  assert sha(p.read_bytes())==rec['sha256'], 'Cache differs from immutable published release'
 return p
if __name__=='__main__':
 for r in records():print(materialize(r['name']))
