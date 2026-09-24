"""Portable, deterministic, source-independent cafe asset pack."""
from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[2];O=R/'renders/cafe_halcyon_agrandi_v1';payload={}
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.suffix=='.zip' or p.name=='verification_package.json':continue
 data=p.read_bytes()
 if p.name=='index.html':data=data.decode().replace('id="pack" href=','hidden id="pack" href=').encode()
 payload[str(p.relative_to(O))]=data
archive=O/'CafeHalcyon_pack.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,data in payload.items():
  info=zipfile.ZipInfo(name,date_time=(2026,9,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,data in payload.items():assert z.read(name)==data
 m=json.loads(z.read('manifest.json'))
 for item in m['layers']+m['furniture']:assert item['file'] in z.namelist()
 for anim in m['animations'].values():
  assert anim['sheet'] in z.namelist()
  for p in anim['frames']:assert p in z.namelist()
report={'pass':True,'files':len(payload),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'archive':archive.name,'checks':['CRC of all payloads','all stored bytes match delivery files except hidden self-download link','all runtime asset dependencies present'],'runtime_PMDO':'NOT TESTED'}
(O/'verification_package.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
