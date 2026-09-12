# Métano V3 — vrais PNG destinés à « PNG to Tileset »

## Ce lot corrige la méthode de rendu

Deux premières scènes **sèches de calibration**, construites avec des blocs de falaises natifs entiers, et non une sélection de fragments de 8 px guidée par la couleur. Les compositions générées précédentes restent des références de forme ; leurs pixels ne sont pas importables comme textures canoniques.

**Ce ne sont pas encore les remplacements complets des deux grandes zones 2048 × 1536.** Ces scènes plus petites servent à vérifier dans PMDO la taille réelle et la continuité des blocs avant de généraliser. Aucun ancien fichier n’a été remplacé.

- `01_cirque/METANO_V3_CIRQUE_SCENE.png` — **1016 × 512 px**, 127 × 64 cellules de 8 px.
- `02_terrasses/METANO_V3_TERRASSES_SCENE.png` — **1016 × 768 px**, 127 × 96 cellules.
- Chaque dossier contient également `…_SOL.png` et `…_FALAISES.png`, calques RGBA au même canevas et à la même origine.
- `METANO_V3_TEMOIN_64x96.png` — un retour de falaise copié exactement de Métano, pour comparer la taille et le rendu après import.
- `METANO_V3_MODULE_*.png` — quatre blocs canoniques séparés et répétables/assemblables dans les conditions illustrées par les scènes.

Le canevas plus petit n’a pas été obtenu par réduction : **les pixels et les dimensions des blocs restent natifs, à ×1**. Aucun passage de 2048 vers 1016 par rééchantillonnage. Pas de filtre, agrandissement global, recoloration ni colonne d’ombre de 8 px répétée artificiellement.

## Import conseillé dans PMDO Dev

1. Importer d’abord **`METANO_V3_TEMOIN_64x96.png`**, avec **taille de tuile = 8 px**. Le bloc couvre 8 × 12 cellules ; sélectionner l’ensemble du bloc, pas une seule cellule, pour comparer sa taille à la référence.
2. Importer ensuite `METANO_V3_CIRQUE_SCENE.png`, puis `METANO_V3_TERRASSES_SCENE.png`, toujours à **8 px**. Utiliser une Ground map à cellules de 8 px pour ce test, comme le terrain Métano de référence.
3. Ne pas modifier l’échelle du PNG et ne pas redimensionner sa texture avant import. Comparer au même zoom caméra, idéalement avec le même sprite Pokémon.
4. Pour des couches séparées, importer les PNG `…_SOL` et `…_FALAISES`, puis poser les rectangles aux **mêmes coordonnées**, sol dessous. Ne pas ajouter en plus le PNG `…_SCENE` : il contient déjà les deux couches composées.
5. Les PNG d’import n’ont aucun texte, quadrillage, cadre ou fond de contrôle ajouté. Le calque falaises est transparent hors de son contenu ; le sol et la scène complète sont opaques.

### Attention aux noms des fichiers

L’importeur utilise le **nom de fichier sans extension** comme nom du tileset. Deux PNG nommés `canonique_sec.png` dans deux dossiers différents peuvent donc viser le même tileset. Les fichiers de ce lot ont volontairement des noms **uniques**, préfixés `METANO_V3_`. Ne pas les renommer tous `scene.png` ou `sol.png` et ne pas employer le nom d’une feuille canonique existante.

Le chemin de code consulté ne redimensionne pas les blocs dans `SaveTileSheet` : il découpe des rectangles de la taille choisie, conserve leurs coordonnées et ignore les cellules transparentes. Ses divisions entières peuvent omettre un bord si les dimensions ne sont pas divisibles par la taille choisie. Tous les PNG du lot sont divisibles par **8**.

Ces observations portent sur RogueEssence au commit `8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b`, pas sur une exécution de l’installation utilisateur :

- [Dialogue et import du tileset](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence.Editor.Avalonia/ViewModels/Content/TilesetEditViewModel.cs) : `btnImport_Click`, `tryImport`.
- [Découpage PNG](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence/Dev/ImportHelper.cs) : `SaveTileSheet`.
- [Unité graphique minimale](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence/Content/GraphicsManager.cs) : `TEX_SIZE = 8`. La taille proposée par le dialogue vient de `GraphicsManager.TileSize`, liée à la configuration des tuiles de donjon ; ne pas supposer qu’elle vaut déjà 8.

## Structure des blocs et contrôles

Les quatre rectangles sources sont conservés sans transformation : descente ouest **224 × 336**, face complète **64 × 96**, retour arrondi **64 × 96**, remontée est **216 × 240**. Les rectangles de face et retour sélectionnent la couronne, la face et le pied utiles au raccord horizontal ; les prolongements nord appartenant au contexte original ne sont pas ajoutés au milieu d’une paroi.

`manifest.json` indique les rectangles source, dimensions, positions et empreintes des scènes. `verification.json` confirme :

- empreintes Git des sources Base et Cliffs épinglées ;
- quatre modules identiques à leurs rectangles natifs ;
- aucune mise à l’échelle des modules ni superposition accidentelle de leurs rectangles ;
- sol + falaises identiques aux PNG des scènes ;
- **11 PNG** découpés/recomposés en cellules de 8 px, en conservant les coordonnées et en omettant les cellules transparentes : **0 différence de pixel** ;
- noms de tilesets uniques.

Le test de découpage reproduit le principe de l’importeur, **pas une exécution du moteur/GPU PMDO**. Les raccords nouveaux ont été inspectés visuellement, mais la qualité artistique ne se réduit pas à ces assertions. Aucun test en jeu, collision ou transition n’est déclaré. L’eau animée et les variantes nuit ne font pas partie de ce premier lot sec de calibration.

## Reconstruction

```sh
.venv/bin/python source/build_metano_import_png.py
.venv/bin/python source/verify_metano_import_png.py
.venv/bin/python source/package_metano_import_png.py
```

Sources artistiques : **Palikadude/Halcyon**, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`, Palika et contributeurs. Nouvelles compositions non officielles ; respecter les droits et conditions des ressources d’origine.
