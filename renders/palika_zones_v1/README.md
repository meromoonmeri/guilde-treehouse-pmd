# Palika — deux zones séparées générées

Cette livraison ne reprend pas les anciennes compositions fusionnées à la racine. Elle contient deux guides indépendants, générés séparément puis exportés en calques transparents alignés.

## Zones

1. `vast_steppe_automne_sud_nord/` — Vast Steppe en automne, avec un chemin principal lisible du sud vers le nord.
2. `foret_neigee_entree_nord_sud/` — zone distincte d’arrivée vers une entrée de forêt enneigée, avec une chaîne de montagnes de style PMD au loin.

## Convention de livraison

- canevas commun : **2048 × 1536 px** ;
- grille logique : **8 × 8 px**, soit **256 × 192 cellules** ;
- origine : `(0, 0)` ;
- calques : PNG RGBA transparents, tous plein-canevas et alignés ;
- composition : `COMPOSITION.png` ;
- édition multicouche : `zone_seche.ora` (OpenRaster) et `zone_seche.aseprite` (1 frame fixe, calques RGBA) ;
- map Tiled : `zone_seche.tmj`, sous forme d’image-layers, car ces visuels générés ne sont pas déclarés comme un atlas de tuiles Halcyon canonique.

## Ordre des calques

Du bas vers le haut :

- `00_montagnes_arriere_plan` — uniquement dans la zone enneigée ;
- `01_sol` ;
- `02_chemin` ;
- `03_bordures` ;
- `04_parois` ;
- `05_rochers` ;
- `06_vegetation_basse` ;
- `07_arbres_massifs` ;
- `08_ombres_profondeur` ;
- `09_entree_foret` — uniquement dans la zone enneigée.

Cet ordre reprend l’organisation des références Palika/Halcyon présentes dans le dépôt : sol et passage d’abord, puis reliefs, éléments de proximité, arbres/massifs et profondeur. La nomenclature eau `01_sol` à `06_cascades` de `sprites/zones_guidees` n’est pas appliquée artificiellement à ces deux zones sèches.

## Méthode et provenance

- Le générateur d’image a produit **deux compositions visuelles séparées**.
- Il a retourné des images de 1200 × 896 ; l’ajustement Lanczos vers le canevas Palika demandé 2048 × 1536 est une correction de livraison.
- Python n’a pas généré le décor : il a seulement redimensionné le guide, préparé les masques, copié les pixels générés dans des PNG transparents, aligné les exports et effectué les contrôles.
- `source/palika_zones_v1/build_layers.py` est le script reproductible de détourage, d’export et de vérification.
- `source/palika_zones_v1/verify.py` relit indépendamment les PNG, l’ORA et le TMJ.
- `manifest.json` dans chaque zone contient le SHA-256 du guide généré, les dimensions, l’ordre des layers et les contrôles.
- `apercu_palika_zones_v1.html` permet d’afficher les deux zones et de masquer/afficher chaque layer individuellement.

## Contrôles réalisés

- les deux zones sont bien deux compositions distinctes ;
- chaque calque est RGBA, 2048 × 1536, sur la même origine ;
- les masques alpha sont disjoints ;
- la recomposition ordonnée des calques est identique au `COMPOSITION.png` livré ;
- le masque du chemin atteint les bords sud et nord dans les deux zones ;
- les masques dédiés de l’entrée et des montagnes sont livrés pour la zone enneigée.

## Limites explicites

Ces PNG sont des **guides de composition générés**, pas des textures natives certifiées ni un atlas Halcyon. Aucun import PMDO, test de collisions, transition de map ou validation runtime n’a été effectué.
