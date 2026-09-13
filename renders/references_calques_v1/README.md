# Références — nouveaux calques V1

Nouvelles générations réalisées à la demande de l’utilisateur. Ne sont pas les PNG approuvés puis perdus lors de l’interruption, ni leur séparation pixel-identique.

## Aperçus
- [Coucher](coucher/composition.png) · [animation](coucher/animation.webp)
- [Nuit](nuit/composition.png) · [animation](nuit/animation.webp)
- [Guilde](guilde/composition.png)
- Galerie autonome : `apercu_references_calques_v1.html` à la racine, visibilité et téléchargement par calque.

## Pile commune, PNG RGBA 960 × 600
1. `01_ciel` : fond seul, sans nuages ni étoiles.
2. `02_etoiles` : points séparés, placement déterministe reconstruit.
3. `03_nuages` : deux sprites extraits de la planche générée, selon ambiance.
4. `04_lune_halo` pour nuit, `04_soleil` pour coucher ; absent de la guilde.
5. `05_mer` pour côtes ; `05_montagnes_foret` pour guilde.
6. `06_reflet` : phase initiale ; `reflet/00.png` à `63.png`, 80 ms chacune, boucle de 5,12 s ; absent de la guilde.
7. `07_falaise` : terrain transparent, sans bâtiment ni décoration.

Les neuf originaux générés sont conservés dans `bruts/`. Fond magenta retiré des sprites ; complétion du halo par alpha radial. Mise en scène par redimensionnement nearest-neighbor ; ce ne sont pas des tuiles natives. Les montagnes et la forêt constituent ensemble un calque distant.

## Animation et limites
Reflet reconstruit par bandes irrégulières fixes dont l’opacité varie sinusoïdalement ; le ciel, l’astre, l’eau de base et le terrain restent fixes. Pas de récupération d’une animation originale, pas de modification du mod natif PMDO. La référence GIF de guilde ne possède qu’une image.

Les falaises sont des propositions générées guidées par la référence Métano, sans certification palette/couronne native. La version nocturne du terrain utilise exactement `source/cote_v4_abyss/night.py`. Les dessins et proportions restent à valider visuellement par l’utilisateur.

## Reproduction et contrôles
Installer Pillow et numpy, puis exécuter `source/references_calques_v1/build.py` et `gallery.py`. `verification.json` consigne les dimensions et l’égalité pixel par pixel entre recomposition des calques exportés et nouvelles compositions. 128 images de reflet vérifiées. Ces contrôles ne constituent pas une validation en jeu.
