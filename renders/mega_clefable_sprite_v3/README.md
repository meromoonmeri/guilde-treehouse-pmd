# Méga-Mélodelfe V3 — toutes les animations **dessinées par le générateur, frame par frame** (lot `mega_clefable_sprite_v3`)

V1 (dérivé) et V2 (5 poses) sont conservés. Cette V3 répond à la demande : chaque feuille d'animation est un dessin du générateur, frame par frame, dans la conception et la configuration des sprites SpriteCollab.

## Méthode
- **Guides** : pour chaque animation, la feuille CHUNSOFT du Mélodelfe (`source/mega_clefable_sprite_v3/gen/guide_<Anim>.png`, grille 8 directions × N frames, fond magenta) est donnée au générateur avec un **verrou de design** (`gen/design_lock.png` : art officiel LPZA fourni par l'utilisateur + version 8 directions cohérente) ; consigne : même grille, mêmes poses, design strictement identique dans chaque case, deux ailes toujours visibles, calotte blanche + boucle, visage de la référence, menottes, **au sol, ne vole pas**.
- **Dessins bruts** : `gen/raw_<Anim>.png` pour Idle, Walk, Attack, Hurt, Sleep, Charge, Dance, Hop, Rotate, Swing (SHA256 dans `manifest.json`).
- **Re-grillage** : segmentation des personnages, affectation aux cases canoniques (toutes les cases dessinées sauf 6 cases de Dance retombées sur la frame voisine), mise à l'échelle sur la hauteur du personnage CHUNSOFT de la frame, **palette fixe 16 couleurs** (pêche ×3, rose ×3, jaune ×2, blanc ×2, menottes ×2, joues, bouche, oreille, contour), contour noir 1 px, alpha binaire, placement sur le centre du corps canonique avec 1 px de marge.
- **Configuration** : `AnimData.xml` = fichier CHUNSOFT (mêmes tailles de frame, durées, Rush/Hit/Return, Strike = CopyOf Attack), `*-Offsets.png` et `*-Shadow.png` **identiques octet pour octet** à la base.

## Vérification — `verify.py` 44/44 PASS
noms/index uniques, CopyOf sans chaînage, 3 PNG de même taille, frames paires, colonnes = durées, aucun frame vide ni coupé par le bord, centre vert / ombre blanche uniques, alpha binaire, ≤ 16 couleurs, Offsets/Shadow identiques au canon.

## Fichiers
`sprite/0036/0001/` (AnimData.xml, 30 PNG, credits.txt), `0036_0001_mega_clefable_v3_spritecollab.zip`, `planche_<Anim>_x2|x3.png`, `apercu_walk_8_directions.webp`, `manifest.json`.

## Limites
- **Withdraw et Double manquent** (limite de 10 générations d'images par tour) : retirées de l'AnimData.xml, à générer au tour suivant.
- Art IA déclaré dans `credits.txt` ; la cohérence du design entre frames est bonne mais pas parfaite (petites variations d'ailes/boucle selon les cases) — relecture humaine nécessaire avant soumission au Discord SpriteCollab. Non testé en moteur.
