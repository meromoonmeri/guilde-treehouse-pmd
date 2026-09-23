# Carte générée à 7 continents — multicalque

Cette version est générée à partir des références visuelles fournies au générateur d'image : la texture parchemin, les motifs cartographiques et la palette pixel-art sont repris comme direction visuelle. L'image générée est archivée dans `raws/` et n'est pas déclarée comme pixels natifs du jeu.

## Calques

- `00_fond_parchemin.png` : fond et motif papier séparés ;
- `01_continents_texture.png` : texture/terrain des 7 masses terrestres ;
- `02_cotes_et_motifs.png` : contours et reliefs ;
- `03_routes.png` : chemins de progression ;
- `04_emblemes_continents.png` : emblèmes générés ;
- `05_etat_deblocage.png` : état jeu ouvert/verrouillé.

Composition complète : `WorldMap_7_Continents_Generated.png`, 1536×1056.

## Animations

`animations/WorldMap_7Continents_v2_00.png` à `07.png` sont huit frames indépendantes de révélation progressive. Le WebP direct est fourni en complément. La boucle n'est pas présentée comme une animation canonique : c'est une animation UI générée.

## AssetSprite et intégration

`assetsprite/WorldMap_7Continents_v2_AssetSprite.png/.json` contient les sept marqueurs. `world_map_state.json` décrit les identifiants, positions et états initiaux pour remplacer les calques d'état en jeu.

## Provenance

- Références visuelles utilisées par le générateur : `Explorers_of_Sky_-_World_Map.png` et `MapAssetsPMD2.webp` ;
- génération enregistrée : `raws/world_map_7_continents_generated.png` ;
- la génération est une composition guidée, pas une extraction pixel native.
