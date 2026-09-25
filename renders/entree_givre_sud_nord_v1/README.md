# EGN1 — Entrée Givre sud → nord, V1

Quatrième map de la série, après les entrées Vapeur, Cratère et Ruine. Biome neige choisi par l'agent (absent de la série) d'après la référence Frosty Forest trouvée en ligne et copiée dans `source/entree_givre_sud_nord_v1/reference/`. Choix à confirmer.

- Aperçu : `apercu_entree_givre_sud_nord_v1.html` (racine) ou `review/EGN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EGN1_projet_pmdo_0812.zip`. Calques PNG 8 px (préfixe unique `EGN1_`) : `EGN1_calques_png_8px.zip`.
- Source : `source/entree_givre_sud_nord_v1/` (`build.py`, `package.py`, 11 tests dans `test_build.py`).

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau glacée | structure de la rivière Métano, palette froide | 4 × 10 ticks |
| 01 | scintillements | pixels Métano recolorés | 4 × 10 ticks |
| 02 | sol complet | neige générée séparément | — |
| 03–04 | neige, sentier | décor généré | — |
| 05 | gué gelé | **dessiné par script** | — |
| 06–10 | glaçons, souche, sapins et congères, falaises de glace, bouche | décor généré | — |
| 11 | flocons | planche générée (6 flocons + 6 boules de neige) | 48 × 5 ticks |

**Flocons** : 40 émetteurs décalés. Chaque flocon tombe de 64 px en 40 phases, en ondulant (sinus de 24 phases) et en tournant (une pose toutes les 2 phases), puis reste posé 2 phases (pose dessinée) et se repose 6 phases. La boucle de 48 phases se ferme exactement (testé).

## Honnêteté et décisions

- **Ruisseau** : le ruisseau généré coupait le sentier. J'ai essayé de faire générer un gué, mais l'édition modifiait tout le ruisseau : je l'ai rejetée. La plaque de glace est donc dessinée par le script.
- **Congères** : le sentier généré est étroit et bordé de congères. Les congères à moins de 6 px du sentier ou du gué sont praticables. C'est une décision de collision qui ne change pas le dessin, **à valider en jeu**.
- **Sapins** : séparés de la neige par la densité de contours (seuil 0,24). Les grosses congères restent dans le calque « sapins_congeres ».
- **Tests** : aucun test PMDO en jeu, art non approuvé.
