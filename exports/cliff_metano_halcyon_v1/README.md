# Cliff Métano / Halcyon — méthode validée (tuiles canoniques 8 px)

Une nouvelle composition de falaise Métano construite **exclusivement** avec des tuiles
natives de `Metano_Town_Base`, `Metano_Town_Cliffs` et `Metano_Town_Animation_Tileset`
(Palikadude/Halcyon, commit `da6c2130`). Aucun pixel généré, recoloré, retourné ou
rééchantillonné : les faces hautes répètent des rangées natives entières et la chute est
en 4 frames natives, comme dans la méthode validée de `build_metano_pixel_perfect.py`.

- `herbe.png` : plateau d'herbe canonique.
- `falaises.png` : rempart traversant avec retour à gauche (calque séparé).
- `cliff_sec.png` : herbe + falaises.
- `eau_frame_1..4.png` + `cliff_eau_frame_1..4.png` : chute animée (4 frames natives).
- `manifest.json` / `provenance.json` : sources, sha256, entrées d'atlas.

## Reconstruction et tests

```sh
python source/cliff_metano_halcyon_v1/build.py
python source/cliff_metano_halcyon_v1/test_cliff.py
```

`test_cliff.py` vérifie que chaque bloc 8×8 non vide des calques herbe / falaises / eau
est identique à au moins une tuile native des feuilles source (0 bloc non canonique).

## Limites

Nouvelle géométrie, pas une carte officielle Métano ; collisions / transitions non
fournies ; pas d'import PMDO réel. Ressources © Palika / contributeurs Halcyon.
