from pathlib import Path
import json,hashlib,base64,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/panoramas_tours_v2';S=R/'source/panoramas_tours_v2';M=json.loads((O/'manifest.json').read_text());assets=[];seen={};projects=[]
for m in M:
 p=dict(m);p['modes']={}
 for mode in ['jour','nuit']:
  ids=[]
  for name in m['layers']:
   b=(O/m['id']/mode/f'pt2_{m["id"]}_{mode}_{name}.png').read_bytes();key=hashlib.sha256(b).hexdigest()
   if key not in seen:seen[key]=len(assets);assets.append('data:image/png;base64,'+base64.b64encode(b).decode())
   ids.append(seen[key])
  p['modes'][mode]=ids
 projects.append(p)
html=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(dict(projects=projects,assets=assets),separators=(',',':')));(R/'apercu_panoramas_tours_v2.html').write_text(html)
readme='''# Panoramas des arènes — Carillon & Cendrée V2

## Ce qui change
Deux panoramas originaux générés séparément puis adaptés à la perspective et aux ouvertures des arènes existantes : forêt vue de haut en contrebas, plusieurs chaînes de montagnes, grand soleil doré-orangé entre les sommets. Carillon : vallée dorée/olive ; Cendrée : reliefs escarpés, canopée cuivrée.
Les anciennes livraisons, entrées Apple Woods, Spring, boss et nuages restent intacts dans leurs répertoires précédents. Cette V2 assemble les éléments des boss précédents avec les nouveaux panoramas et éclairages.

## Calques
640 × 480 pixels, origine commune (0,0), PNG RGBA en composition normale source-over. 46 calques Carillon, 44 Cendrée :
- Ciel, halo de l’astre, disque solaire/lunaire, étoiles (transparentes au crépuscule).
- Trois plans de relief et trois plans de forêt ; chacun a un calque de texture et son calque de lumière.
- Trois nuages, chacun avec son éclairage associé ; déplacements horizontaux indépendants.
- Plancher, accès, parois, vitraux, toiture, traverses et poutres issus des arènes précédentes ; chaque élément possède un nouvel éclairage indépendant.

Le masque de chaque plan de paysage laisse le ciel transparent. Les zones auparavant cachées sous le plan suivant sont reconstruites à partir de sa propre bande visible : ce n’est pas une récupération des pixels occultés. Les plans ne sont pas des modules natifs PMD.
Les éclairages du paysage sont décomposés en accent coloré à alpha variable et base assombrie ; les textures conservent leurs ombres dessinées et leur palette de matériau. Les PNG de base des éléments d’architecture sont identiques aux anciens. Les accents de soleil sur le plancher et les éléments de l’arène sont de nouveaux calques optionnels, pas des modifications destructives des bases.

## Nuit exacte
Une lune avec détails et des étoiles remplacent le soleil ; le halo et les éclairages ont des couleurs sources neutres/froides. Ensuite, la formule exacte Abyss de source/cote_v4_abyss/night.py est appliquée à chaque calque. Il ne s’agit pas d’un filtre approximatif sur l’image aplatie. sources_nuit_avant_filtre.zip conserve les sources préfiltre pour vérification, y compris les alternatives lunaires. Les PNG nuit sont déjà filtrés : ne pas appliquer le filtre une seconde fois.

## Nuages
La galerie anime les trois paires nuage/éclairage avec les paramètres précédents : période 640 px, boucle 64 000 ms, multiplicateurs 1, −1, 2, soit +10, −10, +20 px/s. Les calques de lumière suivent exactement leur nuage. Les PNG/ORA correspondent à la phase zéro. Il n’y a pas de nouveau film WebP complet dans ce pack ; les anciens films et boucles restent dans tours_hooh_v1.

## Provenance et fichiers
Les deux images source/panoramas_tours_v2/references/*_guide.png sont des images générées par IA pour ce travail, non des captures canoniques. Réduction à 640 × 480, adaptation verticale, ciel/astre reconstruits, silhouettes détourées et plans de profondeur reconstruits. Les intermédiaires magenta figurent dans le dépôt, pas dans le pack de travail ; ils sont retirés par clé vers l’alpha avant assemblage. Les lumières et astres sont construits par le script.
- apercu_panoramas_tours_v2.html : aperçu autonome hors ligne, arène/panorama/calque isolé, jour/nuit, visibilité et opacité par calque, éclairages désactivables et nuages animés.
- <tour>/<jour|nuit>/ : PNG préfixés pt2_*, COMPOSITION.png, PANORAMA_SEUL.png, document OpenRaster .ora.
- manifest.json : ordre des calques, provenance, paramètres de l’astre et des nuages.
- verification.json : recomposition, ORA, correspondance nuit, bases d’architecture et périodicité.
Les COMPOSITION, PANORAMA_SEUL, masques et archives d’audit ne sont pas à importer comme ressources globales. Les calques ont des noms uniques. Échelle de travail du projet 8 px, aucun fichier DTEF/autotile ajouté.

## Vérifications et limites
Contrôles d’images et d’alpha uniquement. Aucun test de moteur PMDO, import, collisions, navigation, GPU ou parallaxe en jeu. Les scripts reconstruisent des illustrations calquées, pas des cartes jouables.
Reproduction depuis le dépôt complet : .venv/bin/python source/panoramas_tours_v2/build.py ; puis verify.py ; puis package.py. Pillow, NumPy et SciPy requis ; les anciennes sources du dépôt sont nécessaires.
'''
(O/'README.md').write_text(readme)
board=Image.new('RGB',(1280,2056),'#171922');d=ImageDraw.Draw(board)
for i,m in enumerate(M):
 for row,kind in enumerate(['COMPOSITION','PANORAMA_SEUL']):
  y=(i*2+row)*514;d.text((16,y+9),('Tour Carillon' if i==0 else 'Tour Cendree')+' / '+('Arene' if row==0 else 'Panorama seul'),fill='#f0c58a')
  for col,mode in enumerate(['jour','nuit']):board.paste(Image.open(O/m['id']/mode/f'{kind}.png').convert('RGB'),(col*640,y+30))
board.save(O/'VUE_ENSEMBLE.png')
zpath=O/'Panoramas_Arenes_Tours_v2.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(R/'apercu_panoramas_tours_v2.html','apercu_panoramas_tours_v2.html')
 for p in O.rglob('*'):
  if p.is_file() and p!=zpath and 'intermediaires_magenta' not in p.parts:z.write(p,str(Path('contenu')/p.relative_to(O)))
 for p in S.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None;assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
print('Gallery bytes:',len(html.encode()),'ZIP bytes:',zpath.stat().st_size,'CRC and safe paths PASS')
