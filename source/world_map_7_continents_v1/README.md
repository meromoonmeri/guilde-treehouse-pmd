# Grande carte à 7 continents

Nouvelle composition séparée de l'ancienne carte de progression. Le fond de référence reste `Explorers_of_Sky_-_World_Map.png` à 504×336 ; la livraison de preview est en 2× nearest-neighbor, 1008×672.

## Calques

1. fond canonique 2× ;
2. silhouettes des 7 continents ;
3. côtes et reliefs ;
4. repères de continents ;
5. routes ;
6. état débloqué/verrouillé ;
7. labels.

Les textures des continents sont prélevées dans `MapAssetsPMD2.webp` et documentées comme matériaux atlas normalisés, pas comme pixels natifs de la carte. Le fond canonique original reste intact.

## Continents

Cendre, Sylve, Aurore, Dunes, Archipel, Marais et Cime. Cendre, Sylve, Aurore et Archipel sont ouverts dans l'état de démonstration ; les autres sont verrouillés.

## Animations et AssetSprite

- `animations/WorldMap_7continents_discover_00.png` à `07.png` : révélation progressive, frames indépendantes ;
- `animations/WorldMap_7continents_discover.webp` : boucle directe ;
- `assetsprite/WorldMap_7Continents_AssetSprite.png/.json` : marqueurs numérotés ;
- `world_map_7_continents_state.json` : positions, états et contrat d'intégration.

## Vérification

```bash
.venv/bin/python source/world_map_7_continents_v1/build.py
.venv/bin/python source/world_map_7_continents_v1/verify.py
```
