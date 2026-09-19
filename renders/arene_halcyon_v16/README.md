# V16 — sol continu (sans trou) + boréales de la référence en 10 frames, boucle parfaite

Demandes : « La zone au centre devrait pas avoir de trou, régénère » + « les aurores boréales soit ceux de la référence, régénère les mêmes mais avec 10 frames de loop parfaite ».

## Terrain régénéré sans trou
`bruts/terrain_sans_trou.png` : même arène, **sol central continu** (plus de cratère ni d’anneau sombre). Mesure : bord sombre central **5471 px en V15 → 226 px en V16** (−96 %, testé < 600). Alpha par inondation du magenta, zéro magenta résiduel, pointes de pics conservées.

## Boréales : style référence, 10 frames
`bruts/boreale_ref_10.png` : planche 2×5 générée d’après `aurorepmdsky.png` — cœur magenta, liserés cyan, franges en rayons (style exact de la référence). 10 frames `AuroreV16_00..09.png`, **768×256**, 130 ms chacune (1,3 s), **boucle parfaite** : frame 10 ≈ frame 1 (diff 12,6 %, testé). Même rideau qui ondule, IoU min 0,355 à la phase opposée (testé).
Extraction corrigée : l’inondation seule laissait le **magenta cuit enfermé** entre les passages de la vague — retiré par **seuil serré global d < 40** (le cœur des rubans est à ~72), **sans** `fill_holes` (leçon V9).

## Critères Halcyon conservés
Calques empilés (ciel / étoiles / aurore 10 frames / terrain), nommage et taille uniformes, durée uniforme, position (80, 24) sur grille 8 px, sans wrap, manifeste SHA. Viewer `apercu_arene_halcyon_v16.html`, ZIP.

7 tests dédiés PASS. Pas de test navigateur ni runtime PMDO. Généré d’après la référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.

Rebuild : `.venv/bin/python source/arene_halcyon_v16/build.py` puis `package.py`.
