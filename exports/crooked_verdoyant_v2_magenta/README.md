# Crooked Cavern verdoyante V2 — exports multicalques (comme la guilde)

Dossier `multicalques/` : les 9 calques générés sur fond magenta de `renders/crooked_verdoyant_v2_magenta/`
exportés selon la convention `sprites/zones_guidees/README_multicalques.md` — calques nommés et ordonnés, canevas commun
**512 × 640**, origine (0, 0), PNG RGBA transparents (le sol forme le fond opaque), fichiers **Aseprite** éditables,
grille 8 px, cartes **Tiled** (`.tmj` base64/zlib) avec atlas 8 px dédié, contrôle par recomposition. Jour et nuit.

| Ordre | Calque | PNG jour / nuit |
|---|---|---|
| 1 | Sol : herbe pure | `CrookedMagentaV2_01_sol_herbe[_nuit].png` |
| 2 | Lisière de forêt | `CrookedMagentaV2_02_lisiere_foret[_nuit].png` |
| 3 | Chemin de terre | `CrookedMagentaV2_03_chemin[_nuit].png` |
| 4 | Parois Crooked | `CrookedMagentaV2_04_parois_crooked[_nuit].png` |
| 5 | Entrée (ouverture + sol du débouché) | `CrookedMagentaV2_05_entree_grotte[_nuit].png` |
| 6 | Rochers et cailloux | `CrookedMagentaV2_06_rochers[_nuit].png` |
| 7 | Végétation basse | `CrookedMagentaV2_07_vegetation_basse[_nuit].png` |
| 8 | Troncs + ombres au sol | `CrookedMagentaV2_08_troncs_ombres[_nuit].png` |
| 9 | Canopées (au-dessus du joueur) | `CrookedMagentaV2_09_canopees[_nuit].png` |

- `CrookedMagentaV2_jour.aseprite`, `CrookedMagentaV2_nuit.aseprite` : 9 calques, 1 frame, RGBA, grille 8 px.
- `CrookedMagentaV2_jour.tmj` + `CrookedMagentaV2_jour_8px.{png,tsj}` (idem `_nuit`) : 9 couches de tuiles 64 × 80,
  atlas de 8 559 tuiles 8 px **découpées dans ces calques générés** (ce n'est pas un atlas canonique ; il est dédié à
  cette zone). Les cartes référencent l'atlas par chemin relatif : garder les fichiers ensemble.
- `CrookedMagentaV2_composition_jour.png` / `_nuit.png` : pile complète, identique aux compositions du dossier renders.
- `multicalques.json` (SHA-256), `verification_multicalques.json` : relecture indépendante PNG / Aseprite / Tiled,
  **0 différence de pixel**, `all_pass = true`.

Visualiseur : `apercu_crooked_verdoyant_v2_magenta.html` (cases de visibilité, « Seul », tout afficher, jour/nuit,
zoom ×2, grille 8 px, export PNG des calques visibles, variante objets natifs).

**Provenance** : pixels générés d'après références PMD canoniques (audit `source/crooked_verdoyant_v1/AUDIT.md`), pas des
pixels natifs certifiés ; nuit = filtre Abyss exact. Pas de validation interactive Aseprite/Tiled, pas de test PMDO,
collisions ou warps.

Reconstruction : `.venv/bin/python source/crooked_verdoyant_v2_magenta/multicalques.py` puis `verify_multicalques.py`.
