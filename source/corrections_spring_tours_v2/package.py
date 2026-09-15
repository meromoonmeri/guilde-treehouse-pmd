from pathlib import Path
import json,base64,hashlib,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/corrections_spring_tours_v2';M=json.loads((O/'manifest.json').read_text());assets=[];index={};projects=[]
for m in M:
 project=dict(id=m['id'],title={'spring':'Luminous Spring','carillon_applewoods':'Tour Carillon · Apple Woods','cendree_applewoods':'Tour Cendrée · Apple Woods'}[m['id']],size=m['size'],frames=m['frames'],modes={})
 for mode in ['jour','nuit']:
  layers=[]
  for n in m['layers']:
   frames=[]
   for f in range(m['frames'] if n in m['animated'] else 1):
    p=O/m['id']/mode/f'{m.get("prefix","cs2_spring")}_{mode}_{n}{f"_{f:02}" if n in m["animated"] else ""}.png';b=p.read_bytes();key=hashlib.sha256(b).hexdigest()
    if key not in index:index[key]=len(assets);assets.append('data:image/png;base64,'+base64.b64encode(b).decode())
    frames.append(index[key])
   layers.append(dict(name=n,images=frames))
  project['modes'][mode]=layers
 projects.append(project)
data=json.dumps(dict(projects=projects,assets=assets),separators=(',',':'))
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spring & Apple Woods — calques V2</title><style>
*{box-sizing:border-box}body{margin:0;background:#111b1c;color:#e4e8d9;font:15px system-ui}header{padding:28px 5vw 16px;border-bottom:1px solid #384643}h1{font-size:27px;margin:6px 0}small{color:#b3bcaa}main{padding:22px 5vw;display:grid;grid-template-columns:minmax(300px,1fr) 330px;gap:24px}select,button{background:#263a35;color:inherit;border:1px solid #587366;border-radius:6px;padding:9px;margin:5px 8px 5px 0}#stage{position:relative;width:100%;max-width:800px;background:repeating-conic-gradient(#25332f 0% 25%,#192621 0% 50%) 0/16px 16px;image-rendering:pixelated}#stage img{position:absolute;width:100%;height:100%;top:0;left:0}aside{background:#1b2b27;padding:17px;border-radius:9px}#layers{max-height:64vh;overflow:auto}.layer{border-bottom:1px solid #34493e;padding:9px 0;font-size:12px}.layer input[type=range]{width:100%}p{line-height:1.6;color:#bfcbbb}input{accent-color:#dfb564}footer{padding:0 5vw 30px;color:#aabaaa;line-height:1.7}@media(max-width:850px){main{grid-template-columns:1fr}#layers{max-height:40vh}}</style>
<header><small>CORRECTIONS V2 · CALQUES INDÉPENDANTS · JOUR / NUIT</small><h1>Une lumière plus légère, un chemin d’automne.</h1><select id="project"></select><select id="mode"><option value="jour">Jour</option><option value="nuit">Nuit · Abyss exact</option></select><button id="pause">Pause</button><button id="reset">Réinitialiser les calques</button></header>
<main><section><div id="stage"></div><p id="note"></p><label>Phase <input id="phase" type="range" min="0" max="77" value="39"> <span id="frame"></span></label></section><aside><h2>Calques</h2><p>Visibilité et opacité indépendantes. Le spectre est déjà limité à 35 % dans les PNG ; son curseur multiplie cette opacité.</p><div id="layers"></div></aside></main>
<footer>Spring : couleurs fixes, pulsation d’opacité sur 6,5 s. Fond masqué reconstruit localement, pas récupéré à l’identique. Escaliers, relief et halo hors colonne conservés.<br>Apple Woods : herbe, chemin et arbres extraits de <code>Apple_Woods_entrance_TDS.png</code>, sans agrandissement ; feuillage recoloré, feuilles au sol ajoutées. Architecture précédente conservée selon les masques documentés.<br>Les deux tours restent séparées. Salles de boss et nuages inchangés. Vérifications d’images et de calques uniquement : aucun test d’import, de collisions ou d’exécution PMDO.</footer>
<script>const DATA=__DATA__;
const byId=id=>document.getElementById(id),project=byId('project'),mode=byId('mode'),stage=byId('stage'),panel=byId('layers'),phase=byId('phase');let current,views=[],playing=true,start=performance.now(),offset=3250,last=-1;
DATA.projects.forEach((p,i)=>project.add(new Option(p.title,String(i))));
function setup(){current=DATA.projects[Number(project.value)||0];stage.style.aspectRatio=current.size.join('/');stage.replaceChildren();panel.replaceChildren();views=[];current.modes[mode.value].forEach(l=>{const img=document.createElement('img');img.alt='';stage.append(img);const row=document.createElement('div');row.className='layer';const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=true;label.append(check,document.createTextNode(' '+l.name.replace(/_/g,' ')));const range=document.createElement('input');range.type='range';range.min=0;range.max=100;range.value=100;range.setAttribute('aria-label','Opacité '+l.name);check.onchange=()=>img.style.visibility=check.checked?'visible':'hidden';range.oninput=()=>img.style.opacity=range.value/100;row.append(label,range);panel.append(row);views.push({img,layer:l});});phase.max=current.frames-1;phase.disabled=current.frames===1;byId('pause').disabled=current.frames===1;byId('note').textContent=current.id==='spring'?'Masquez le calque 05 pour voir le décor derrière le spectre. Eau, halo et colonne restent indépendants.':'32 calques alignés : herbe, chemin, feuilles, arbres individuels et architecture. Matériaux Apple Woods natifs ; feuillages adaptés à l’automne.';last=-1;paint(Math.min(39,current.frames-1));}
function paint(f){if(f===last)return;last=f;views.forEach(v=>v.img.src=DATA.assets[v.layer.images[f%v.layer.images.length]]);phase.value=f;byId('frame').textContent=(f+1)+' / '+current.frames;}
function tick(now){if(playing&&current.frames>1){const time=((now-start+offset)%6500+6500)%6500;paint(Math.floor(time*78/6500));}requestAnimationFrame(tick);}
project.onchange=mode.onchange=byId('reset').onclick=setup;byId('pause').onclick=()=>{if(playing)offset=(performance.now()-start+offset)%6500;else start=performance.now();playing=!playing;byId('pause').textContent=playing?'Pause':'Lecture';};phase.oninput=()=>{playing=false;byId('pause').textContent='Lecture';offset=Number(phase.value)*6500/78;paint(Number(phase.value));};setup();requestAnimationFrame(tick);
</script></html>'''.replace('__DATA__',data)
(R/'apercu_spring_applewoods_v2.html').write_text(html)
readme='''# Spring translucide & chemins Apple Woods — V2

## Contenu
- Luminous Spring : 600 × 600, 5 familles de calques, 78 phases / 6,5 s ; spectre à couleurs fixes, alpha maximal 89/255 (34,9 %). Eau et halo natifs indépendants. Le fond auparavant opaque est remplacé uniquement dans la colonne (x 275–324, y 0–200) par une reconstruction à partir du décor adjacent et du côté opposé du bassin. Ce ne sont pas des pixels cachés récupérés.
- Tour Carillon et Tour Cendrée : deux entrées distinctes de 640 × 480, 32 calques chacune. Architecture issue de tours_hooh_v1, conservée pixel pour pixel dans les masques fournis ; suppression des restes de fond dans les silhouettes. Arbres individuels, sol, chemin, feuilles et architecture séparés.
- Jour et nuit : formule Abyss exacte appliquée à chaque calque, et non approximation sur la composition aplatie.

## Provenance et adaptations
La référence locale Apple_Woods_entrance_TDS.png (552 × 408) fournit directement les échantillons 24 × 24 d’herbe et de chemin, ainsi que deux arbres extraits à leur échelle native. Les coordonnées sont dans manifest.json. Extraction des arbres par masque feuillage/tronc : ce ne sont pas des sprites détourés officiels. Recoloration du feuillage en or et orange, placement recomposé ; feuilles tombées dessinées pour cette version. Le sol et le chemin ne sont pas recolorés. Les textures natives répétées ne constituent pas un nouveau DTEF/autotile.
L’architecture est la création/adaptation précédente, pas une extraction native Apple Woods. Les salles de boss, boucles de nuages, anciennes entrées et autres livraisons ne sont pas modifiées.

## Utilisation
Ouvrir apercu_spring_applewoods_v2.html (autonome, hors ligne), choisir le lieu et le mode, puis régler les calques. L’opacité 100 % du curseur conserve l’alpha des PNG, elle ne rend pas le spectre opaque.
Chaque répertoire jour/nuit contient les PNG alignés, la composition et un OpenRaster (.ora). Spring inclut aussi son animation WebP. Les ORA de Spring montrent la phase 39 ; les autres phases sont des PNG séparés.
Échelles de travail non validées en jeu : grille habituelle du projet 8 px ; échantillons de matériau 24 px, pas des fichiers DTEF. Utiliser les noms préfixés cs2_* pour les calques ; COMPOSITION et les masques sont des fichiers de contrôle, pas des ressources à importer globalement.

## Contrôles et limites
verification_build.json et verification_independante.json : recomposition PNG/ORA, formule nuit, géométrie des arbres, échantillons natifs, préservation de l’architecture dans les masques, 78 phases de Spring et invariance hors colonne. Connexité du masque du chemin en image seulement.
Aucun test d’exécution, d’import, de collisions ou de navigation PMDO. Les décors restent à intégrer et à tester dans le moteur.

## Reproduction
Depuis la racine : .venv/bin/python source/corrections_spring_tours_v2/build.py ; puis verify.py ; puis package.py. Dépendances : Pillow, NumPy, SciPy. Les sources et anciennes livraisons sont conservées dans le dépôt.
'''
(O/'README.md').write_text(readme)
board=Image.new('RGB',(1280,1640),'#111b1c');draw=ImageDraw.Draw(board)
for i,m in enumerate(M):
 y=i*540;draw.text((16,y+10),projects[i]['title'],fill='#e4e8d9')
 for j,mode in enumerate(['jour','nuit']):
  im=Image.open(O/m['id']/mode/'COMPOSITION.png').convert('RGB');im.thumbnail((640,500),Image.Resampling.NEAREST);board.paste(im,(j*640+(640-im.width)//2,y+35));draw.text((j*640+15,y+28),mode,fill='white')
board.save(O/'VUE_ENSEMBLE.png')
zip_path=O/'Spring_AppleWoods_v2.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(R/'apercu_spring_applewoods_v2.html','apercu_spring_applewoods_v2.html')
 for p in O.rglob('*'):
  if p.is_file() and p.suffix!='.zip':z.write(p,str(Path('contenu')/p.relative_to(O)))
 for p in (R/'source/corrections_spring_tours_v2').rglob('*'):
  if p.is_file():z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
print('Gallery',len(html.encode()),'bytes; archive',zip_path.stat().st_size,'bytes; CRC/path validation PASS')
