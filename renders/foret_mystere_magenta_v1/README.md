# Forêt Mystère — entrée de donjon sud → nord (calques générés sur magenta)

**[Aperçu avec calques activables](apercu_calques.html)** · [composite 440×592](composite.png) · [manifeste](manifest.json) · [contrôle gate](gate.json)

| Ordre | Fichier | Rôle |
|---|---|---|
| 1 | `ForetMystereMagentaV1_01_sol.png` | sol plein : sous-bois, prairie, chemin, trouée d'entrée au nord |
| 2 | `ForetMystereMagentaV1_02_herbes_hautes.png` | touffes d'herbe haute |
| 3 | `ForetMystereMagentaV1_03_rochers.png` | rochers et cailloux |
| 4 | `ForetMystereMagentaV1_04_troncs_racines.png` | troncs et racines (derrière le joueur) |
| 5 | `ForetMystereMagentaV1_05_canopees_devant_joueur.png` | couronnes de feuillage (devant le joueur) |

Tous les calques font 440×592 (55×74 cases de 8 px), alignés en (0,0), alpha binaire. Import : **PNG to Tileset, tuiles 8 px**. `apercu_x2_NE_PAS_IMPORTER.png` sert uniquement à la revue.

## Provenance (honnête)

- **Pixels générés** : quatre générations indépendantes à partir de `Mystifying_Forest_entrance_TDS.png` (référence seule), soit le sol en plein cadre, puis arbres, rochers et herbes hautes sur fond magenta. Aucun morceau de carte existante n'est greffé et **ce ne sont pas des tuiles natives**.
- Détourage magenta explicite. Faux pixels de 2 px du générateur ramenés en 1:1 par vote majoritaire, sans LANCZOS ni NEAREST.
- **Palette** : toutes les couleurs sont des couleurs exactes de la référence (118 couleurs). Pour le sol, les arbres et les rochers, c'est le plus proche voisin Lab. Pour les herbes hautes, générées en sarcelle, une rampe de luminance sur 6 verts de la référence conserve le modelé.
- **Composition par l'agent** : les sprites sont placés à la main (positions dans `manifest.json`). Les arbres sont séparés automatiquement par couleur en canopée et bois.
- Scripts : `source/foret_mystere_magenta_v1/process.py`, `compose.py`, tests `test_compose.py`.

## Limites

Collisions, warps et zones d'occlusion restent à définir dans PMDO. Rien n'y a été testé. Validation artistique en attente.
