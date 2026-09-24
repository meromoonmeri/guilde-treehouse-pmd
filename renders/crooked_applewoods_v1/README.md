# Crooked Cavern × Apple Woods — entrée de grotte en forêt (sud → nord)

**[Aperçu avec calques activables](apercu_calques.html)** · [composite 464×432](composite.png) · [manifeste](manifest.json) · [contrôle gate](gate.json)

| Ordre | Fichier | Rôle |
|---|---|---|
| 1 | `CrookedAppleV1_01_sol.png` | herbe Apple Woods, chemin sableux, parvis devant la grotte |
| 2 | `CrookedAppleV1_02_falaise_grotte.png` | falaise en grès Crooked Cavern, mousse et lierre, bouche de la grotte |
| 3 | `CrookedAppleV1_03_vegetation_basse.png` | touffes, fleurs, arbustes |
| 4 | `CrookedAppleV1_04_rochers.png` | amas moussus au pied de la falaise, cailloux |
| 5 | `CrookedAppleV1_05_troncs_racines.png` | troncs et racines (derrière le joueur) |
| 6 | `CrookedAppleV1_06_canopees_devant_joueur.png` | couronnes des pommiers et buissons (devant le joueur) |

Calques de 464×432 (58×54 cases de 8 px), alignés en (0,0), alpha binaire. Import : **PNG to Tileset, tuiles 8 px**. `apercu_x2_NE_PAS_IMPORTER.png` sert seulement à la revue.

## Provenance (honnête)

- **Pixels générés** : 5 générations indépendantes à partir des références `Apple_Woods_entrance_TDS.png` et `Halcyon__crooked_cavern_entrance_composition.png`. On a le sol en plein cadre, puis la falaise, les arbres, les rochers et la végétation sur fond magenta. **Ce ne sont pas des tuiles natives**, et aucun morceau de carte n'est greffé.
- **Grille** : la taille des faux pixels est mesurée par image. Elle vaut 2 pour le sol et les arbres, 3 pour la végétation, 2,867 pour la falaise et 5,733 pour les rochers, ces deux derniers pas étant fractionnaires. Chaque cellule prend sa couleur majoritaire, sans rééchantillonnage flou.
- **Palettes exactes** : Apple Woods (145 couleurs) pour le sol, les arbres et la végétation. Crooked Cavern (453 couleurs) plus les verts d'Apple Woods pour la falaise et les rochers moussus.
- **Composition par l'agent** (positions dans `manifest.json`). Les arbres sont séparés automatiquement : les pommes restent dans la canopée.
- Scripts : `source/crooked_applewoods_v1/convert.py`, `pixels_lib.py`, `compose.py`, tests `test_compose.py`.

## Limites

Collisions (pied de falaise, troncs), warp de la grotte et occlusion restent à définir dans PMDO. Rien n'y a été testé.
