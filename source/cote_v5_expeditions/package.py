"""Package 40 ready-to-edit Ground, lossless 20-location viewer and manual.
Run verify.py and runtime_test.py beforehand. The ZIP bytes are compared against
staging, and Ground bytes against the copy used by the native runtime test.
"""
from pathlib import Path
import base64,io,json,zipfile,shutil,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
WEB=ROOT/'sprites/cote_v5_expeditions';PACK=Path.home()/'.cache/cote_v5_expeditions_pack'
VIEW='apercu_metano_expeditions.html';ZIP='mod_metano_expeditions_pmdo_0812.zip'

def main():
 assert json.loads((PACK/'verification.json').read_text())['status']=='PASS'
 assert json.loads((PACK/'runtime_verification.json').read_text())['ground_deserialized']==40
 manifest=json.loads((PACK/'manifest.json').read_text());new=json.loads((WEB/'manifest.json').read_text())
 required=set('fonds/'+p.name for p in (WEB/'fonds').glob('*.png'))
 for z in new['zones']:
  for v in z['variants'].values():required.update(z['id']+'/'+f for f in v['layers'])
 images={}
 for name in sorted(required):
  im=Image.open(WEB/name).convert('RGBA');b=io.BytesIO();im.save(b,format='WEBP',lossless=True,exact=True,method=6)
  raw=b.getvalue();assert Image.open(io.BytesIO(raw)).convert('RGBA').tobytes()==im.tobytes()
  images[name]='data:image/webp;base64,'+base64.b64encode(raw).decode()
 old_html=(ROOT/'apercu_cotes_metano_abyss.html').read_text()
 old=json.loads(old_html.split('const DATA=',1)[1].split(';\ndocument.querySelectorAll',1)[0])
 for name,data in old['images'].items():
  if name in images:
   a=Image.open(io.BytesIO(base64.b64decode(data.split(',',1)[1]))).convert('RGBA')
   b=Image.open(io.BytesIO(base64.b64decode(images[name].split(',',1)[1]))).convert('RGBA')
   assert a.size==b.size and a.tobytes()==b.tobytes()
  else:images[name]=data
 template=(ROOT/'source/cote_v4_abyss/viewer.html').read_text()
 template=template.replace('Métano · Nuit Abyss · PMDO 0.8.12','Métano Expéditions · 40 Ground').replace('Dix côtes Métano · nuit Abyss','Métano Expéditions').replace('PMDO 0.8.12 · 10 lieux · 20 Ground','7 falaises + 3 entrées · 20 lieux · 40 Ground')
 template=template.replace('cotes_metano_abyss_0812_pmdo.zip',ZIP)
 template=template.replace("let mode='nuit',selected=0", "let mode='jour',selected=7")
 template=template.replace("const get=(key)=>images[key];", "el('zone').value='7';\nconst get=(key)=>images[key];")
 template=template.replace("(z.new?'':'V2 · ')","(z.new?(z.kind==='donjon'?'Entrée · ':'Nouveau · '):'Archive · ')")
 template=template.replace('Aucun bâtiment, arbre ou chemin posé','Entrées natives · structures libres · destinations à raccorder')
 template=template.replace('Terrain V2 conservé · nouveaux fonds et nuit','Terrain Métano/Abyss précédent conservé')
 template=template.replace('Métano natif · filtre Abyss · bords W/E/S joints','Nouveau terrain Métano · filtre Abyss · grille 8 px')
 a=template.index('<p>Les dix silhouettes approuvées');b=template.index('</p>',a)+4
 template=template[:a]+'''<p>Sept nouvelles falaises et trois entrées interprètent les layouts étudiés, sans leurs textures. Herbe, roche et accès viennent de Métano. Les deux grottes partagent un encadrement natif dans deux compositions distinctes ; le troisième accès est un défilé ouvert. Le mod conserve aussi les vingt Ground précédents. Les trois destinations de donjon sont à raccorder : les marqueurs ne sont pas des téléporteurs automatiques.</p>'''+template[b:]
 template=template.replace('<strong>Aucun test dans PMDO n’a été effectué.</strong> Les collisions sont libres : dessiner les obstacles et vérifier les raccords avant d’en faire des zones jouables.', '<strong>40 Ground chargés par le vrai PMDO 0.8.12, sans affichage.</strong> Le rendu GPU et le gameplay ne sont pas testés. Les nouvelles collisions de base et les chemins vers les trois seuils sont vérifiés par grille ; les anciennes cartes gardent leurs collisions libres. Voir le manuel pour les raccords et destinations.')
 html=template.replace('__DATA__',json.dumps({'manifest':manifest,'images':images},ensure_ascii=False,separators=(',',':')))
 (ROOT/VIEW).write_text(html)
 (PACK/VIEW).write_text(html.replace(f'<a href="{ZIP}" download>Pack PMDO ↓</a>','<span class="small">Mod extrait · README.md</span>'))
 for src,name in [(HERE/'README.md','README.md'),(ROOT/'MANUEL_METHODE_PMDO.md','MANUEL_METHODE_PMDO.md')]:shutil.copyfile(src,PACK/name)
 shutil.copyfile(HERE/'README.md',WEB/'README.md')
 doors=[]
 for z in new['zones']:
  if z['door']:doors.append({'title':z['title'],'ground_jour':z['variants']['jour']['asset'],'ground_nuit':z['variants']['nuit']['asset'],'threshold_marker':'donjon_seuil','threshold':z['door']['threshold'],'zone_id':None,'segment':None,'floor':None,'return_marker':'entrance','active':False})
 (PACK/'RACCORDEMENT_DONJONS.json').write_text(json.dumps({'note':'Fiche a completer, non executee. Les destinations ne sont pas connues.','entrances':doors},ensure_ascii=False,indent=2))
 (PACK/'OUVRIR_EDITEUR.bat').write_text('@echo off\r\ncd /d "%~dp0..\\.."\r\nif exist "PMDO.exe" (\r\n  start "" "PMDO.exe" -dev -quest metano_expeditions\r\n) else if exist "PMDC.exe" (\r\n  start "" "PMDC.exe" -dev -quest metano_expeditions\r\n) else (\r\n  echo Placer metano_expeditions dans le dossier MODS de PMDO.\r\n  pause\r\n)\r\n')
 (PACK/'OUVRIR_EDITEUR.sh').write_text('#!/usr/bin/env bash\nset -e\ncd -- "$(dirname -- "$0")/../.."\nif [[ -x ./PMDO ]]; then exec ./PMDO -dev -quest metano_expeditions; fi\nif [[ -x ./PMDC ]]; then exec ./PMDC -dev -quest metano_expeditions; fi\necho "Placer metano_expeditions dans le dossier MODS de PMDO." >&2\nexit 1\n')
 runtime=ROOT/'.cache/pmdo-runtime/engine/PMDO/MODS/metano_expeditions'
 hashes={}
 for p in (PACK/'Data/Ground').glob('*.rsground'):
  assert p.read_bytes()==(runtime/'Data/Ground'/p.name).read_bytes()
  hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert len(hashes)==40
 (PACK/'ground_sha256.json').write_text(json.dumps(hashes,indent=2))
 output=ROOT/ZIP
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for p in sorted(PACK.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:
    info=zipfile.ZipInfo('metano_expeditions/'+p.relative_to(PACK).as_posix(),(2026,9,13,0,0,0))
    info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if p.suffix=='.sh' else 0o100644)<<16
    archive.writestr(info,p.read_bytes(),compresslevel=9)
 with zipfile.ZipFile(output) as archive:
  assert archive.testzip() is None
  assert len([n for n in archive.namelist() if n.endswith('.rsground')])==40
  for name in archive.namelist():assert archive.read(name)==(PACK/name.split('/',1)[1]).read_bytes()
 result={'zip':ZIP,'ground':40,'new_cliff_locations':7,'new_entrance_locations':3,'previous_locations':10,
  'viewer_lossless_images':len(images),'native_loaded_ground_bytes_match':True,'zip_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
  'editor_graphics_tested':False,'dungeon_destinations_bound':False}
 (HERE/'package_verification.json').write_text(json.dumps(result,indent=2))
 print(f'40 Ground packaged; {len(images)} lossless images; ZIP {output.stat().st_size/2**20:.2f} MiB; HTML {(ROOT/VIEW).stat().st_size/2**20:.2f} MiB')
if __name__=='__main__':main()
