# Forêt Magenta V1 — une map, cinq calques, textures canoniques

## Objectif

Cette passe applique exactement la méthode demandée, **une seule map à la fois** :

1. générer la composition complète sur fond magenta `#FF00FF` ;
2. normaliser le guide à la taille de la map et contrôler les quatre coins ;
3. utiliser le guide uniquement pour verrouiller la composition et la silhouette ;
4. reconstruire la composition finale avec les pixels canoniques déjà audités ;
5. livrer une Ground PMDO avec exactement cinq calques différents.

La deuxième entrée rocheuse n’est pas incluse dans cette passe. Elle sera traitée séparément après validation de cette forêt.

## Map livrée

- `forest_magenta_v1` — 512 × 640 px, grille 64 × 80 cellules de 8 px ;
- arrivée au sud : 224,632,64×8 ;
- seuil nord : 240,136,32×16 ;
- chemin sud → nord contrôlé ;
- aucun warp ou donjon inventé.

## Les cinq calques finaux

1. `01_sol_chemin` — sol et chemin de terre continus ;
2. `02_vegetation_arriere` — canopée arrière ;
3. `03_cliff_grotte` — falaise blanche et ouverture de grotte ;
4. `04_arbres` — troncs et canopées d’arbres complets ;
5. `05_premier_plan` — pierres et végétation au pied de falaise.

Les couches finales sont composées exclusivement depuis les PNG V3 et leurs provenances `.npz`. La composition finale recomposée est identique au témoin canonique V3 avec zéro différence de pixel. Les pixels du guide généré sur magenta ne sont pas copiés dans les textures finales.

## Guide magenta

Le guide généré est conservé dans `provenance/guide/forest_cave_layout_magenta.png`, avec sa version alpha nettoyée. Il sert à montrer le passage générateur → fond chroma → silhouette ; il ne doit pas être importé comme texture de jeu.

Une image générée guidée par des références PMD n’est pas une preuve de pixels natifs. La provenance du matériau final est donc explicitement séparée dans `provenance/v3_source/` et `provenance/final_layers/`.

## Installation PMDO

Copier `exports/forest_cave_magenta_v1_pmdo/` dans `PMDO/MODS/`, activer le mod **Forêt Magenta V1 — textures canoniques**, puis ouvrir `forest_magenta_v1` dans l’éditeur Ground.

Pour fusionner dans un mod existant :

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/mon_mod"
```

L’installateur fusionne l’index, ne copie pas son `index.idx` par-dessus celui du mod cible et refuse une carte déjà modifiée.

## Validation et limites

Le contrôle vérifie le guide magenta, les cinq recompositions canoniques, les banques `.tile` 8 px, le Ground, l’index et l’installateur. Le résultat PMDO graphique, GPU, déplacement réel, collisions en mouvement et transition vers un donjon ne sont pas testés dans cet environnement.

## Reproduction

Depuis la racine :

```sh
.venv/bin/python source/zones_south_north_magenta_v1/build.py
.venv/bin/python source/zones_south_north_magenta_v1/verify.py
.venv/bin/python source/zones_south_north_magenta_v1/package.py
```
