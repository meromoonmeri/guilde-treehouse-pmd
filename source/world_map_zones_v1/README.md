# Grande carte du monde — zones débloquées

Cette version reprend la carte fournie dans le dernier commit, et non une nouvelle géométrie inventée.

## Sources canoniques utilisées

- `Explorers_of_Sky_-_World_Map.png` : fond natif 504×336, conservé à 1× dans `layers/00_fond_canonique_1x.png`.
- `MapAssetsPMD2.webp` : atlas d'emblèmes/repères. Les repères sont prélevés par boîtes documentées dans `assetsprite/WorldMap_Lieux_AssetSprite.json`.
- `animationmapdiscover.png` : planche de découverte 2×6. Les 12 images sont découpées en frames PNG 504×336, puis regroupées en WebP.

Aucun fond canonique n'est recoloré, redimensionné ou repeint. Les routes, marqueurs d'état et surlignages sont des calques UI séparés qui peuvent être remplacés par l'état réel du jeu.

## Sorties

- `renders/world_map_zones_v1/WorldMap_Zones.png` : composition avec repères et routes.
- `layers/00_fond_canonique_1x.png` : fond exact.
- `layers/01_routes_zones.png` : tracé de progression indépendant.
- `layers/02_emblemes_canoniques.png` : repères issus de l'atlas fourni.
- `layers/03_etat_deblocage.png` : état ouvert/verrouillé indépendant.
- `layers/04_surlignage_debloque.png` : halo des zones ouvertes indépendant.
- `animations/WorldMap_discover_00.png` à `11.png` : frames directes extraites de la planche fournie.
- `animations/WorldMap_discover.webp` : boucle WebP directe.
- `assetsprite/WorldMap_Lieux_AssetSprite.png` et `.json` : spritesheet et rectangles d'intégration.
- `manifest.json` : dimensions, SHA et provenance.

État de démonstration : Volcan, Forêt et Plage ouverts ; Désert, Glace, Ruines et Tour verrouillés. Les coordonnées sont natives 504×336.

## Vérification

```bash
.venv/bin/python source/world_map_zones_v1/build.py
.venv/bin/python source/world_map_zones_v1/verify.py
```
