# Waterfall Lake V2 — trois cascades et falaises en demi-cercle

Disposition choisie par l’utilisateur : **trois cascades au total**, la centrale conservée et deux nouvelles chutes latérales autour de la moitié supérieure du lac. L’accès sud reste ouvert.

## Édition limitée de la version fidèle
La base reste `waterfall_lake_fidele_v1`, dérivée du PNG GBA original. Ses calques de roche centrale, herbe, végétation, disque et pierres d’accès sont conservés pixel pour pixel. Les nouveaux reliefs s’ajoutent devant certains pixels du fond ; il ne s’agit donc pas d’une composition globale pixel-identique à V1, même si ses calques d’origine restent intacts.

Deux ailes rocheuses ont été générées isolément sur magenta avec la référence Waterfall Lake, puis réduites au plus proche voisin et ramenées à la palette des falaises GBA originales. Elles prolongent l’encadrement en demi-cercle dans la partie haute seulement. La bande centrale x=196–307 n’est pas recouverte par ces ajouts : la chute principale et ses rochers natifs y restent visibles. Le centre du lac et l’accès ne sont pas redessinés.

## Trois chutes cohérentes
- Chute centrale et écume centrale : mêmes calques et animations que V1.
- Chutes latérales : même matière de pixels GBA extraite en V1, déplacée vers le bas de 2 px par pose. Les canaux suivent les ouvertures des nouveaux reliefs et sont continus de la limite haute au pied, y=108.
- Écumes latérales : copies adaptées de la petite écume GBA animée en V1, à une largeur de 42 px. Elles restent attachées aux nouveaux pieds.

Les nouvelles chutes entrent par la limite haute de l’image, comme la centrale ; leur alimentation en amont hors cadre n’est pas représentée. Les mouvements sont reconstruits depuis la référence statique, pas récupérés comme des animations GBA originales.

## Eau : subtilité et harmonie
### Cercles de profondeur
Aucun déplacement ni déformation des cercles. Leurs couleurs reçoivent une modulation très faible sur quatre poses : **rouge inchangé, vert ±2 maximum, bleu ±3 maximum**. La variation est répartie selon les bandes de profondeur et revient à la couleur initiale ; pas de grand mouvement de vague ni de changement de taille des cercles. Hors masque des anneaux, le fond d’eau est identique à V1.

### Reflets autour des plateformes
Les huit poses, les contours et les alphas des reflets natifs Altere/Métano sont conservés. Leurs **RGB sont adaptés à la profondeur locale**, puis ramenés aux couleurs aquatiques du PNG GBA original, pour éviter un halo vert-turquoise étranger au lac bleu. Ce n’est donc plus une copie RGB intacte du reflet natif ; c’est son animation géométrique, harmonisée à Waterfall Lake. Les pixels des pierres ne sont pas recolorés en jour.

## Jour/nuit et calques
504 × 360, **28 calques par ambiance**, 24 poses, boucle de **4 secondes**. Cadence commune : 10 frames de jeu par pose, horodatages cumulés arrondis en millisecondes. La nuit garde le filtre Abyss déjà employé pour Northern et V1, appliqué par calque. Pas de ciel ou d’astre inventé au-dessus de ce lac vu de dessus.

- 14 statiques : terrain GBA d’origine, deux ailes de falaise, disque et six pierres d’accès.
- 14 animés : eau/anneaux, trois cascades, trois écumes, sept groupes de reflets autour du disque et des pierres.

Les calques de scène utilisent des basenames `lake2_jour_*` et `lake2_nuit_*`, distincts de V1. Les surfaces cachées derrière les nouveaux reliefs ne sont pas reconstituées comme un terrain explorable ; la base V1 reste dessous.

## Ouvrir
- `../../apercu_waterfall_lake_trois_v2.html` : galerie animée jour/nuit, sélection de chaque calque.
- `jour/COMPOSITION.png`, `nuit/COMPOSITION.png` : états initiaux.
- `jour/ANIMATION.webp`, `nuit/ANIMATION.webp` : boucles complètes.
- `jour/lake2_jour.ora`, `nuit/lake2_nuit.ora` : 28 calques à l’état initial.
- `jour/lake2_jour_*.png`, `nuit/lake2_nuit_*.png` : calques alignés et 24 compositions par ambiance.
- `bruts/falaises_arc_magenta.png` : génération des seuls ajouts rocheux.
- `MASQUE_*.png` : anneaux, falaises ajoutées et deux nouveaux canaux.
- `verification.json` : résultats des contrôles.
- `waterfall_lake_trois_v2.zip` : paquet autonome avec dépendances de V1 nécessaires aux scripts.

## Vérifications
48 recompositions opaques jour/nuit, dimensions, ORA, WebP ; calques statiques originaux inchangés ; cascade et écume centrales inchangées ; modulation RGB limitée aux anneaux ; alphas natifs des reflets préservés ; deux canaux continus sans pixels de chute sur les nouveaux rochers ; contact chute/écume dans chaque phase ; filtre nuit exact par calque.

Ces contrôles ne sont **pas** une validation d’import, de collisions, de mouvement ou de combat dans PMDO. Aucun modèle physique d’écoulement n’est revendiqué. Les images antérieures et la référence originale restent intactes ; les ressources PMD gardent les droits de leurs ayants droit.

Reconstruction depuis la racine avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/waterfall_lake_trois_v2/build.py
.venv/bin/python source/waterfall_lake_trois_v2/verify.py
.venv/bin/python source/waterfall_lake_trois_v2/package.py
```
