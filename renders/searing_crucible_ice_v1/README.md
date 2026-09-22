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

## Sprites (ajout `pack_sprites.py`)
- `pmdo_object_dir/Ice_Peak_*.dir` — 4 objets PMDO prêts à déposer dans `Content/Object/` : même conteneur que les `.dir` natifs de lave (feuille PNG de même taille et même grille de colonnes, en-tête int32 `tileW,tileH,dirs,frames` identique octet pour octet, RGBA prémultiplié). Aller-retour décodé = bandes 63 images à l'identique.
- `rsmap_decorations_glace.json` — les 8 décorations du rsmap avec `AnimIndex` renommé (MapLoc, FrameTime, miroirs inchangés), à recoller dans une copie de `searing_crucible.rsmap`.
- `spritecollab/Ice_Peak_*.zip` (+ dossiers dépliés) — format SpriteCollab / PMDOWiki « PMD Sprite Format » : `AnimData.xml` + `Idle-Anim.png` / `Idle-Offsets.png` / `Idle-Shadow.png`, images de même taille, dimensions de frame paires (48×48 ou 48×24), 63 frames de gauche à droite sur une seule direction, `<Duration>4</Duration>` (1/60 s) par frame, pixel vert = centre du corps, pixel blanc = centre de l'ombre, `ShadowSize` 0.
  Ce format est celui des Pokémon : pour des objets de décor, le moteur PMDO utilise les `.dir` ci-dessus ; les zips sont fournis pour la compatibilité outillage (Sprite Tool / SkyTemple), pas pour une soumission au dépôt SpriteCollab (réservé aux Pokémon).
- `sprites_manifest.json` — en-têtes, tailles, SHA256. `verify.py` : 15/15 + 12/12 PASS. Aucune validation moteur.

## Carte complète (ajout `build_rsmap.py`)
- `Data/Map/frozen_crucible.rsmap` — copie du rsmap de référence où seuls changent : TileTex de chaque cellule (feuille `VastIceMountainPeak`, TexLoc issus de l'autotile canonique DumpAsset `vast_ice_mountain_peak_{wall,floor}.json`), `AnimIndex` des 8 décorations → `Ice_Peak_*`, couleur de la brume, nom. Rendu depuis le `VastIceMountainPeak.tile` de DumpAsset = calque 01 **pixel-identique** (`calques/01b_sol_rendu_depuis_rsmap.png`).
- `Content/Object/` + `frozen_crucible_mod.zip` + `INSTALL.md` — paquet prêt à déposer dans un mod PMDO. Non testé en moteur.
