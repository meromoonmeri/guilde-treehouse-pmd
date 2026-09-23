"""Check direct image/ZIP delivery and retained historical raw URLs."""
from pathlib import Path
import urllib.request,urllib.error,json,hashlib,zipfile,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.dungeon_biomes_v1.archive import data,entries
from source.casino_network_v1.archive import data as old_data,entries as old_entries
O=R/'renders/dungeon_biomes_v1'
def get(port,path,expected):
 with urllib.request.urlopen(f'http://127.0.0.1:{port}'+path) as r:
  assert r.status==200;assert r.read()==expected,path
 return 1
n=0
for p in list((O/'apercus').iterdir())+[O/'DB1_cinq_duos_multicalques.zip']:
 n+=get(8011,'/'+str(p.relative_to(R)),p.read_bytes())
n+=get(8011,'/',(O/'apercus/DB1_collection.png').read_bytes())
with zipfile.ZipFile(O/'DB1_cinq_duos_multicalques.zip') as z:
 m=json.loads(z.read('manifest.json'));paths=[f for rec in m['maps'] for f in rec['layers']]
 paths+=['manifest.json','README.md','assemble.py']+[rec['frames'][0] for rec in m['animations'].values()]
 for path in paths:n+=get(8011,'/dungeon-pack/'+path,z.read(path))
for rec in entries():n+=get(8011,'/'+rec['path'],data(R/rec['path']))
for rec in old_entries():
 for port in [8010,8011]:n+=get(port,'/'+rec['path'],old_data(R/rec['path']))
for port in [8010,8011]:
 try:urllib.request.urlopen(f'http://127.0.0.1:{port}/.git/config');raise AssertionError('private Git path exposed')
 except urllib.error.HTTPError as e:assert e.code==404
print('PASS',n,'direct image/ZIP/archived-raw responses; private Git paths blocked')
(O/'http_verification.json').write_text(json.dumps({'pass':True,'responses':n,'ports':[8010,8011],'scope':'HTTP byte identity, direct PNG/WebP/ZIP, historical raw URLs, private Git paths blocked; not browser/GPU validation'},indent=2)+'\n')
