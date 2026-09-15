# Panoramas des arènes — Carillon & Cendrée V2

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
