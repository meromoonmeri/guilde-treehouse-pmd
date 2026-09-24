"""Portable export/viewer pack; generation originals stay in the repository."""
from pathlib import Path
import zipfile,json,hashlib
P=Path(__file__).resolve().parents[2]/'renders/beach_network_v1'
from restore_exports import restore_exports
restore_exports(P)
archive=P/'BeachNetwork_pack.zip'
files=sorted(p for p in P.rglob('*') if p.is_file() and 'bruts' not in p.relative_to(P).parts and p.name not in [archive.name,'verification_package.json'])
def payload(p):
 data=p.read_bytes()
 if p==P/'index.html':
  # A pack cannot contain itself: remove that one download link from the copy.
  data=data.decode().replace('<a class="button" href="BeachNetwork_pack.zip" download>Pack des six zones + ciel</a>','<span class="small">Pack local · exports ci-dessous</span>').encode()
 return data
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:z.writestr(str(p.relative_to(P)),payload(p))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for p in files:assert z.read(str(p.relative_to(P)))==payload(p)
 assert 'index.html' in z.namelist() and 'manifest.json' in z.namelist()
report={'pass':True,'file':archive.name,'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'checks':['CRC all files','payload identity for all files','local viewer included; self-ZIP link removed in archived copy'],'excludes':['bruts','rebuild sources/dependencies','the archive itself','this outer report'],'runtime_PMDO':'NOT TESTED'}
(P/'verification_package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
