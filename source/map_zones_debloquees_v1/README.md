# Map Zones Débloquées — Café

Carte de progression destinée à l'écran de hub en jeu. Elle reprend le langage bois/lumière du dernier commit du café et affiche les zones accessibles sans cuire de personnage ou de Pokémon dans le décor.

## Sorties

- `renders/map_zones_debloquees_v1/MapZones_debloquees.png` : composition complète.
- `layers/` : cinq couches sémantiques alignées :
  - fond du hub et cadre bois ;
  - carte/parchemin ;
  - chemins entre zones ;
  - emblèmes des lieux ;
  - état de déblocage et libellés.
- `animations/MapZones_unlock_00.png` à `07.png` : vraies frames indépendantes de la pulsation des zones déjà débloquées.
- `animations/MapZones_unlock.webp` : boucle WebP directe des mêmes frames.
- `ZoneEmblemes_AssetSprite.png` : spritesheet 6 × 144×144.
- `assetsprite.json` : rectangles et identifiants utilisables par l'UI/AssetSprite.
- `manifest.json` : SHA, dimensions et provenance.

## État de démonstration

Forêt, Plage et Volcan sont débloqués par défaut. Désert, Glace et Tour sont verrouillés. L'état se trouve sur son calque séparé afin que le jeu puisse remplacer ce calque sans repeindre le fond.

Les six emblèmes sont de nouveaux marqueurs de lieu, pas des sprites canoniques de Pokémon. Leurs couleurs et leur bordure sont guidées par les textures du café ; les références canoniques restent intactes.

## Provenance

- Base visuelle générée et calques du dernier commit : `renders/cafe_multietage_v3/calques_alignés/`.
- Références de tileset canoniques conservées : `Guild_Second_Floor_Floor.tile`, `Guild_Second_Floor_Walls.tile`, `Guild_Second_Floor_Objects.tile` et `guild_second_floor_reference.png`.
- Le `.tile` natif n'est pas repeint, agrandi ou modifié. Les fichiers de la map sont une composition UI séparée, documentée comme telle.

## Vérification

```bash
.venv/bin/python source/map_zones_debloquees_v1/build.py
.venv/bin/python source/map_zones_debloquees_v1/verify.py
```
