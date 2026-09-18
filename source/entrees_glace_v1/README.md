# Production — entrées de grotte glacées V1

Demande : corriger le ciel/les nuages des falaises précédentes, pousser, puis créer plusieurs layouts de chemin sud→grotte nord avec matière de glace PMD et calques indépendants (sol/chemin, cliffs/reliefs, immersion, ciel, nuages wrap, étoiles, onde boréale animée).

## Sources retrouvées et choisies

- Climat approuvé : `source/cote_dix_zones/reference_autre_agent/`, commit **c16efe12**. Sources native jour/nuit, six familles de nuages, astres ; mêmes rectangles/destinations que le lot Dix Zones. `source/ciels_valides.py` isole ces recettes sans reconstruire les anciens mods.
- Glace : `iceroadpmdsky.png` et `pmdskyicearena.png`, réellement inspectés et fournis au générateur. Les RGB de ces deux PNG forment la palette autorisée du terrain de jour.
- Onde principale : texture canonique du lot `effet_boreale_canonique_v10`, dix poses existantes160ms. Retrait des composantes détachées<40px pour ne pas inclure les points étoilés résiduels ; ni redessin ni resampling. Les étoiles sont sur leur propre plan natif.
- Alternative proposée dans le viewer : les huit PNG du dernier `boreales_palette_cycling_v12`, inchangés. Dessin généré, pas copie native. Aucun fondV3/V8 du lot d’aurores n’est repris.

## Sept appels du générateur

1. Seuil du Givre : chemin central direct, cave au nord, bordures avant gauche/droite ; références deux PNGglace.
2. Anse des Neiges : détour à gauche d’un massif puis cave au nord-est ; mêmes références.
3. Col des Aiguilles : chemin enS, cave nord-ouest, grande aiguille droite ; mêmes références.
4. Sol neige complet : sous-couche sans relief. Premier résultat trop granuleux, conservé mais non utilisé.
5. Correction locale du Col : raccord du chemin interrompu au bord sud. Références : brut3 + IceRoad.
6. Correction locale du Col : refermer le sommet pointu dans le cadre, précédemment coupé par le bord supérieur. Référence : brut corrigé5.
7. Sol neige doux : nouvelle sous-couche presque uniforme, sans confetti/grain dense. Références : brut1 + IceRoad. Cette version est celle du build.

Tous les bruts sont sauvegardés, sans écrasement. Terrain et sols générés1264×848 ; normalisation uniforme nearest763×512 et placement(2,128) dans768×640. L’espace supérieur est un vrai calque ciel, pas une partie générée/peinte du terrain. Le ciel, les étoiles et les nuages restent à taille native, sans resampling.

## Découpe et sol caché

`layouts.json` contient les polygones annotés dans les coordonnées du brut, les zones d’obstacles, un ROI+germe par bouche de grotte, les seuils et les tracés de contrôle. Après sélection du sol, une ouverture sur les pixels clairs retire les morceaux de paroi débordants ; les petits trous fermés (fissures) sont conservés. Le seuil ombré reçoit une région explicite, car sa faible luminosité n’en fait pas une paroi. Les obstacles centraux sont exclus. Tout pixel opaque du terrain appartient à un des cinq masques disjoints (sol visible, profondeur, relief, avant gauche, avant droit).

Le sol visible et le chemin sont remis par-dessus la sous-couche générée propre. Les quatre autres calques du terrain recouvrent exactement les zones où la sous-couche remplace les reliefs. Recompositions exactes testées. Le sol caché est une reconstruction ; les faces cachées des reliefs ne le sont pas. Aucune affirmation d’objets complets arbitrairement déplaçables.

Palette de jour : plus proche couleur canonique en CIELAB, méthode du lot CapsV4. Nuances du brut volontairement corrigées, bruts disponibles. Cette appartenance de palette ne rend **pas** le motif pixel-exact. Nuit terrain : Abyss ; nuages : recette nuit originale Guilde/Sharpedo distincte ; ciel : vraie source nuit.

## Reconstruction

Depuis le dépôt complet :

```sh
python -m venv .venv
.venv/bin/pip install -r source/cliffs_metano_v1/requirements.txt
.venv/bin/python source/entrees_glace_v1/build.py
.venv/bin/python source/entrees_glace_v1/verify.py
.venv/bin/python source/entrees_glace_v1/package.py
node source/entrees_glace_v1/test_viewer.cjs
.venv/bin/python source/entrees_glace_v1/package.py
.venv/bin/python source/entrees_glace_v1/serve.py
```

Le serveur écoute0.0.0.0:8001. Dans Arena utiliser l’aperçu proxy. En local sur la machine du serveur, ouvrir `http://localhost:8001`. `renders/entrees_glace_v1/index.html` et le ZIP fonctionnent aussi hors ligne : manifest embarqué, images locales, pas de fetch indispensable. Les liens documentaires vers le dépôt nécessitent GitHub hors checkout.

Les scripts **ne relancent pas** les appels d’image. `PLANCHE_CALQUES_TERRAIN.png` est une planche d’inspection auxiliaire, pas à importer.

## Contrôles

- `verify.py` : **140 contrôles PASS**, dont palette extraite des deux références, alpha, partitions, recompositions jour/nuit, six ORA à neuf plans, ciel/étoiles validés, six familles de nuages identiques aux exports historiques, modulo wrap, source/retrait de petits points V10, dix frames et WebP lossless, huit copies V12 exactes.
- Trois corridors de contrôle13px contigus sur sol/seuil ; entrée au bord sud et arrivée à la grotte dans la même composante. Tracé descriptif et masques, **pas** des collisions/warps PMDO.
- `test_viewer.cjs` : **19 contrôles PASS, DOM simulé**, trois sélections, six liens jour/nuit, deux effets/sans onde, wrap fin de boucle et retour0, visibilité/opacité, zoom, grille et parcours. Pas un vrai navigateur.
- Syntaxe JavaScript vérifiée par Node ; chemins HTTP et intégrité ZIP contrôlés. Pas de rendu GPU ou gameplay PMDO. L’installation Chromium de la session précédente a échoué (TLS/CDN) ; ne pas annoncer de test réel navigateur.

## Cliffs Métano corrigés dans le même push

`source/cliffs_metano_v1/build.py` utilise maintenant `ciels_valides.py` pour ciel/astres/nuages ; seuls les fonds mer restent ceux de CapsV3. ORA passés de4 à5plans, bande nuages native1440×208 et animationwrap−4px/s ajoutées au viewer. **PNGterrain jour/nuit inchangés**.60contrôlesPASS, ancien test de galerie actualisé. Aucun autre mod ou ancien rendu modifié.
