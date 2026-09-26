# ECF1 — Entrée de la fosse du Dark Crater, sud → nord, 4:3

Demande : « passe à la suite stp ». Le biome a été choisi par l'agent : la fosse du Dark Crater. Sa capture `Dark_Crater_Pit_TDS.png` n'avait jamais servi de référence principale.

- Aperçu : `apercu_entree_cratere_fosse_sud_nord_v1.html` (racine).
- Pack PMDO 0.8.12 : `ECF1_projet_pmdo_0812.zip`.
- Calques : `ECF1_calques_png_8px.zip`, ORA, `review/ECF1_scene_animee.webp`.
- Source : `source/entree_cratere_fosse_sud_nord_v1/`, 11 tests.

## Méthode : rendu généré référencé

La capture est passée au générateur comme image de référence. Les prompts sont dans `manifest.json`.

1. `decor_magenta.png` : décor complet en 4:3.
   - L'arrivée est au sud, sur un chemin de roche bordé d'arêtes.
   - Le chemin mène à un grand plateau, puis un pont de roche sinueux monte jusqu'à une grotte dans la paroi noire, au nord.
   - Il y a deux îlots et huit pics noirs. **Toute la lave est en magenta.**
2. `sol_complet.png` : roche complète, obtenue au 2ᵉ essai (le premier a rendu une réponse vide). La paroi nord est conservée ; elle reste sous son calque.
3. `bulles_lave_poses.png` : planche sur magenta. La rangée 1, une bulle qui gonfle puis éclate, donne 6 poses réduites ×1/8. La rangée 2 (flammèches) n'est pas utilisée.

Le décor est découpé en pleine résolution, puis chaque matière est réduite séparément. Calques : sol, bordures, pics, paroi, bouche, plus la lave et les bulles.

## Animations

- **Lave** (12 × 8 ticks) : des cellules (Voronoï) sont colorées avec les **11 couleurs exactes** de la rampe de la capture, du rouge au jaune. Chaque cellule respire, avec une bande rouge contre la roche.
  - Un test vérifie que toutes les couleurs appartiennent à la capture.
  - Le motif et le mouvement sont créés par nous.
- **Bulles** (24 × 4 ticks) : 14 points sur la lave, à plus de 22 px de la roche. Chronologie : gonfle, éclate, repos.

Les boucles sont fermées (testé).

## Fidélité au rip

| Matière | Brut | Calque final |
|---|---|---|
| Sol | 12,7 | 11,0 |
| Bordures | 15,9 | 32,5 |
| Roche noire (paroi) | 28,8 | 32,9 |

Le brut rend la paroi plus noire que la capture. Les bordures perdent à la réduction leurs liserés clairs, qui partent au sol ou à la lave.

## Accès

- Pour que le pont de roche fasse 2 cases de large, les rebords à plus de 3 px de la lave sont praticables.
- `entrance` est en (384, 560), `donjon_seuil` en (368, 80), devant la bouche. Un chemin libre de 16 × 16 px a été vérifié.
- Bilan : 1016 cases praticables. Il n'y a aucun warp.

11 tests PASS. **Pas de test PMDO en jeu. L'art n'est pas validé.**
