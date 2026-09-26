# EDP1 — Entrée Dark Crater, fosse de lave sud → nord (4:3)

Demande : « passe à la suite stp » (après EFF2). Biome **choisi par l'agent** : Dark Crater Pit. La capture `Dark_Crater_Pit_TDS.png` n'avait jamais servi de référence principale.

- Aperçu : `apercu_entree_dark_crater_pit_sud_nord_v1.html` (racine).
- Pack PMDO 0.8.12 : `EDP1_projet_pmdo_0812.zip`. Calques PNG 8 px : `EDP1_calques_png_8px.zip`, ORA, `review/EDP1_scene_animee.webp`.
- Source : `source/entree_dark_crater_pit_sud_nord_v1/`, 11 tests.

## Méthode : rendu généré référencé

1. `bruts/decor_magenta.png` : décor 4:3 nouveau, généré avec la capture en référence. L'arrivée est au sud, par un chemin de pierre entre des rebords en pointes. Il mène à un grand plateau, puis un pont de pierre monte jusqu'à la grotte percée dans un grand mur noir. Toute la lave est en magenta.
2. `bruts/lave_complete.png` : le décor édité par le générateur, avec le décor et la capture en références. Le magenta y est remplacé par de la lave.
3. `bruts/sol_complet.png` : pierre grise complète, obtenue au 2e essai (le 1er a rendu une réponse sans image).
4. `bruts/bulles_poses.png` : planche de bulles. Les 6 premières poses ont un fond de lave rectangulaire et les 2 dernières sont tramées : seules 5 poses servent (3 gerbes, 2 anneaux).

La segmentation se fait en pleine résolution, puis chaque matière est réduite séparément. La même partition est appliquée au brut de lave.

## Animations

| Calque | Cadence | Origine |
|---|---|---|
| Lave | 12 × 8 ticks | motif généré, ramené aux **11 couleurs exactes du rip** ; cycle de palette : indice de rampe ± 1 selon une onde oblique (créé par nous) |
| Bulles | 24 × 4 ticks | 5 poses générées réduites ×1/10 ; 12 points, chronologie éclatement → anneau → repos |

La scène boucle en 96 ticks (1,6 s). Toutes les boucles sont fermées (testé).

## Fidélité au rip

| Matière | Brut | Calque final |
|---|---|---|
| Pierre | 5,1 | 7,3 |
| Roche sombre | 16,0 | 19,6 |
| Lave | 10,0 | couleurs exactes |

## Accès

- `entrance` en (384, 560), `donjon_seuil` en (376, 96). Chemin libre de 16 × 16 px vérifié ; 1471 cases praticables. Aucun warp.

## Limites

- Le calque de lave pèse lourd : 12 phases sur une grande surface, soit la majorité des 51 468 tuiles.
- Pas de test PMDO en jeu. L'art n'est pas validé.
