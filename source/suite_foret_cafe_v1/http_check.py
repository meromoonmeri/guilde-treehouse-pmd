"""Compare served bytes against pinned assets and every portable ZIP member."""
import urllib.request,urllib.error,zipfile,json
from storage import records,materialize,S,sha
base='http://127.0.0.1:8013';n=0
def check(path,expected):
 global n
 req=urllib.request.Request(base+path,headers={'Host':'8013-preview.e2b.app'})
 with urllib.request.urlopen(req) as r:assert r.status==200 and r.read()==expected
 n+=1
for r in records():check('/'+r['name'],materialize(r['name']).read_bytes())
for path,name in {'/':'LF1_duo.png','/finale':'LF1_finale.png','/animation':'LF1_finale_animee.webp','/mobilier':'FC1_mobilier.png','/cafe':'FC1_cafe_echelle1x.png'}.items():check(path,materialize(name).read_bytes())
for prefix,name in [('foret-pack','LF1_finale_calques.zip'),('cafe-pack','FC1_mobilier_taille_import.zip')]:
 with zipfile.ZipFile(materialize(name)) as z:
  for p in z.namelist():check('/'+prefix+'/'+p,z.read(p))
for p in ['/.git/config','/%2e%2e/.git/config','/cafe-pack/../../.git/config']:
 try:urllib.request.urlopen(base+p);raise AssertionError('Private path exposed')
 except urllib.error.HTTPError as e:assert e.code==404
print('PASS',n,'byte-identical responses, preview Host accepted, 3 private paths404')
