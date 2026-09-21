# Les chemins de la Forêt givrée — Native V2

Six cartes reliées, construites uniquement avec les **vrais modules Frosty Forest** : la neige et les petits arbres givrés viennent des feuilles DTEF canoniques, copiés à leur taille d’origine, sans recoloration, rotation, retournement ni retouche. Galerie : `index.html` (à servir par HTTP). [Les six cartes](WinterNativeV2_Board.png) · [Atlas continu 1008×1656](WinterNativeV2_NetworkTerrain.png).

Cette version répond à la demande « utiliser réellement les textures et arbres canoniques ». La proposition générée précédente (V1, grands sapins générés) n’a **pas** été écrasée : elle n’était pas présente dans cette copie du dépôt — son commit local `57e9b952` n’avait jamais pu être publié — et son archive est nécessaire pour la réarchiver à l’identique.

## Réseau
| Carte | Titre | Sorties | Ambiance par défaut |
|---|---|---|---|
| 01 | La lisière | N, S (arrivée extérieure), E | nuageuse |
| 02 | Les lacets | N, W | nuageuse |
| 03 | Le sentier des arbres givrés | N, S | boréale |
| 04 | La clairière | N, S | nuageuse |
| 05 | Le détour du bosquet | S, E | boréale |
| 06 | Le seuil de l’arène | N (arène V5), S, W | boréale |

Liaisons : 01.N↔03.S, 01.E↔02.W, 02.N↔04.S, 03.N↔05.S, 04.N↔06.S, 05.E↔06.W, 06.N→arène V5 (inchangée). Deux itinéraires rejoignent le seuil ; un cycle. Les six cartes forment un atlas continu 2×3 dont l’adjacence des bosquets est calculée d’un seul tenant : les bords partagés se répondent module à module. **05 est un détour dans le bosquet**, pas une corniche : la feuille Frosty Forest ne contient aucune falaise et aucune n’a été inventée.

## Ce qui est natif, ce qui ne l’est pas
- **Natif, pixel-identique** : les 2898 cellules visibles du terrain (24 px), vérifiées une par une contre leurs rectangles sources ; la palette du terrain est incluse dans celle des feuilles ; cailloux du sol = variante 1 native ; aucune image agrandie.
- **Composition originale** : les tracés des chemins, la répartition des variantes, la neige reconstituée sous les bosquets (calque `Snow`, entièrement en modules natifs). Ce ne sont pas des cartes du jeu d’origine.
- **Non natif, séparé** : les panneaux de ciel (boréal = ciel/étoiles/aurores V5 déjà approuvés, recadrés sans resampling ; nuageux = ciel et nuages validés `ciels_valides.py`), la poudre au vent et les flocons (96 phases, 15 i/s, dessinés pour ce lot). Aucun horizon n’est collé aux tuiles : la vue de dessus reste intacte.
- Frosty Forest n’a pas de calque de terrain secondaire ni d’eau ; ses 19 PNG d’animation sont vides pour ces types et sont archivés à titre de preuve.

## Fichiers
Par carte `NN_id/` : `WinterNativeV2_<id>_{Snow,Forest,Terrain,WalkIntent}.png` (504×552), `_Layers.ora`, `_Placements.json` (source de chaque cellule), `_boreal_Preview.png`, `_cloudy_Preview.png`, `_AnimatedPreview.webp` (6,4 s ; ciel boréal avec les 192 poses V5 à 30 i/s, poudre et flocons).
`atmosphere/` : panneaux de ciel séparés, 96 PNG de poudre + 96 de flocons, `_Powder_Animated.webp`, `_Flakes_Animated.webp`, `_boreal_Animated.webp`, `provenance.json`.
Racine : `network.json`, `native_placements.json`, `world_grid.json`, `verification.json`.
`WalkIntent` est une intention de tracé (blanc = neige), pas une collision PMDO.

## Source exacte
[PMDCollab/RawAsset](https://github.com/PMDCollab/RawAsset) commit **03c80dad937911572f8fb19903771a47956fc696**, `TileDtef/FrostyForest/tileset_{0,1,2}.png` (432×192) ; mapping des 47 cas d’adjacence lu dans `DtefImportHelper.cs` de RogueEssence (commit `8b7eafaf…`, copie déjà présente dans `source/dungeon_autotiles_v1/references/engine/`). Hachages SHA256 et blobs Git : `source/winter_forest_native_v2/provenance.json`. Ressources attribuées à leurs auteurs ; leur présence dans un dépôt public ne vaut pas licence générale.

## Vérifications
`verify.py` : **111 contrôles PASS** — hachages sources, 2898 cellules identiques aux rectangles natifs, palette incluse, recomposition Snow+Forest = Terrain = fusion ORA = découpe de l’atlas, bords scellés sauf ports déclarés (72 px), une seule région praticable par carte, aperçus contenant le terrain inchangé, boucles de 6,4 s, liaisons déclarées des deux côtés.
`test_viewer.cjs` : DOM simulé — six cartes, cycle complet par les boutons de passage, messages arène/extérieur, calques, effets, pause, ciel, zoom. **Aucun navigateur réel n’était disponible dans cet environnement** ; pas de test Chromium pour ce lot.
**Aucun test PMDO** : ni import, ni caméra, ni collisions, ni transitions moteur. Prototype graphique, comme Ledian.

## Reproduction
```
.venv/bin/python source/winter_forest_native_v2/build.py
.venv/bin/python source/winter_forest_native_v2/weather.py   # ~4 min (WebP sans perte)
.venv/bin/python source/winter_forest_native_v2/verify.py
node source/winter_forest_native_v2/test_viewer.cjs
```
Pillow 12.3, NumPy 2.4, SciPy 1.17. Le ciel boréal lit `renders/ice_arena_northern_sky_v5/`.
