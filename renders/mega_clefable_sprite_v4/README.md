# Méga-Mélodelfe V4 — design strict (références utilisateur), toutes les animations donjon (lot `mega_clefable_sprite_v4`)

V1–V3 conservés. Demande : garder le design strict des références fournies (sheet 64 px 4 directions + GIF), **Méga-Mélodelfe vole** (Idle/Walk gardés de V3 à la demande), refaire toutes les autres feuilles d'après les exemples SpriteCollab du Mélodelfe.

## Verrou de design
`source/mega_clefable_sprite_v4/gen/design_lock_strict.png` (tes deux références) → `raw_turnaround.png` (8 directions, généré, validé) + `raw_extra_poses.png` (blessé, sommeil, attaque, charge) → `design_lock_final.png` fourni au générateur avec la feuille CHUNSOFT de chaque animation.

## Feuilles générées frame par frame (`gen/raw_<Anim>.png`)
Attack (issu de la feuille Double stricte : la feuille Attack générée est ressortie en turnaround), Hurt, Sleep, Charge, Swing, Double, Withdraw, Dance, Hop, Rotate. Idle et Walk = V3.
Re-grillage identique à V3 : segmentation, affectation aux cases canoniques (toutes les cases dessinées, aucun repli), palette fixe 16 couleurs, contour 1 px, alpha binaire, ombres portées du générateur supprimées, `AnimData.xml` / `Offsets` / `Shadow` **identiques à la base CHUNSOFT** (13 animations, Strike = CopyOf Attack). `verify.py` 52/52 PASS.

## Qualité par animation (relecture visuelle honnête)
| Anim | Cohérence du design entre cases | Remarque |
|---|---|---|
| Hurt, Sleep, Withdraw, Hop, Swing | bonne | ailes, calotte, menottes stables |
| Dance, Idle, Walk | correcte | Idle/Walk = V3 |
| Charge, Rotate | moyenne | dérive de pose/ailes en fin de ligne |
| Attack, Double | faible | personnages dessinés trop petits par le générateur → détails perdus à 56–72 px ; à regénérer |

## Fichiers
`sprite/0036/0001/` (AnimData.xml, 36 PNG, credits.txt), `0036_0001_mega_clefable_v4_spritecollab.zip`, `planche_<Anim>_x2|x3.png`, `apercu_walk_8_directions.webp`, `manifest.json` (SHA256 des dessins bruts, source de chaque feuille).
Art IA déclaré ; relecture humaine nécessaire ; non testé en moteur.
