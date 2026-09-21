"""Byte-identical direct PNG/WebP/ZIP delivery, without an HTML viewer."""
from pathlib import Path
import sys,urllib.request,urllib.error,zipfile,json,subprocess,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.lisiere_pmd_v1.release import entries,materialize
from source.dungeon_biomes_v1.native_archive import native_source_archive
O=R/'renders/lisiere_pmd_v1';count=0

def check(path,expected):
 global count
 with urllib.request.urlopen('http://127.0.0.1:8012'+path) as r:
  assert r.status==200 and r.read()==expected,path
 count+=1
check('/',(O/'LE1_lisiere.png').read_bytes())
for name in ['LE1_lisiere.png','LE1_calques_apercu.png','LE1_cascades_animees.webp']:
 check('/renders/lisiere_pmd_v1/'+name,(O/name).read_bytes())
for rec in entries():check('/'+rec['path'],materialize(rec['name']).read_bytes())
with zipfile.ZipFile(materialize('LE1_lisiere_calques_et_effets.zip')) as z:
 for name in z.namelist():check('/lisiere-pack/'+name,z.read(name))
check('/source/dungeon_biomes_v1/native_sources.zip',native_source_archive().read_bytes())
for rec in json.loads((R/'source/lisiere_pmd_v1/raws/archive.json').read_text()):
 b=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R);assert hashlib.sha256(b).hexdigest()==rec['sha256'];check('/'+rec['path'],b)
try:urllib.request.urlopen('http://127.0.0.1:8012/.git/config');raise AssertionError('private Git data exposed')
except urllib.error.HTTPError as e:assert e.code==404
print('PASS',count,'direct byte-identical HTTP responses; private Git path blocked')
(O/'http_verification.json').write_text(json.dumps({'pass':True,'responses':count,'port':8012,'scope':'Direct files and Git-backed assets verified byte-for-byte; not a browser/GPU/PMDO validation.'},indent=2)+'\n')
