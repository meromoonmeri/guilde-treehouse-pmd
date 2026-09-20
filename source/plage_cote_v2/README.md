# Plage « côte, mer en bas » — lot `plage_cote_v2`

Deux nouveaux layouts de la crique de Beach Cave, **plus grands que la
source**, **grotte à gauche** (comme le lot livré `plage_beach_cave_v1`) et
**la mer de l'autre côté : en bas**, avec **l'animation canonique de l'eau**
(15 frames par cellule, `FrameLength` 8 ≈ 133 ms). Ré-assemblage cellule par
cellule depuis la carte canonique PMD Sky `Brine_Cave_Entrance` (Explorers of
Sky Origins, commit épinglé `bed94499`) — seule source dont la mer est en bas
de carte ; la mer de la plage D01P11A n'existe qu'en haut (la mettre en bas
exigerait une rotation, interdite).

| Layout | Cellules (24 px) | Pixels | Source |
|---|---|---|---|
| **Crique** (`plage_cv2_crique`) | 35 × 21 | 840 × 504 | source 27 × 21 + module [19..27) ×2 (extension horizontale) |
| **Grande anse** (`plage_cv2_anse`) | 43 × 21 | 1032 × 504 | module [19..27) ×3 |

Extension en **largeur uniquement** : toutes les adjacences verticales sont
exactement celles de la source. Boucle du module mur pixel-parfaite (période
4) et sol quasi parfait ; la mer (période 3, incompatible avec 4) prend un
saut de phase borné et documenté sur la couronne d'écume à chaque jonction
intérieure (ANALYSE §4-§5).

- Composition : `SPEC.md` (fonction, bords, arrivée, seuil, sortie) ; mesures
  et justifications des recollements : `ANALYSE.md` / `analyse.json` / `analyse2.json`.
- Plan de cellules : `layout.py` ; correspondances : `cell_mapping.json`.
- Provenance (dépôt, commit, SHA-256, blobs Git) : `provenance.json`.
- Vérification : `verify.py` → `verification.json` ; chargement natif :
  `runtime_test.py` → `runtime_verification.json`.
- Guides de composition **générés** (aucune tuile n'en provient) :
  `references/guide_composition_L1.png`, `references/guide_composition_L2.png`.

## Livrables (racine du dépôt)

| Fichier | Contenu |
|---|---|
| `plage_cote_v2_pmdo_0812.zip` | projet PMDO 0.8.12 autonome : **2 Grounds** (`plage_cv2_crique`, `plage_cv2_anse`), feuille `PLAGE_CV2_BRINE.tile` (copie octet pour octet de `Brine Cave Entrance.tile`), `Content/Tile/index.idx`, `Mod.xml` (namespace `plage_cote_v2`), squelettes Lua, `INSTALLER.py`, `OUVRIR_EDITEUR.bat/.sh`, aperçu, provenance |
| `apercu_plage_cote_v2.html` | aperçu animé des deux layouts (15 frames, recomposés depuis le projet livré) |
| `exports/plage_cote_v2/crique/`, `…/anse/` | calque PNG, `frame00.png`, GIF ×2 et WebP animés (15 frames) |
| `exports/plage_cote_v2/tiled/` | `plage_cv2_crique.tmj`, `plage_cv2_anse.tmj` + TSX/PNG (24 px, tuiles de mer animées 15 frames) |
| `exports/plage_cote_v2/comparaison_avant_apres.png` | planche source + deux layouts |

## Installation PMDO

1. Extraire le ZIP dans `PMDO/MODS/` (dossier `plage_cote_v2/`), ou lancer
   `python INSTALLER.py <PMDO>/MODS/<mon_mod>` pour fusionner dans un mod
   existant (jamais d'écrasement, index sauvegardé).
2. `OUVRIR_EDITEUR.bat` / `.sh` lance PMDO en mode développeur sur ce projet.
3. Grounds : **Plage — Crique de Beach Cave (mer en bas)** et
   **Plage — Grande anse de Beach Cave (mer en bas)**.
4. Raccorder les deux déclencheurs dans
   `Data/Script/plage_cote_v2/ground/plage_cv2_<layout>/init.lua`
   (`Exit_Touch`, `Beach_Cave_Entrance_Touch`).

## Ce qui est garanti / ce qui ne l'est pas

- Chaque cellule copie la **séquence complète des 15 frames** d'une cellule de
  la carte EoSO ; la feuille livrée est identique octet pour octet à la
  feuille source ; aucune image générée, recolorée, tournée ou redimensionnée.
- La mer n'est jamais figée par un remplissage statique : toutes les cellules
  de mer profonde sont animées (15 phases) ; la rive d'écume statique est
  l'état canonique de la source.
- **Chargé par le vrai PMDO 0.8.12, sans affichage** (`runtime_test.py` →
  `runtime_verification.json`) ; rendu GPU, éditeur, collisions en jeu et
  déclencheurs **non testés** ; un aperçu HTML ne les valide pas non plus.
- La rive d'écume s'arrête à la colonne 12 de la source (à gauche de
  l'embouchure, c'est la diagonale qui prend le relais) — conforme à la source.
- Aux jonctions de modules, la couronne d'écume change de phase (périodes
  mer/sol incommensurables) : discontinuité documentée dans `ANALYSE.md`,
  pixels intégralement canoniques, visible à l'œil comme une vague différente.
