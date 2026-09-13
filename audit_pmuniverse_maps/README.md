# Audit de composition des cartes PMUniverse / PMUniverse map-composition audit

> **Résultat court / Short result:** PMUniverse ne stocke pas une carte sous la forme d'une grande image, ni dans une unique base de tilesets. Chaque cellule de carte référence jusqu'à **dix emplacements visuels** et leurs indices de tileset. Les pixels des tiles vivent côté client dans des conteneurs `Tiles0.tile` à `Tiles10.tile`; la composition (coordonnées, layers, indices de tile et de tileset) est persistée côté serveur dans `Content_Data.zip!/pmu_data.sql`, table `map_tiles`.

Ce dossier est un inventaire de **métadonnées**, sans pixels d'assets PMUniverse et sans noms de maisons de joueurs. Il a été produit le 2026-09-13 depuis les commits et l'archive hachée déclarés dans `summary.json`.

## Fichiers livrés / Delivered files

| Fichier | Contenu |
| --- | --- |
| `summary.json` | Provenance reproductible, comptages globaux par layer, pairings d'animation, recensement alpha des onze tilesets et références non résolues. |
| `all_maps_layer_catalog.json` | Les 17 028 cartes connues, avec type, dimensions, révision, nombre de lignes `map_tiles`, et pour chacun des dix slots: cellules non nulles, tilesets employés, nombre de références distinctes et modes alpha. Il ne contient pas de noms de maisons. |
| `waterfall_water_bridge_maps.json` | Les 52 cartes standard dont le nom officiel contient `water`, `cascade` ou `bridge`. Pour **chaque cellule non nulle** et **chaque layer**, ce fichier fournit `x`, `y`, `tileset`, `tile` et `alpha`. Il est donc le catalogue coordonné des références eau/cascade/pont. |
| `../source/audit_pmuniverse_map_layers.py` | Script reproductible qui a généré les trois JSON en une lecture streaming de la dump SQL et sans exporter les PNG inspectés. |

`alpha` vaut `opaque`, `mixed`, `empty`, ou `unresolved`. `unresolved` ne signifie pas transparent: le serveur référence un index absent de la copie cliente examinée, donc son PNG et son alpha ne peuvent pas être affirmés.

## Modèle réel de couche / Actual layer model

Chaque ligne `map_tiles` est une cellule `(MapID, X, Y)`. Elle contient les dix couples **numéro de tile / numéro de tileset** suivants:

1. `Ground` / `GroundTileset`
2. `GroundAnim` / `GroundAnimTileset`
3. `Mask` / `MaskTileset`
4. `MaskAnim` / `MaskAnimTileset`
5. `Mask2` / `Mask2Tileset`
6. `Mask2Anim` / `Mask2AnimTileset`
7. `Fringe` / `FringeTileset`
8. `FringeAnim` / `FringeAnimTileset`
9. `Fringe2` / `Fringe2Tileset`
10. `Fringe2Anim` / `Fringe2AnimTileset`

Les paires sont `(Ground, GroundAnim)`, `(Mask, MaskAnim)`, `(Mask2, Mask2Anim)`, `(Fringe, FringeAnim)` et `(Fringe2, Fringe2Anim)`. À chaque phase, le slot animé non nul **remplace** le slot statique associé à cette cellule; ce n'est pas une superposition d'une frame additionnelle. `MapViewer.cs` inverse `DisplayAnimation` toutes les 250 ms. Le renderer dessine d'abord Ground, Mask puis Mask2; les deux Fringe sont dessinés dans le passage de premier plan, après le dessin du monde/entités.

**English.** Every tile-grid record carries ten visual references, arranged as five static/alternate pairs. A non-zero alternate reference replaces its static counterpart on the 250 ms alternate phase. Ground, Mask and Mask2 render before the entity/world pass; Fringe and Fringe2 render in the later foreground pass.

## Ce que prouvent les données / What the data proves

* **17 028** enregistrements de carte, dont **17 002** avec au moins une ligne `map_tiles`; **12 672 441** lignes de cellules associées à une carte identifiée. Une ligne de dump dont `MapID` est vide est explicitement exclue et comptée séparément dans `map_tile_rows_excluded_empty_map_id`.
* Les types d'ID observés sont 2 000 `standard`, 11 406 `house`, 2 494 `random_dungeon` et 1 128 `instanced`. Les 26 cartes sans cellules sont conservées dans le catalogue, avec des statistiques de layer à zéro.
* L'usage global non nul est entièrement détaillé dans `summary.json`. En particulier: `ground` 10 691 653 cellules, `ground_animation` 318 383, `mask` 6 532 578, `mask_animation` 122 717, `mask_2` 441 392, `mask_2_animation` 42 854, `fringe` 393 435, `fringe_animation` 35 524, `fringe_2` 159 970, `fringe_2_animation` 40 795.
* La recherche de noms ne constitue **pas** un label sémantique de tile: les fichiers de tileset ne nomment pas un asset « water », « waterfall » ou « bridge ». L'attribution vérifiable est donc le triplet: nom officiel de carte + coordonnées/layer + couple `(tileset, tile)` dans le JSON dédié.

### Exemples vérifiables eau / cascade / pont

| Carte | Grille | Preuve de calques |
| --- | ---: | --- |
| `s1060` — **Cortek Canyon Great Waterfall** | 51×51 | 2 600 Ground, 1 795 Mask, 825 MaskAnim, 142 Mask2, 3 Mask2Anim, 85 Fringe, 2 FringeAnim, 5 Fringe2, 1 Fringe2Anim; 5 458 références coordonnées dans le catalogue. |
| `s713` — **Secret Waterfall Cave** | 20×15 | Ground 299, Mask 120, MaskAnim 296, Mask2 120, Mask2Anim 2, Fringe 5, FringeAnim 4. |
| `s1074` — **Waterfall Cave** | 20×15 | Ground 300, Mask 30 et MaskAnim 6: animation d'alternance réellement référencée. |
| `s796` — **Sun Bridge** | 51×51 | Ground 2 601, Mask 389, Mask2 20, Fringe 281, FringeAnim 1; 3 292 références coordonnées. |

Les cartes officielles waterfall/bridge de l'inventaire incluent `s713`, `s796`, `s1050`–`s1058`, `s1060` et `s1070`–`s1074`. Les 52 entrées complètes, y compris les autres noms contenant water/cascade/bridge, sont dans `waterfall_water_bridge_maps.json`.

## Transparence / Transparency conclusion

Les 52 486 PNG 32×32 indexés dans les onze conteneurs `.tile` ont tous été décodés et leur canal alpha a été inspecté:

| Alpha des PNG | Nombre |
| --- | ---: |
| entièrement transparent (`empty`) | 17 809 |
| partiellement transparent (`mixed`) | 20 891 |
| entièrement opaque (`opaque`) | 13 786 |

Les tiles PMUniverse ne sont donc ni tous opaques, ni tous « sur un fond transparent ». La transparence alpha est fréquente, particulièrement appropriée aux masques et premiers plans, mais les bases de terrain sont souvent opaques. L'absence de référence (`0`) demande au renderer de ne rien dessiner; ce n'est pas un PNG de fond. Aucune conclusion de chroma-key magenta n'est nécessaire ou justifiée ici: les conteneurs utilisent des PNG avec alpha.

## Limite de snapshot importante / Important snapshot limitation

La dump serveur fait référence à **711 couples `(tileset, tile)` distincts** absents des onze fichiers `.tile` présents dans le snapshot client audité, pour **9 158 cellules**. La ventilation par tileset est dans `summary.json`; les deux cibles nommées affectées sont `s122` (une cellule Fringe2) et `s818` (trois cellules Ground). Les autres 50 cartes eau/cascade/pont ont des références entièrement classées par alpha dans ce snapshot.

Cela établit que cette archive serveur et ce checkout client ne constituent pas, ensemble, une distribution graphique parfaitement synchronisée pour chaque carte historique. La base serveur contient les **références de composition**, pas une copie de tous les pixels. Ne remplacez pas ces références manquantes par des tiles supposés: récupérez une distribution cliente correspondant à la même révision si une reconstruction visuelle bit-à-bit de toutes les cartes est nécessaire.

## Où sont les données / Where the data lives

### Client

* `resources/GFX/Tiles/Tiles0.tile` … `Tiles10.tile`: onze conteneurs indexés de PNG, chacun avec des tiles 32×32 et leur alpha. Ils sont les pixels utilisés par un couple `(tileset, tile)`.
* `resources/GFX/Maps/Map-*.dat`: caches de cartes locaux chiffrés. Le code `MapHelper.SaveLocalMap` sérialise un `MapData|V9` puis les lignes `Tile|...` et chiffre les octets Unicode. Les fichiers `.dat` observés ne sont pas la source de cette inventaire: la clé/révision effectivement applicable aux fichiers fournis n'a pas été démontrée, donc aucun contenu `.dat` n'est présenté comme déchiffré.

### Server

* `PMU-Server/Content_Data.zip!/pmu_data.sql`: dump peuplée employée pour l'audit.
* `map_general`: limites/dimensions et révision; `map_data`: métadonnées, dont les noms officiels utilisés seulement pour cibler les cartes standard eau/cascade/pont.
* `map_standard_data`, `map_house_data`, `map_rdungeon_data`, `map_instanced_data`: typage de carte.
* `map_tiles`: persistance de la grille et des dix références visuelles ci-dessus. `DataManager/Maps/MapDataManager.cs` sélectionne exactement ces colonnes et les sauvegarde à nouveau dans `map_tiles`.

## Reproduire / Reproduce

Depuis la racine de ce dépôt, avec les checkouts locaux PMUniverse et Pillow installés dans le venv de travail:

```bash
.cache/inspect-venv/bin/python source/audit_pmuniverse_map_layers.py \
  --client-repo .cache/pmuniverse-audit/clones/PMU-Client \
  --server-repo .cache/pmuniverse-audit/clones/PMU-Server \
  --audit-date 2026-09-13 \
  --out audit_pmuniverse_maps
```

Le parseur lit `pmu_data.sql` directement depuis le ZIP, en streaming (environ 166 secondes lors de cet audit), et n'extrait ni la dump ni les PNG dans les fichiers produits.

## Pistes de code / Code evidence

Les chemins ci-dessous correspondent au snapshot client/serveur déclaré dans `summary.json`:

* `PMU-Client/Client/Maps/MapHelper.cs`, notamment la sérialisation V9 et l'ordre des dix valeurs `Tile`.
* `PMU-Client/Client/Maps/Tile.cs`, propriétés de chaque référence graphique.
* `PMU-Client/Client/Graphics/Renderers/Maps/MapRenderer.cs`, sélection/replacement static-versus-animation et les passes Ground/Mask/Mask2/Fringe/Fringe2.
* `PMU-Client/Client/Widgets/MapViewer.cs`, bascule de phase toutes les 250 ms.
* `PMU-Server/DataManager/DataManager/Maps/MapDataManager.cs`, lecture et écriture SQL des colonnes `map_tiles`.
