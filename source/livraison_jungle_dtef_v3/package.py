from pathlib import Path
import json,base64,re,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];D=R/'renders/donjons_generes_dtef_v3';J=R/'renders/jungle_geysers_v2';m=json.loads((D/'manifest.json').read_text());data={};relative={}
# Full DTEF viewer keeps native independent layer timing, not the short WebP excerpts.
old=(R/'renders/donjons_dtef_v2/apercu_dtef.html').read_text();before,after=old.split('const DATA=',1);after=after.split(',c=document',1)[1]
for e in m['themes']:
 for mode in ['jour','nuit']:
  id=f'd3_{e["id"]}_{mode}';imgs={};rel={}
  for f in e['files']:
   p=D/'RAW/TileDtef'/id/f;imgs[f]='data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode();rel[f]=f'RAW/TileDtef/{id}/{f}'
  obj={**e,'id':id,'title':e['id']+' · '+mode,'kind':'Matières retouchées au générateur ; bordures et animations natives conservées'};data[id]={**obj,'images':imgs};relative[id]={**obj,'images':rel}
head=re.sub(r'<header>.*?</header>','<header><h1>Dix donjons — retouches générées légères</h1><p>Matières générées adaptées aux vrais gabarits DTEF de Sakura. Bordures4px, silhouettes et couches animées natives conservées. Jour/nuit Abyss.</p></header>',before,flags=re.S)
head=re.sub(r'<footer>.*?</footer>','<footer><p>788PNG DTEF dont728feuilles animées inchangées. Import DTEF24px ; aucun test PMDO. Matières adaptées, pas des tuiles canoniques intactes. La vue V0 seule compare les variantes finales, pas le rendu avant génération.</p></footer>',head,flags=re.S)
after=after.replace("themes.value='d2_foret_jour'","themes.value='d3_foret_jour'")
(R/'apercu_donjons_generes_dtef_v3.html').write_text(head+'const DATA='+json.dumps(data)+',c=document'+after)
(D/'apercu_dtef.html').write_text(head+'const DATA='+json.dumps(relative)+',c=document'+after)
# Main gallery: both immersive Ground versions, and quick previews of each biome.
links={}
def uri(p):
 mime='image/webp' if p.suffix=='.webp' else 'image/png';u='data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode();links[u]=str(p.relative_to(R));return u
def item(n,p):return dict(name=n,src=uri(p))
gallery={};desc={}
for e in json.loads((J/'manifest.json').read_text()):
 name='Jungle — '+('clairière et grotte' if e['id'].endswith('grotte') else 'clairière');gallery[name]={};desc[name]='648×504 · 29calques · un geyser central et quatre petits · quatre poses générées sur un cycle de4secondes. Végétation générée + groupes natifs Southern Jungle à échelle1:1.'
 for mode in ['jour','nuit']:
  P=J/e['id']/mode;ls=[item('Composition animée',P/'ANIMATION.webp'),item('Émission centrale maximale',P/f'jgv2_{e["id"]}_{mode}_composition_05.png')]
  for n in e['layer_order']:ls.append(item(n+' · état0',P/(f'jgv2_{e["id"]}_{mode}_{n}_00.png' if n in e['animated'] else f'jgv2_{e["id"]}_{mode}_{n}.png')))
  gallery[name][mode]=ls
for e in m['themes']:
 name='Donjon — '+e['id'];gallery[name]={};desc[name]='Matières retouchées au générateur, vrai gabarit DTEF natif24px. Le WebP est un extrait répété de2secondes ; ouvrir la galerie DTEF pour les cadences complètes.'
 for mode in ['jour','nuit']:
  A=D/'apercus'/f'd3_{e["id"]}_{mode}';ls=[item('Aperçu animé — extrait2s',A/'EXTRAIT_2S.webp')]
  for v in range(3):ls.append(item(f'Gabarit DTEF statique — variante{v}',D/'RAW/TileDtef'/f'd3_{e["id"]}_{mode}'/f'tileset_{v}.png'))
  gallery[name][mode]=ls
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Jungle à geysers et DTEF générés</title><style>body{background:#102822;color:#ebf0db;font:16px system-ui;margin:0}main{max-width:1120px;margin:30px auto;padding:20px}h1{font-size:32px}p{line-height:1.6;color:#c0d7c6}select{background:#2b4a3f;color:white;padding:12px;border:1px solid #648571;border-radius:6px;max-width:100%;margin:5px}img{image-rendering:pixelated;max-width:100%;width:100%;background:repeating-conic-gradient(#284438 0 25%,#385246 0 50%) 0/16px 16px}a{color:#b1e6cf}.note{background:#243e34;padding:16px}</style><main><h1>Southern Jungle · geysers & donjons retouchés</h1><p>Deux clairières immersives, avec ou sans grotte, en jour/nuit. Dix donjons légèrement retouchés au générateur puis réexportés dans leurs véritables gabarits DTEF.</p><select id="project"></select><select id="mode"><option>jour</option><option>nuit</option></select><select id="asset"></select><p id="info"></p><img id="view" alt="Aperçu des nouveaux décors"><p><a href="apercu_donjons_generes_dtef_v3.html">Ouvrir la galerie technique DTEF — animations complètes, variantes et fichiers</a></p><p class="note">Les zones associent un décor généré à des groupes végétaux Southern Jungle natifs. Les geysers sont générés, puis détourés et animés sur des calques indépendants. Les donjons gardent leurs bordures et animations natives, mais leur matière statique est adaptée. Nuit exacte Abyss par calque. Aucun test PMDO.</p></main><script>const data='''+json.dumps(gallery)+''',descriptions='''+json.dumps(desc)+''';Object.keys(data).forEach(k=>project.add(new Option(k,k)));function setup(){asset.replaceChildren();data[project.value][mode.value].forEach((e,i)=>asset.add(new Option(e.name,i)));info.textContent=descriptions[project.value];show()}function show(){view.src=data[project.value][mode.value][+asset.value].src}project.onchange=setup;mode.onchange=setup;asset.onchange=show;setup();</script></html>'''
(R/'apercu_jungle_donjons_v3.html').write_text(html)
# Compact distributable: exports, sources, local-linked galleries; raw generations remain in repository.
zpath=D/'DTEF_generes_et_jungle_geysers_v3.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for p in (D/'RAW').rglob('*'):
  if p.is_file():z.write(p,str(p.relative_to(D)))
 for root in [D,J,R/'source/donjons_generes_dtef_v3',R/'source/jungle_geysers_v2',R/'source/livraison_jungle_dtef_v3']:
  for p in root.rglob('*'):
   if p.is_file() and p!=zpath and '__pycache__' not in p.parts and 'bruts' not in p.parts and '_composition_' not in p.name and 'RAW' not in p.parts:z.write(p,str(p.relative_to(R)))
 for u,path in links.items():html=html.replace(u,path)
 # Main gallery DTEF links use pack-root RAW/, not repository-relative paths.
 html=html.replace('renders/donjons_generes_dtef_v3/RAW/','RAW/');z.writestr('apercu_jungle_donjons_v3.html',html);z.writestr('apercu_donjons_generes_dtef_v3.html',(D/'apercu_dtef.html').read_text())
 for e in json.loads((J/'manifest.json').read_text()):
  for mode in ['jour','nuit']:
   p=J/e['id']/mode/f'jgv2_{e["id"]}_{mode}_composition_05.png';z.write(p,str(p.relative_to(R)))
print('Gallery + compact ZIP:',zpath.stat().st_size,'bytes')
