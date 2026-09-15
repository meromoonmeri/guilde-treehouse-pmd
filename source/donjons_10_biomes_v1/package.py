from pathlib import Path
import json,base64,io,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_10_biomes_v1';V=R/'renders/waterfall_lake_generateur_v6';S=R/'renders/steam_cave_geysers_v1'
links={}
def uri(p,mime=None):
 p=Path(p);mime=mime or ('image/webp' if p.suffix=='.webp' else 'image/png');u='data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode();links[u]=str(p.relative_to(R));return u
def item(name,p):return dict(name=name,src=uri(p))
labels={'foret':'Forêt','jungle':'Jungle','marais':'Marais','roche':'Grotte rocheuse','cristal':'Cristal','glace':'Glace','volcan':'Volcan','desert':'Désert','ruines':'Ruines','vapeur':'Grotte vapeur'}
data={};meta={}
for name,label in labels.items():
 data[label]={};meta[label]='12 sols · 47 raccords de murs × 2 variantes · 47 raccords animés × 4 phases · obstacle et miroir. Modules24px, import8px. Matières personnalisées, configuration PMDO non installée.'
 for mode in ['jour','nuit']:
  P=O/name/mode;ls=[item('Carte de démonstration animée',P/'ANIMATION.webp')]
  for suffix,title in [('sols_12','12 variantes de sol'),('murs_47x2','94 cellules murales'),('obstacles','Obstacle et orientation miroir')]:ls.append(item(title,P/f'd10_{name}_{mode}_{suffix}.png'))
  for p in range(4):ls.append(item(f'Terrain animé — phase {p+1}',P/f'd10_{name}_{mode}_terrain_anime_{p}.png'))
  for suffix in ['01_sol','02_murs','04_obstacles']:ls.append(item('Calque '+suffix,P/f'd10_{name}_{mode}_{suffix}.png'))
  data[label][mode]=ls
for label,P,prefix,desc in [('Cascades — V6 générateur',V,'lake6','Raccords latéraux repassés au générateur ; eau animée calée sur les nouveaux contours.30calques. Bassin, cascade centrale et écume conservés.'),('Steam Cave — cinq geysers',S,'steam1','Décor original Steam Cave Peak sans perte. Un geyser central, quatre petits, jets et vapeurs séparés.17calques. Geysers dessinés procéduralement, non canoniques.')]:
 data[label]={};meta[label]=desc;m=json.loads((P/'manifest.json').read_text())
 for mode in ['jour','nuit']:
  ls=[item('Composition animée',P/mode/'ANIMATION.webp')]
  if prefix=='lake6':ls.append(item('V5 — avant passage au générateur',R/'renders/waterfall_lake_encastrees_v5'/mode/'ANIMATION.webp'))
  else:ls.append(item('Geyser central — émission maximale',P/mode/f'steam1_{mode}_composition_05.png'))
  for n in m['layer_order']:
   f=P/mode/(f'{prefix}_{mode}_{n}_00.png' if n in m['animated'] else f'{prefix}_{mode}_{n}.png');ls.append(item('Calque pose0 — '+n,f))
  data[label][mode]=ls
# Contact sheet for quick comparison of all ten actual assembled test scenes.
board=Image.new('RGB',(1440,492),(23,39,42));d=ImageDraw.Draw(board)
for i,(name,label) in enumerate(labels.items()):
 x=(i%5)*288;y=(i//5)*246;d.text((x+8,y+8),label,fill='white');im=Image.open(O/name/'jour/COMPOSITION.png').convert('RGB').resize((288,216),Image.Resampling.NEAREST);board.paste(im,(x,y+30))
board.save(O/'VUE_10_BIOMES.png')
cmp=Image.new('RGB',(1008,388),(23,39,42));d=ImageDraw.Draw(cmp);d.text((10,8),'V5 : encastrement procedural',fill='white');d.text((514,8),'V6 : raccords du generateur',fill='white');cmp.paste(Image.open(R/'renders/waterfall_lake_encastrees_v5/jour/COMPOSITION.png'),(0,28));cmp.paste(Image.open(V/'jour/COMPOSITION.png'),(504,28));cmp.save(V/'AVANT_APRES.png')
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>PMD — cascades,10biomes et Steam Cave</title><style>*{box-sizing:border-box}body{margin:0;background:#11262b;color:#ebeedb;font:16px system-ui}main{max-width:1250px;margin:auto;padding:32px 24px}h1{font-size:32px}p{line-height:1.6;color:#c2d4d0}.tag{color:#86d6c3;text-transform:uppercase;letter-spacing:2px;font-size:12px}select{padding:12px;background:#28464d;color:white;border:1px solid #507078;border-radius:7px;margin:6px 8px 6px 0;max-width:100%}#view{display:block;image-rendering:pixelated;max-width:100%;max-height:1000px;width:auto;min-width:60%;background:repeating-conic-gradient(#294b51 0 25%,#365a60 0 50%) 0/16px 16px;border:1px solid #45616a;margin:16px 0}#board{width:100%;image-rendering:pixelated}.note{padding:18px;background:#223c43;border-left:3px solid #8bbaa4;border-radius:5px}footer{font-size:13px;margin-top:25px}</style><main><div class="tag">Atelier PMD · nouvelle livraison</div><h1>Cascades encastrées, dix biomes et Steam Cave</h1><p>Raccords des chutes repassés au générateur. Dix familles de tilesets personnalisés avec variantes structurelles et jour/nuit. Une zone Steam Cave dédiée aux geysers.</p><select id="project"></select><select id="mode"><option>jour</option><option>nuit</option></select><select id="asset"></select><p id="desc"></p><img id="view" alt="Aperçu sélectionné"><h2>Les dix biomes — même plan de comparaison</h2><img id="board" src="'''+uri(O/'VUE_10_BIOMES.png')+'''" alt="Les dix biomes"><p class="note">Les planches de donjon sont des créations personnalisées : neuf matières générées et une famille issue de crops Steam Cave. Ce ne sont pas dix tilesets natifs certifiés. Modules24px, import8px ; configuration des autotiles, animations et collisions à effectuer dans PMDO. Aucun test moteur. Les geysers sont dessinés procéduralement ; le décor Steam Cave reste natif.</p><footer>PNG par calque, planches de variantes, animations WebP, ORA et manifests inclus dans le ZIP. Nuit : filtre exact Abyss par calque. Les contrôles d’images ne valent pas validation artistique ou moteur.</footer></main><script>const data='''+json.dumps(data)+''',meta='''+json.dumps(meta)+''';Object.keys(data).forEach(k=>project.add(new Option(k,k)));project.value='Cascades — V6 générateur';function setup(){asset.replaceChildren();data[project.value][mode.value].forEach((x,i)=>asset.add(new Option(x.name,i)));desc.textContent=meta[project.value];show()}function show(){view.src=data[project.value][mode.value][+asset.value].src}project.onchange=setup;mode.onchange=setup;asset.onchange=show;setup();</script></html>'''
(R/'apercu_cascades_biomes_steam_v1.html').write_text(html)
zpath=O/'cascades_10_biomes_steam_v1.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for root in [O,V,S,R/'source/donjons_10_biomes_v1',R/'source/waterfall_lake_generateur_v6',R/'source/steam_cave_geysers_v1']:
  for p in sorted(root.rglob('*')):
   if p.is_file() and p!=zpath and '__pycache__' not in p.parts and 'bruts' not in p.parts and '_composition_' not in p.name and '_demo_' not in p.name:z.write(p,str(p.relative_to(R)))
 # Compact ZIP gallery references exported files instead of duplicating their bytes as base64.
 for u,path in links.items():html=html.replace(u,path)
 z.writestr('apercu_cascades_biomes_steam_v1.html',html)
 for mode in ['jour','nuit']:
  for p in [R/'renders/waterfall_lake_encastrees_v5'/mode/'ANIMATION.webp',S/mode/f'steam1_{mode}_composition_05.png']:z.write(p,str(p.relative_to(R)))
print('Gallery and ZIP:',zpath.stat().st_size,'bytes')
