# Cristal boréal V1 — couches animées multiples

Quatre couches animées ajoutées à `renders/layouts_magenta_v1/zones/cristal_boreal/`, sans retoucher la
base : `08_aurore_ciel` (onde V12 rejouée en rotation de palette, posée en voile à 96/255 sur le ciel,
8 × 120 ms), `09_eclats_cristaux` (rotation des quatre classes de luminance du relief des cristaux et de
leur raccord, 8 × 240 ms), `10_scintillement_givre` (points vifs des poses natives hors zone protégée,
sélection tournante sur 12 diagonales de 8 px, 12 × 160 ms), `11_lueur_sol` (le même plan d'aurore,
échantillonné décalé de 6 px par pose sur le sol visible, 8 × 240 ms). Les douze poses natives et les
cinq calques statiques du lot V1 sont recopiés fichier par fichier.

Scène maîtresse : 48 poses de 40 ms, cycle 1 920 ms, pile `01` → cinq calques → `09 10 11` → `08` en
voile. `SCENE_SANS_VOILE.webp` et `COMPOSITION_SANS_VOILE.png` sont la même scène sans l'aurore. Un
`.ora` de 53 calques garde toutes les poses, la pose 0 seule visible. Chaque couche a son dossier de
PNG, sa boucle WebP sans perte, son masque d'empreinte et sa provenance au `manifest.json`.

À chaque pose, la pile sans voile est égale, canal alpha compris, à la pose native correspondante sur les
167 059 px protégés : c'est le contrôle central, regenerated par `test_build.py` (18 tests PASS). Les
boucles WebP encodent moins d'images que de poses (les poses consécutives identiques sont fusionnées,
durées additionnées) : le cycle est conservé, pas le compteur.

Aucune collision, aucun warp, aucun import moteur, aucun rendu PMD Online testé ; aperçu non testé dans un
navigateur de jeu ; **art non approuvé**. Rebuild : `.venv/bin/python source/cristal_boreal_layers_animees_v1/build.py`
puis `package.py` (`--check` pour vérifier sans régénérer).
