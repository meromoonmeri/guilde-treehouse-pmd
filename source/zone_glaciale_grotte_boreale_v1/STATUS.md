# Zone glaciale / grotte boréale V1 — état

Demande utilisateur : créer une nouvelle zone glaciale avec falaises, grotte de glace, chemin clair du **sud vers le nord** et ciel boréal animé.

## Livré

- Une composition générée entière, conservée sur magenta puis détourée : vallée de glace, grande cavité naturelle au nord, parois latérales et cristaux.
- Un ciel de nuit généré séparément, avec 32 petites composantes d’étoiles séparées en overlay transparent.
- Une aurore générée séparément sur magenta : 16 calques PNG 1264 × 1008, 100 ms, boucle 1,6 s, WebP et GIF.
- Une animation non-scrollée : onde transversale verticale par colonne et cycle de palettes cyan / violet-rose à contre-courant. L’asset indexé, l’alpha et les palettes sont fournis séparément.
- Huit plans de terrain : sol reconstitué sous relief, sol visible, chemin, falaise nord, falaises latérales, cadre de grotte, obscurité intérieure et détails avant.
- Un ORA avec la phase 0, 10 masques/contrôles, scènes d’échantillon, deux planches et un viewer HTML autonome avec lecture, pas-à-pas, grille, visibilité de chaque calque et export de la frame affichée.
- `verify.py` produit `verification.json` : 53 contrôles PASS au dernier build.

## Méthode et garde-fous

Les pixels retenus du terrain ne sont pas redimensionnés : le terrain est simplement translaté de 200 px pour ne pas sacrifier le ciel. La partition des sept calques de terrain visibles recompose le terrain détouré exactement. Le sol reconstitué est intentionnellement sous-jacent et donc exclu de cette égalité.

Le contrôle `masques/09_corridor_geometrique_sud_nord.png` prouve une continuité géométrique du centre sud `(632,1007)` au seuil `(632,548)` avec demi-largeur de 25 px. Il ne constitue pas une collision PMDO.

## Ne pas affirmer

Ne pas qualifier ces rendus générés de tiles canoniques, de carte PMDO importable ou de test runtime. Le ciel/aurore, les colliders, l’occlusion du héros et la transition vers le donjon restent à intégrer puis tester. L’art reste proposé, non approuvé.

## Commandes

```sh
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/build.py
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/verify.py
.venv/bin/python source/zone_glaciale_grotte_boreale_v1/package.py
```
