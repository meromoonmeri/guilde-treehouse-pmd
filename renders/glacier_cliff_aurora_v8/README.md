# Glacier Cliff Aurora v8 — construction par étapes

Cette version suit l'ordre demandé et repart de zéro avec le générateur d'image :

1. `layers/01_arena_cliff_base_magenta.png` — socle de l'arène et falaise ;
2. `layers/02_snow_forest_border_magenta.png` — forêt enneigée qui borde la falaise ;
3. `layers/03_distant_mountains_magenta.png` — chaîne lointaine ;
4. `layers/04_near_snow_crags_magenta.png` — crêtes de neige plus proches ;
5. `layers/05_night_sky_canonical_magenta.png` — ciel canonique indépendant ;
6. `layers/06_aurora_palette_cycle_source_magenta.png` — source de l'aurore,
   générée en dernier.

Le magenta `#ff00ff` est le fond de masque hors couche. Les six fichiers
`layers/aurora_palette_cycle/frame_00.png` à `frame_05.png` gardent exactement
la silhouette de l'aurore et changent uniquement leur famille de couleurs :
ils forment le cycle de palette indépendant du ciel. La prévisualisation
animée est `aurora_palette_cycle.gif`.

`composition/07_map_pre_aurora.png` est la composition générée avant l'ajout
de l'aurore. Les previews `composition/frames/` montrent l'ajout de chaque
frame au-dessus de cette composition.

Références utilisées : `VastIceMountain.tile`, `pmdskyicearena.png`,
`iceroadpmdsky.png`, `path.png`, `snow.png`,
`bgnightbackgroundpmdskyda.png` et `aurorepmdsky.png`. Les PNG de ce dossier
sont des guides visuels générés et masquables ; les ressources PMDO natives et
la carte jouable restent dans le package PMDO.
