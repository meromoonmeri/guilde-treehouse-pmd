# Grotte glaciaire boréale V1 — chemin Sud → Nord

## Livraison visuelle

Nouvelle zone glaciale **768 × 640 px**, sur grille de présentation 8 px : un chemin enneigé arrive au **sud**, remonte sans coupure vers une **grotte prise dans la falaise nord**, sous un ciel nocturne dont l’aurore vit sur son propre calque. La scène est une proposition de rendu PMD et un document de travail éditable ; ce n’est ni un tileset natif, ni une Ground PMDO, ni une collision jouable.

## Méthode Guilde appliquée

1. Trois images originales ont été générées séparément : terrain complet sur magenta, ciel sans aurore, planche 2 × 4 d’aurores sur magenta.
2. Le magenta extérieur est retiré par inondation depuis les bords, sans supprimer les accents violets enfermés dans les rubans.
3. Le terrain reste une composition complète — **aucun morceau de map existante n’est assemblé** — et est réparti en surfaces visibles indépendantes : neige, chemin, vide de grotte, falaise nord, deux falaises latérales et premier plan.
4. Les quatre poses générées les plus cohérentes sont ancrées au même repère ; leurs intercalaires sont fondus en alpha prémultiplié. L’aurore a 16 phases de 120 ms (1,92 s), sur transparence, **sans wrap ni défilement**.
5. Chaque rendu est vérifié : séparation exacte des calques, absence du fond magenta extérieur, chemin continu Sud → seuil nord, animation bouclée, ORA, GIF/WebP et aperçu autonome.

## Fichiers

- `bruts/` — sources générées exactes, magenta et ciel conservés.
- `calques/` — ciel opaque et 7 plans terrain RGBA alignés.
- `animation/aurore_frames/` — 16 overlays transparents 768 × 640 ; `aurore_16frames.webp` est la boucle sans perte.
- `animation/keyposes/` — les quatre poses générées retenues et ancrées ; les quatre autres restent visibles dans le brut, mais ne sont pas intégrées car leurs silhouettes dérivent trop pour une boucle propre.
- `masques/` — masques binaires des surfaces visibles.
- `grotte_glaciaire_boreale_v1.ora` — scène multicouche, phase 0 incluse.
- `review/` — GIFs, planches, scène pleine définition et tracé de contrôle du passage (ce dernier n’est pas un asset de jeu).
- `placement_recipe.json` / `manifest.json` — ordre de rendu, timing, provenance, positions et limites.
- `apercu.html` dans le ZIP ; `apercu_grotte_glaciaire_boreale_v1.html` à la racine du dépôt : lecture/pause, phases, calques, grille et tracé Sud → Nord.

## Animation et limites

L’aurore est une **nouvelle animation proposée**, construite à partir de poses générées avec la référence PMD fournie : ce n’est pas un cycle officiel extrait du jeu. Le ciel et le terrain restent fixes. Les huit poses du brut ne sont pas toutes acceptées automatiquement : l’audit de recouvrement sélectionne 0–3 afin de conserver une déformation douce autour d’un ancrage commun ; 4–7 sont archivées dans la planche source, pas silencieusement recyclées.

Les images de référence Pokémon restent la propriété de leurs ayants droit. Les rendus ici sont générés, inspirés par la DA fournie, et **ne prétendent pas être des pixels canoniques ni une autorisation de redistribution**. Aucun import PMDO, parallax moteur, collision, warp, test GPU ou approbation artistique utilisateur n’est déclaré. Le contrôle de chemin est géométrique ; il ne remplace pas les collisions moteur.

## Reproduction

```sh
.venv/bin/python source/grotte_glaciaire_boreale_v1/build.py
.venv/bin/python source/grotte_glaciaire_boreale_v1/package.py
```
