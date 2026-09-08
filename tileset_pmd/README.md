# Luminous Spring PMDO — reconstruction Halcyon

Ce dossier est la reconstruction de `luminoussspring.png` avec la logique technique de **Luminous Spring / Halcyon de Palikadude**. La seconde image fournie sert de référence de construction et de lisibilité, pas de texture à copier.

## Ce qui est construit

- même ambiance nocturne bleu-vert et même lumière cyan-blanche que l'image source ;
- cellules de sol PMDO de **8 × 8 px**, comme les `.tile` de Halcyon ;
- modules artistiques de 16 px, toujours composés de cellules 8 px ;
- calques inspirés de la grammaire Halcyon : `Base`, `River`, `Cliffs`, `Shadows`, `Objects Under`, `Objects`, `Objects Over`, `Fringe` ;
- rives et bassin modulaires : quatre directions, coins, pierres et transitions ;
- eau propre et répétable ;
- arbres indépendants, transparents et repositionnables ;
- lumière indépendante avec **8 frames réellement différentes**, même canvas 32 × 32 px, même ancre `[16, 31]` ;
- animation de rivière PMDO avec **4 frames**, `FrameLength = 10`, calquée sur la logique observée dans `Altere_Pond_River_Animations.tile` ;
- carte Tiled 64 × 64 cellules et compagnon `.rsground` PMDO.

## Fichiers importants

```text
planches/
  base.png                  planche Base
  river.png                 planche eau et rives
  cliffs.png                planche pierres, coins et contours
  fringe.png                planche herbes / franges
  objects.png               rochers, roseaux et éléments indépendants
  objects_under.png
  objects_over.png
  shadows.png
  river_animations.png      cellules animées 8 × 8
  05_lumiere_frames.png     8 frames de lumière, en bande horizontale

aseprite/05_lumiere_spring.aseprite
  animation 8 frames, 32 × 32 px, 100 ms/frame

tiled/luminous_spring_pmdo.tmj
  carte éditable, grille Tiled 8 × 8, calques PMDO

tiled/tilesets/*.tsx
  tilesets Tiled séparés par calque

pmd/Content/Tile/*.tile
  sheets binaires 8 × 8 compatibles avec le format RogueEssence/PMDO

pmd/Data/Ground/luminous_spring_pmdo.rsground
  squelette de zone PMDO avec la même pile de calques et l'animation de rivière

preview/luminous_spring_pmdo_animation_board.png
  aperçu recomposé + ligne des frames de lumière

source/generated/
  études issues du générateur et configuration de prompt. Elles servent à fixer
  la direction artistique ; aucune n'est découpée comme texture finale.
```

## Reproduire

Depuis la racine du dépôt :

```bash
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
.venv/bin/python tileset_pmd/build_pmdo_zone.py
.venv/bin/python tileset_pmd/verify_pmdo_zone.py
```

Aseprite peut ouvrir `aseprite/05_lumiere_spring.aseprite`. Tiled peut ouvrir `tiled/luminous_spring_pmdo.tmj` et afficher la grille de 8 px.

## Animation

La lumière n'est pas une image dupliquée : le script crée huit dessins distincts avec variation de largeur de faisceau, position du noyau, diffusion en marches de pixels et scintillements. L'ancre reste constante pour éviter le tremblement en jeu.

La nappe d'eau utilise la logique PMDO/Halcyon : les cellules animées restent dans leur calque `River Animations`, et chaque cellule possède une séquence de quatre coordonnées dans `river_animations.tile`, avec une durée commune de 10 ticks. Cela permet à PMDO de boucler l'eau sans modifier la géométrie de la rive.

## Contrôle magenta

Les planches sont transparentes pour l'intégration. Pour contrôler les ouvertures, les contours et les éléments séparés comme dans la méthode de la guilde, importer chaque planche sur un calque et placer un fond `#FF00FF` sous la composition. Aucun élément important n'est fusionné dans un arrière-plan opaque.
