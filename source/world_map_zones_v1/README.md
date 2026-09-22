# Grande World Map — Zones à débloquer

Recomposition large inspirée de la planche fournie : carte du monde sur fond parchemin, plusieurs continents/îles, routes, emblèmes et états de progression séparés.

## Sorties

- `renders/world_map_zones_v1/WorldMap_Zones.png` : composition 2048×1536.
- `layers/` : mer, continents, bordure, routes, emblèmes, état de déblocage et atmosphère.
- `animations/WorldMap_discover_00.png`…`07.png` : vraies images indépendantes.
- `animations/WorldMap_discover.webp` : boucle WebP directe.
- `assetsprite/WorldMap_Lieux_AssetSprite.png` et `.json` : spritesheet et rectangles d'emblèmes.

Forêt, Plage et Volcan sont ouverts par défaut ; Désert, Glace, Tour et Archipel restent verrouillés. Le calque `05_etat_deblocage.png` peut être remplacé par l'état réel du jeu.

## Provenance

Les matériaux de terrain et de mer utilisent les ressources présentes dans le dernier commit :

- `sprites/zones_guidees/01_cirque/canonique_sec.png` ;
- `sprites/zones_guidees/01_cirque/herbe.png` ;
- `sprites/zones_guidees/01_cirque/eau_1.png`.

Ces textures natives servent de matériaux/tuilage sans modification des fichiers sources. Les continents, routes, marqueurs et fond parchemin sont une composition nouvelle ; ils ne sont pas prétendus comme pixels natifs de la carte World Map jointe.

## Test

```bash
.venv/bin/python source/world_map_zones_v1/build.py
.venv/bin/python source/world_map_zones_v1/verify.py
```
