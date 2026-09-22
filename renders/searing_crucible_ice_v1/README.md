# Creuset de glace — ré-adaptation glaciaire de la zone « Searing Crucible » (lot `searing_crucible_ice_v1`)

Nouveau lot, aucune livraison antérieure n'est modifiée.

## Référence identifiée
« Searing Crucible » = salle de boss (chapitre 5, dérivée d'Halcyon) du dépôt **meromoonmeri/New-Era-Abyss-to-Ascension-V5 @ cb6e902f** :
`Data/Map/searing_crucible.rsmap` (21×21 tuiles, 72 sol / 369 mur, entrée (11,10), statut `steam` + `mysterious_force`),
tileset `Content/Tile/Spring_Cave_Pit.tile`, 4 objets animés `Content/Object/Spring_Cave_Pit_{Big_Lava_Stream,Small_Lava_Stream,Lava_Pool_Connected,Lava_Pool_Disconnected}.dir`
(63 images, FrameTime 4, placés en 4 paires miroir), fond `Content/BG/Steam.dir`. Bruts + SHA256 dans `source/searing_crucible_ice_v1/references/`.
Décodage de la référence (rendu statique + WebP animé) : `reference/`.

## Ce qui est canonique / ce qui est dérivé
| Élément | Statut |
|---|---|
| Géométrie 21×21 (sol/mur, positions des 8 animations, FrameTime, miroirs) | identique à la référence |
| Sol et murs | **natif** : autotile PMD « Vast Ice Mountain Peak » (PMDCollab/RawAsset @03c80dad), résolution 47 cas AutoTileAdjacent, 441 cellules pixel-identiques aux feuilles (vérifié) — sans recoloration, rotation ni agrandissement |
| Les 4 animations « flux / mares de glace » | **dérivées** : transfert de palette des 63 images natives de lave (table explicite dans `manifest.json` : lave → rampe glace lumineuse, croûte → bleus des murs Vast Ice Mountain Peak, fond de sol rouge → transparent). Silhouettes et timings natifs conservés ; les pixels ne sont pas certifiés canoniques |
| Brume froide | BG natif `Steam` teinté façon moteur (170,200,230,90), défilement y −20 comme l'émetteur `steam` de la référence |

## Fichiers
- `creuset_glace_anime.webp` — composition animée (63 images, boucle 252 frames jeu ≈ 4,2 s) ; `creuset_glace_anime_sans_brume.webp` sans l'overlay.
- `calques/01_sol_vast_ice_mountain_peak_natif.png`, `02_flux_glace_frame0.png`, `03_brume_froide_frame0.png` — calques séparés.
- `objets_animes/Ice_Peak_*_63f.png` — bandes 63 images prêtes à ré-empaqueter en `.dir` ; `comparatif_*` lave vs glace.
- `planche_reference_vs_glace.png`, `creuset_glace_frame0.png`, `manifest.json` (provenance, palette, cellules).

Reproduction : `.venv/bin/python source/searing_crucible_ice_v1/decode.py && build.py && verify.py` (15/15 PASS). Aucune validation moteur/collision.
