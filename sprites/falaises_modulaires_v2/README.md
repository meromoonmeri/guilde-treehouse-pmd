# Falaises de Métano — décor et morceaux modulaires V2

Cette livraison répond aux deux usages : **un nouveau grand décor** et **des fragments de falaise à assembler**, avec les tuiles de référence de Métano Town. Les trois anciens layouts restent dans `../falaises_metano/` et ne sont pas remplacés.

## Les PNG à regarder

- **`rendu_collection.png`** : présentation générale du nouveau décor, détail de cascade, dix nouvelles maisons et sélection de morceaux natifs.
- **`rendu_falaise.png`** : nouveau décor **sans maisons**, 2048 × 1536 px, soit **256 × 192 cases de 8 px**.
- **`rendu_village.png`** : même décor avec les dix nouvelles maisons, résolution native, sans légende ni grille.
- **`planche_modules.png`** : planche légendée des quinze morceaux/phases, vue agrandie ×2 ; pas un atlas à importer.
- `../maisons_organiques_v2/planche.png` : présentation détaillée des dix nouvelles maisons.

## Morceaux issus des tuiles originales

La banque contient **11 fragments fixes + 4 phases de cascade** :

1. Rebord herbeux — 64 × 24 px
2. Paroi répétable — 64 × 48 px
3. Pied de paroi — 64 × 16 px
4. Section complète — 64 × 112 px
5. Escalier natif — 64 × 112 px
6. Coude ouest — 64 × 112 px
7. Coude est — 64 × 112 px
8. Palier ouest — 32 × 112 px
9. Palier est — 32 × 128 px
10. Entrée rocheuse — 64 × 144 px
11. Sol herbeux — 64 × 64 px
12–15. Cascade — quatre phases de 64 × 136 px

Les fragments sont **extraits sans redimensionnement ni redessin** de `Metano_Town_Cliffs.tile`, des patches de terrain natifs déjà vérifiés et des quatre frames de cascade originales. `modules.json` donne le fichier source, son SHA-256, le rectangle source et le rectangle de sélection dans l'atlas. La vérification obtient **zéro différence de pixels source** après remise en alpha prémultiplié des PNG.

Les quelques pixels d'alpha partiel des ressources natives sont convertis en alpha droit pour les PNG d'éditeur ; le `.tile` conserve la représentation prémultipliée. Aucun filtre de couleur n'est appliqué.

### Planche d'import

- `Falaises_Metano_Modules.png` : atlas transparent **400 × 480 px**.
- Emplacements de 80 × 160 px ; les fragments y restent à leur taille native et sont positionnés sur la grille de 8 px.
- `Falaises_Metano_Modules.tsj` : Tiled, cellules de 8 px. Sélectionner les rectangles décrits par `atlas_rect_cells`, **pas la totalité du cadre vide**.
- `Falaises_Metano_Modules.tile` : nouvelle ressource PMDO, 50 colonnes × 60 lignes.
- `01_rebord.png` … `15_cascade_4.png` : fichiers individuels.

Les morceaux ne constituent pas un autotile automatique couvrant toutes les formes possibles. Les raccords doivent être choisis et placés ; les angles gardent la perspective de la source. La paroi centrale se répète pour prolonger une face ; les rebords et pieds terminent l'assemblage.

Les quatre cascades représentent **des phases, pas quatre types de chute**. Les animations du TSJ sont portées par les cellules de la première phase. Pour PMDO, les Frames sont dans `modules.json`. Cadence de présentation proposée : 10 ticks/phase ; elle n'est pas prouvée comme cadence autonome de ces rectangles dans la carte originale.

## Nouveau décor : Le balcon des racines

`decor/04_balcon/` contient :

- `terrain.png` : terrain fixe, relief et escaliers ;
- `eau_1.png` … `eau_4.png` : calques transparents d'eau ;
- `layout_1.png` … `layout_4.png` : décor sans maisons, quatre phases ;
- `structures.png` : les dix maisons sur un calque transparent indépendant ;
- `village_1.png` … `village_4.png` : décor avec maisons ;
- `layout.tmj` : carte Tiled à deux calques, terrain et eau ;
- `village.tmj` : variante à trois calques, maisons séparées ;
- `layout.json` : reliefs et positions des escaliers/chutes.

Les cartes font toutes **2048 × 1536 px**, grille **8 × 8 px**, donc **49 152 cases**. Les maisons conservent leurs propres atlas ; le village TMJ utilise un chemin relatif vers `../../../maisons_organiques_v2/Maisons_Organiques_V2_jour.tsj`. Garder l'arborescence des dossiers lors du téléchargement.

L'atlas du décor `decor/Falaises_V2_Decor.{png,tile,tsj}` porte un nom distinct de celui des trois layouts précédents. Ses animations natives figurent dans `decor/kit.json`.

### Ce qui est nouveau, ce qui reste identique

- **Fragments modulaires :** pixels natifs extraits, pas de génération d'image.
- **Grand décor :** nouvelle géométrie composée avec les textures natives. Les parois sont prolongées par répétition, les cascades longues par répétition de leur milieu ; elles ne sont donc pas des extractions intactes de 64 × 136 px.
- **Rivières du décor :** nouveaux contours et vaguelettes, avec les couleurs de Métano.
- **Maisons :** dix nouvelles créations au générateur, références originales en entrée, pas des extractions du jeu.

## Import PMDO et limites

Importer les `.tile` souhaités dans `Content/Tile/` puis **réindexer les ressources**. Ne pas écraser un index global avec un index partiel. Ces ressources visent une Ground à **TexSize = 1**, soit 8 px. Les noms sont distincts des ressources originales de Halcyon et du premier lot.

Les JSON sont des manifests auxiliaires, les TMJ sont des cartes Tiled : **aucun `.rsground` intégré n'est fourni**. Le raccord à Métano, les collisions, l'occlusion, les entrées et scripts sont à configurer dans le moteur. Les chemins, ponts éventuels et accès des dix maisons restent à vérifier ; le placement des maisons est une proposition visuelle, pas un village jouable validé.

## Reconstruction

Depuis la racine du dépôt, Pillow requis :

```sh
python source/build_houses_metano.py --organic-v2
python source/build_cliff_layouts.py \
  --config source/falaises_modulaires_v2/layout_config.json \
  --output sprites/falaises_modulaires_v2/decor \
  --sheet-name Falaises_V2_Decor --no-preview
python source/build_modular_cliffs_v2.py

python source/verify_houses_metano.py --organic-v2
python source/verify_cliff_layouts.py \
  --output sprites/falaises_modulaires_v2/decor \
  --expected-maps 1 --sheet-name Falaises_V2_Decor
python source/verify_modular_cliffs_v2.py
```

Tests : pixels des quinze fragments contre leurs sources, atlas natif, références d'animation, nouveau décor recomposé depuis Tiled aux quatre phases, calque maisons et quatre rendus du village. Les tests des anciens lots passent aussi. Ouverture dans PMDO/Tiled non testée.

## Attribution

Textures et tuiles de référence : **Palika / Halcyon**, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Voir les [crédits de Halcyon](https://github.com/Palikadude/Halcyon#credits), notamment Jaifain pour les animations de rivière de Métano. La nouvelle composition et les maisons ne sont pas des créations officielles. Vérifier les autorisations des auteurs avant redistribution publique de leurs ressources.
