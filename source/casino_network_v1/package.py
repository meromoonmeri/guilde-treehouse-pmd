"""Portable casino kit, without duplicated large review images or generation raws."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'renders/casino_network_v1';SRC=Path(__file__).parent
m=json.loads((P/'manifest.json').read_text());files={}
for folder in ['calques','objets','animations','editeur']:
 for path in (P/folder).rglob('*'):
  if path.is_file():files[str(path.relative_to(P))]=path.read_bytes()
for name in ['manifest.json','flammes_provenance.json','verification.json','verification_viewer.json','verification_export.json']:
 if (P/name).exists():files[name]=(P/name).read_bytes()
page=(P/'index.html').read_text().replace('<a id="pack"','<a hidden id="pack"').replace('<a id="still"','<a hidden id="still"').replace('<a id="animation"','<a hidden id="animation"')
files['index.html']=page.encode();files['export_png.py']=(SRC/'export_png.py').read_bytes()
text=(P/'README.md').read_text();text='# Casino des braises — pack autonome\n\n[Ouvrir le viewer](index.html)\n\n'+text[text.index('## Réseau et aménagement'):];files['README.md']=text.encode()
archive=P/'Casino_pack.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,payload in sorted(files.items()):z.writestr(name,payload)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,payload in files.items():assert z.read(name)==payload
 for l in m['layers']:
  for f in l.get('frames',[l.get('file')]):assert f in z.namelist()
report={'pass':True,'file':archive.name,'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'checks':['all CRCs','all payload identities','every viewer image dependency present'],'scope':'38 layer instances, 8 canonical PNG poses/splits, standalone viewer and aligned PNG exporter. No bruts or redundant previews.','runtime_PMDO':'NOT TESTED'}
(P/'verification_package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
