# Zone glaciale — grotte boréale V1

Nouvelle zone de rendu demandée : une vallée gelée avec **arrivée au sud**, chemin lisible vers une **grande grotte de glace au nord**, falaises glacées, cristaux, ciel nocturne et aurore animée. La composition finale est [`COMPOSITION.png`](COMPOSITION.png) ; l’aperçu interactif autonome est [`../../apercu_zone_glaciale_grotte_boreale_v1.html`](../../apercu_zone_glaciale_grotte_boreale_v1.html).

## Livrables

| Élément | Emplacement | Rôle |
|---|---|---|
| Composition phase 0 | `COMPOSITION.png` | rendu complet 1264 × 1008 px, sans lissage |
| Calques éditables | `calques/` | ciel, étoiles, sol, chemin, falaises, grotte et détails transparents alignés |
| Aurore animée | `animation/frames/` | 16 PNG transparents alignés, 100 ms par phase, boucle de 1,6 s |
| Asset palette | `animation/aurore_indexee.png`, `aurore_alpha.png`, `palettes_16frames.json` | indices et alpha séparés ; rampes chromatiques cyclées |
| Édition | `zone_glaciale_grotte_boreale_v1.ora` | OpenRaster : tous les calques statiques + frame 00 de l’aurore |
| Contrôles visuels | `review/`, `PASSAGE_SUD_NORD_CONTROLE.png`, `masques/` | planches, GIFs, route géométrique et masques de découpe |
| Métadonnées | `manifest.json`, `placement_recipe.json`, `verification.json` | provenance, ordre des plans, limites et résultats des contrôles |
| Sources brutes | `bruts/` | trois sorties de génération préservées, dont les deux détourages magenta |

La toile fait **1264 × 1008 px** (158 × 126 cellules de 8 px). Les pixels des trois bruts n’ont pas été redimensionnés : le terrain a été translaté de 200 px vers le bas pour dégager un vrai ciel au-dessus de la falaise, et le bas non visible du ciel est prolongé sous le terrain.

## Chemin sud → nord

Le chemin quitte le bord **sud** autour de `(632, 1007)` et rejoint le seuil de grotte autour de `(632, 548)`. Le masque `masques/09_corridor_geometrique_sud_nord.png` est continu, avec une demi-largeur minimale de 25 px ; `PASSAGE_SUD_NORD_CONTROLE.png` le met en évidence.

Il s’agit d’un **contrôle de composition uniquement**. Le masque ne fournit ni colliders, ni occlusion de personnage, ni warp de donjon.

## Méthode Guilde appliquée

1. Les sources de terrain et d’aurore ont été générées sur fond magenta puis gardées sans écrasement dans `bruts/`.
2. Le fond est retiré par une matte reproductible : magenta pur et composante magenta reliée aux bords. Les petits débris isolés de l’aurore sont écartés ; aucun lissage ou redimensionnement ne modifie les pixels retenus.
3. Le terrain détouré est réparti en une **partition exacte** : sol de vallée, chemin, falaise nord, falaises latérales, encadrement de grotte, obscurité de la cavité et détails avant. Un sol discret séparé est généré sous les volumes afin d’éviter un vide lorsqu’un relief est caché ; il est recouvert par la partition dans la composition complète.
4. Le ciel reste opaque, les étoiles sont un overlay transparent, et l’aurore est un troisième overlay transparent placé derrière le terrain.
5. L’aurore utilise un dessin indexé et un alpha distincts. Ses 16 phases combinent une onde verticale par colonne — **sans défilement ni wrap** — et la rotation des rampes cyan / violet-rose. La phase virtuelle 16 est identique à la phase 0 avant encodage.
6. Tous les plans sont alignés sur la même toile, exportés en PNG, regroupés dans un ORA, présentés dans un viewer autonome et vérifiés avant l’archive.

Les nouveaux visuels sont des **rendus générés à examiner artistiquement**, et non des textures canoniques pixel-identiques extraites d’un jeu.

## Reproduire et vérifier

Depuis la racine du dépôt :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r source/zone_glaciale_grotte_boreale_v1/requirements.txt
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/build.py
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/verify.py
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/package.py
```

Le vérificateur exécute 53 contrôles au moment de cette livraison : dimensions et grille, hashes des bruts, pixels retenus lors du détourage, partition/recomposition exacte du terrain, continuité géométrique du chemin, 16 calques d’aurore, onde non rigide, boucle, palette/index/alpha, absence de magenta résiduel, recomposition de la scène, GIF/WebP, ORA et syntaxe du viewer.

## Limites explicites

- Ce pack est un **rendu multicouche éditable**, pas un atlas, un `.tile`, un `.rsground` ou une carte PMDO importée.
- Les contrôles sont des contrôles de fichiers et de composition ; ils ne valent pas une approbation artistique.
- Collisions, profondeur par rapport aux personnages, déclenchement de la grotte, sortie de donjon, parallaxe et rendu runtime **ne sont pas testés dans PMDO**.
- La cadence, la déformation et le cycling sont une animation originale proposée ; ce n’est pas l’extraction d’un cycle officiel.

Références PMD présentes dans le dépôt : © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft. Les sorties de génération ajoutées ici ne revendiquent aucune licence ou approbation officielle.
