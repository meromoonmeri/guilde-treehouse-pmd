# Forêt Sinister générée V1 — entrée de forêt en 8 calques + animation

Deux générations au générateur d'images (style PMD, proposition guidée par
`Mystifying_Forest_entrance_TDS.png` + composition du guide forêt V3) :

- `bruts/foret_sinister_complete.png` (848×1264) : scène complète retenue —
  chemin en S du sud vers une grotte sombre au nord, grands arbres à racines,
  rochers, vignettage noir.
- `bruts/foret_sinister_sol.png` (848×1264) : variante sol nu **non recalée**
  (même courbe approximative, bonus seulement, pas utilisée dans les calques).

## Calques (partition exacte du brut, 0 px d'écart)

| Calque | Contenu | px |
|---|---|---:|
| 01_sol | Herbe claire + sol reconstitué sous les éléments (opaque) | 1071872 |
| 02_chemin | Chemin tan, sud → clairière nord | 74185 |
| 03_sous_bois | Masses basses et ombres profondes | 122989 |
| 04_rochers | Rochers isolés (couronne du haut exclue) | 12139 |
| 05_troncs | Troncs et racines (écorce désaturée) | 22662 |
| 06_canpees | Canopées sombres (couche animée) | 473193 |
| 07_profondeur | Grotte sombre + couronne rocheuse | 64368 |
| 08_frange | Vignette noire des bords | 176051 |

`SinisterGenV1_composite.png` = brut exact. Grille 8 px, aucun resampling.

## Animation

Frémissement subtil des canopées, 8 frames × 150 ms (boucle 1,2 s) :
frame0 = brut exact, boucle fermée, seuls les pixels de canopée bougent.
`animation/frame_00..07.png`, `SinisterGenV1_animation.webp` (sans perte),
`SinisterGenV1_animation.gif` (aperçu 256 couleurs).

## Limites annoncées

- Dessin **généré** intégré : PAS des tuiles natives, PAS un démontage de map.
- Sol reconstitué par diffusion depuis l'herbe/chemin de la même image.
- Animation proposée, pas un cycle officiel. Aucun test PMDO/GPU.
- 28 tests PASS (`source/foret_sinister_generee_v1/test_build.py`).
- Galerie : `apercu_foret_sinister_v1.html`. Pack : `renders/foret_sinister_generee_v1_pack.zip`.
