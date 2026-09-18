# Glacier Cliff Aurora v3 — composition finale de référence

Cette image a été générée avec le générateur d’image en fournissant **à la
fois** les références canoniques et des rendus raster issus du vrai tileset
PMDO `VastIceMountain.tile`.

## Rendus de tileset fournis au générateur

- `preview/native_floor_layer.png` : sol natif de l’arène ;
- `preview/native_wall_layer.png` : falaises et parois natives ;
- `preview/native_foreground_layer.png` : rebord de glace avant ;
- `preview/native_access_path_layer.png` : accès sud natif.

Ces images sont des aperçus exacts du tileset byte-identique, pas de nouvelles
textures moteur.

## Références canoniques fournies

- ciel nocturne ;
- aurore boréale ;
- montagnes distantes ;
- arbres et forêt enneigée ;
- matériau d’arène ;
- chemin canonique.

Le résultat `raw/native_tileset_reference_composition_magenta.png` est un
guide de composition harmonisé : ciel/aurore à l’arrière, montagnes au loin,
forêt en contrebas, falaises d’arène séparées visuellement, arène praticable
et chemin sud. Le magenta sert uniquement à identifier les zones hors couche.

Ce PNG généré n’est pas importé dans PMDO. La carte jouable reste construite
par `source/glacier_cliff_aurora_pmdo_v1/build.py` avec les `.dir`,
`VastIceMountain.tile`, le Ground sérialisé et les collisions séparées.
L’aurore animée du livrable est produite séparément depuis sa frame canonique
par un cycle de palette indépendant du ciel.
