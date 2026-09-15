from pathlib import Path
import json,base64,hashlib,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=R/'source/tours_layers_v3';O=R/'renders/tours_layers_v3';M=json.loads((O/'manifest.json').read_text());assets=[];seen={};projects=[]
def uid(path):
 b=path.read_bytes();key=hashlib.sha256(b).hexdigest()
 if key not in seen:seen[key]=len(assets);assets.append('data:image/png;base64,'+base64.b64encode(b).decode())
 return seen[key]
for m in M:
 p={k:m[k] for k in ['id','title','kind','layers','environment_count','lights','clouds']};p['resources']={}
 for mode in ['jour','nuit']:
  p['resources'][mode]={n:dict(ids=[uid(O/f) for f in a['files']],frame_ms=a['frame_ms']) for n,a in m['modes'][mode].items()}
 projects.append(p)
data=dict(projects=projects,assets=assets,scale='data:image/png;base64,'+base64.b64encode((O/'ECHELLE_FEUILLES_1X.png').read_bytes()).decode());html=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(data,separators=(',',':')));(R/'apercu_tours_layers_v3.html').write_text(html)
readme='''# Tours V3 — entrées générées, petites feuilles, soleil animé et lune réutilisée

## Les quatre scènes restent distinctes
- Entrée Carillon : 36 calques, jour/nuit.
- Entrée Cendrée : 36 calques, jour/nuit.
- Arène Carillon : 47 calques, crépuscule/nuit.
- Arène Cendrée : 45 calques, crépuscule/nuit.
Toutes les compositions et tous les calques sont alignés en 640 × 480, origine (0,0). Ordre exact dans manifest.json. Les versions précédentes restent intactes.

## Entrées : véritable passage au générateur par éléments
Cinq générations : architecture Carillon, architecture Cendrée, sol Carillon, sol Cendrée, planche de quatre variantes d’arbres automnaux. Les tours précédentes et la capture locale Apple_Woods_entrance_TDS.png servent de références. Les arbres et architectures sont générés sur magenta, détourés vers l’alpha, puis adaptés à la taille de travail par nearest-neighbor.
Sol/herbe, chemin, ombres d’arbres, ombre de tour, feuilles au sol, 24 arbres individuels et cinq partitions d’architecture sont séparés. Le chemin est extrait puis ajusté à l’approche ; l’herbe cachée dessous est reconstruite. Les partitions d’architecture recomposent exactement le sprite généré détouré, mais ne sont pas des modules de construction natifs.
Cette V3 est une adaptation générée inspirée d’Apple Woods : contrairement à la V2 d’entrée, elle ne revendique pas une réutilisation pixel-identique des arbres/sols natifs. Les architectures sont régénérées, leur identité est conservée, pas tous leurs pixels.

## Petites feuilles animées
Deux plans alpha indépendants par entrée : arrière (24 particules) et avant (20). Feuilles dessinées dans une cellule de 3 × 3 pixels, avec des poses étroites de 1 à 3 pixels, quatre poses de battement. 128 phases × 125 ms = boucle de 16 secondes. Chute verticale et balancement périodiques ; les débordements sont répliqués aux bords. Les feuilles ne sont pas agrandies dans la scène.
Comparaison réelle : sprite Idle de Bulbizarre PMD, cellule 32 × 40, silhouette visible 17 × 21 pixels. Les feuilles font au maximum 3 pixels de côté, soit 1/7 de sa hauteur visible. ECHELLE_FEUILLES_1X.png est à l’échelle native ; la version 4X est un agrandissement nearest-neighbor de contrôle. Bulbizarre n’est pas intégré aux scènes.
Référence : https://github.com/PMDCollab/SpriteCollab/tree/master/sprite/0001 ; crédit fourni par le dépôt : CHUNSOFT. Fichiers AnimData.xml, crédits et commit consulté conservés dans source/tours_layers_v3/references. Référence de comparaison uniquement, pas une création originale de cette livraison.

## Soleil animé, lune identique aux autres décors
Le disque solaire est un calque indépendant du halo et du ciel. Animation douce à couleurs fixes : alpha 224–255, sans déplacement du disque ni rotation de teinte. 64 phases × 125 ms = 8 secondes. Le halo solaire pulse sur un autre calque. Le soleil n’est pas incrusté dans le ciel ou les montagnes.
La lune simplifiée V2 est remplacée par renders/references_calques_v2/astres/lune.png, la lune détaillée déjà utilisée dans les autres décors, notamment Northern. Même texture et mêmes couleurs, redimensionnement nearest uniquement : disque de 121 × 121 pour Carillon et 131 × 131 pour Cendrée, exactement comme le disque solaire correspondant. Son halo reprend les 64 phases du halo d’origine, à la même échelle et indépendamment du disque. Le disque lunaire reste statique.
Les trois plans de montagnes/relief, trois plans de forêt et chacun de leurs éclairages sont conservés séparément depuis panoramas_tours_v2. Les bases des arènes ne sont pas aplaties. Les nuages et leur éclairage suivent leurs trois déplacements indépendants : +10, −10, +20 px/s ; boucle 64 s.

## Nuit
Entrées : formule Abyss exacte appliquée à chaque calque, y compris les 128 phases des feuilles. Arènes : décors et éclairages nuit déjà validés de V2 conservés pixel pour pixel. Exception émissive explicite : la lune et son halo sont repris tels quels de la version nuit des autres décors, sans leur appliquer une seconde fois le filtre Abyss. C’est le même traitement que la lune de Northern, pas une nouvelle lune recolorée arbitrairement.

## Fichiers et aperçu
apercu_tours_layers_v3.html est autonome hors ligne : quatre scènes, deux ambiances, calques isolés, opacité/visibilité, éclairages désactivables, zoom ×1/×2/×4, pause et curseur temporel. Mémoire de décodage bornée par un cache de 80 images ; les animations sont calculées à partir des PNG, pas d’un film aplati.
Le pack contient les PNG statiques et toutes les phases PNG, les huit OpenRaster phase 0, l’aperçu et les rapports. Les WebP animés alpha par calque et les grands bruts du générateur restent dans le dépôt pour éviter les doublons dans le ZIP.
Chaque famille animée utilise des noms préfixés tl3_<scene>_<mode>_<calque>_<phase>.png. Les PNG ont tous leur canevas 640 × 480. Les petits sprites de feuilles et arbres sont des sources auxiliaires, pas des calques déjà alignés. COMPOSITION, ECHELLE, ARCHITECTURE_GENEREE_DETOUREE et MASQUE_CHEMIN sont des fichiers de contrôle, pas à importer globalement avec les calques. Aucun DTEF ajouté ; échelle de travail habituelle 8 px, détails de feuilles 1–3 px.

## Vérifications et limites
Recomposition des huit scènes et ORA ; filtres nuit ; durée des 14 animations alpha ; lune exacte et taille égale au soleil ; géométrie/RGB fixes du disque solaire ; connexité du masque du chemin ; taille des feuilles et périodicité des paramètres. Les variantes de forêt et de montagne sont conservées à l’identique depuis V2 ; les extensions cachées de ces anciens plans restent des reconstructions.
Tests d’images seulement : aucune validation d’import, de collisions, de navigation ou d’exécution PMDO, ni test GPU réel. La planche d’échelle ne prouve pas l’échelle d’affichage en moteur.
Reproduction depuis le dépôt complet : .venv/bin/python source/tours_layers_v3/build.py ; verify.py ; package.py. Pillow, NumPy, SciPy. Les générations originales et les livraisons précédentes du dépôt sont nécessaires.
'''
(O/'README.md').write_text(readme)
board=Image.new('RGB',(1280,548),'#171c1c');d=ImageDraw.Draw(board)
for i,m in enumerate(M):
 for row,mode in enumerate(['jour','nuit']):
  x=i*320;y=row*274;d.text((x+7,y+6),m['title']+' / '+mode,fill='#e9c58d');im=Image.open(O/m['id']/mode/'COMPOSITION.png').convert('RGB').resize((320,240),Image.Resampling.NEAREST);board.paste(im,(x,y+27))
board.save(O/'VUE_ENSEMBLE.png')
zpath=O/'Tours_Calques_Animations_v3.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(R/'apercu_tours_layers_v3.html','apercu_tours_layers_v3.html')
 for p in O.rglob('*'):
  if p.is_file() and p!=zpath and p.suffix!='.webp':z.write(p,str(Path('contenu')/p.relative_to(O)))
 for p in S.iterdir():
  if p.is_file():z.write(p,str(p.relative_to(R)))
 for name in ['bulbasaur_credits.txt','bulbasaur_AnimData.xml','spritecollab_commit.txt']:
  p=S/'references'/name;z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None;assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
print('Gallery bytes',len(html.encode()),'ZIP bytes',zpath.stat().st_size,'CRC and paths PASS')
