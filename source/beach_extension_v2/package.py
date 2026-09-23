"""Small, standalone four-module archive; never repackage the unchanged V1 lot."""
from pathlib import Path
import json,copy,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'renders/beach_extension_v2';SRC=Path(__file__).parent
m=json.loads((P/'manifest.json').read_text());portable=copy.deepcopy(m);portable['scope']='extension_only';portable['rooms']=[r for r in portable['rooms'] if r['new']]
portable['layouts']={'extension':portable['layouts']['extension']}
for key in ['reference_beach','sky_assets','preserved_v1_hashes']:portable.pop(key,None)
names={r['id'] for r in portable['rooms']};portable['edges']=[e for e in portable['edges'] if e['from'] in names and e['to'] in names];portable['external_connection']='07N connects to 05S in the separate V1 network.'
files={}
for r in portable['rooms']:
 for rec in r['modes'].values():
  rec.pop('composition',None) # Redundant: native PNG layers recompose exactly.
  for asset in rec['layers']+list(rec['animation'].values()):files[asset['file']]=(P/asset['file']).read_bytes()
files['manifest.json']=(json.dumps(portable,ensure_ascii=False,indent=2)+'\n').encode()
page=(SRC/'viewer.html').read_text().replace('__DATA__',json.dumps(portable,ensure_ascii=False)).replace('const ROOT="renders/beach_extension_v2/"','const ROOT="./"');files['index.html']=page.encode()
files['export_png.py']=(SRC/'export_png.py').read_bytes();files['BeachExt_plan_extension.png']=(P/'BeachExt_plan_extension.png').read_bytes()
for name in ['verification.json','verification_viewer.json','verification_export.json']:
 if (P/name).exists():files[name]=(P/name).read_bytes()
text=(P/'README.md').read_text();material=text[text.index('## Matière et calques'):text.index('## Viewer et export PNG')]
readme='''# Beach Extension V2 — pack autonome 07–10

[Ouvrir le viewer](index.html) · [Plan des quatre cartes](BeachExt_plan_extension.png)

Deux T (07/08), une croix (09), une baie coudée (10). 80 PNG de calques natifs 512×512 et 16 atlas lossless contenant 512 frames. Le viewer fonctionne avec ces seuls fichiers, sans charger V1. La sortie 07N est une connexion externe à la carte 05 du lot précédent ; 08E, 09W et 09S restent libres. Les quatre nouvelles cartes sont reliées entre elles en boucle.

Extraire toute l’archive. Au besoin : `python -m http.server 8000`, puis ouvrir `http://localhost:8000/` sur la même machine.

## Export PNG sans perte

Avec Python et Pillow :

```sh
python -m pip install Pillow
python export_png.py           # 8 compositions PNG, jour/nuit
python export_png.py --frames  # mêmes compositions + 512 frames d’animation PNG
```

Les fichiers sont écrits dans `export_png/`. Aucun resampling ; canevas 512×512, grille8px, basenames uniques. Le viewer permet aussi d’exporter une vue ou un calque à l’instant affiché. Désactiver les guides avant un export sans annotations.

La nuit du terrain utilise Abyss exactement. L’archive n’embarque pas le ciel, les nuages, les six anciens modules ou les bruts de génération : ils restent dans le dépôt. Les quatre nouvelles maps sont des modules de terrain, pas des bandes de ciel.

Les tests rapportés concernent les assets et une simulation DOM ; pas de navigateur graphique ni PMDO validé. Collisions, transitions moteur et ajustements complets des contours rocheux restent à réaliser. Les sources de reconstruction et les bruts sont dans le dépôt, pas dans ce ZIP.

'''+material
files['README.md']=readme.encode();archive=P/'BeachExtension_4modules.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,payload in sorted(files.items()):z.writestr(name,payload)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,payload in files.items():assert z.read(name)==payload
 for r in portable['rooms']:
  for rec in r['modes'].values():
   for asset in rec['layers']+list(rec['animation'].values()):assert asset['file'] in z.namelist() and '..' not in Path(asset['file']).parts
report={'pass':True,'file':archive.name,'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'scope':'Only four new modules; standalone local viewer; no V1 assets required','checks':['all CRCs','all payload bytes identical','every visible image dependency inside archive','external V1 port remains an explicit external connection'],'runtime_PMDO':'NOT TESTED'}
(P/'verification_package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
