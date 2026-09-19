# Plage « Beach Cave », grande — lot `plage_beach_cave_v1`

Nouveau layout de plage, **45 × 20 cellules de 24 px (1080 × 480 px)**,
ré-assemblé cellule par cellule à partir de la plage canonique de PMD
Explorers of Sky (fond `D01P11A`) telle que livrée par Explorers of Sky Origins
(EoSO), avec **l'animation canonique de la mer (17 frames par cellule)** et
**l'entrée de Beach Cave** à gauche. Carte d'origine : 33 × 16.

- Composition : `SPEC.md` (fonction, profondeur, bords, arrivée, seuil, sortie).
- Mesures de raccord et choix des blocs : `ANALYSE.md` / `analyse.json`.
- Plan de cellules : `layout.py` ; correspondances cellule → source : `cell_mapping.json`.
- Provenance (dépôt, commit, SHA-256, blobs Git) : `provenance.json`.
- Vérification : `verify.py` → `verification.json` ; chargement natif : `runtime_test.py` → `runtime_verification.json`.

## Livrables (racine du dépôt)

| Fichier | Contenu |
|---|---|
| `plage_beach_cave_v1_pmdo_0812.zip` | projet PMDO 0.8.12 autonome : `Data/Ground/plage_bc1_grande_jour.rsground`, 3 feuilles `.tile` (copies octet pour octet des feuilles EoSO, renommées `PLAGE_BC1_*`), `Content/Tile/index.idx`, `Mod.xml` (namespace `plage_beach_cave_v1`), squelette Lua, `INSTALLER.py`, `OUVRIR_EDITEUR.bat/.sh`, aperçu, provenance |
| `apercu_plage_beach_cave_v1.html` | aperçu animé recomposé par calque, comparaison avec l'original |
| `exports/plage_beach_cave_v1/calques/` | PNG par calque : `PLAGE_BC1_back_*.png`, `PLAGE_BC1_front_*.png`, `PLAGE_BC1_mer_frame00..16.png` (alpha droit) |
| `exports/plage_beach_cave_v1/plage_bc1_grande_x2.gif`, `…_anim.webp` | animation composite (17 frames, 267 ms) |
| `exports/plage_beach_cave_v1/comparaison_avant_apres_x2.png`, `phases_mer.png` | planches |
| `exports/plage_beach_cave_v1/tiled/` | `plage_bc1_grande.tmj` + 3 TSX (24 px ; tuiles de mer animées) |

## Installation PMDO

1. Extraire le ZIP dans `PMDO/MODS/` (dossier `plage_beach_cave_v1/`), ou lancer
   `python INSTALLER.py <PMDO>/MODS/<mon_mod>` pour fusionner dans un mod
   existant (jamais d'écrasement, index sauvegardé).
2. `OUVRIR_EDITEUR.bat` / `.sh` lance PMDO en mode développeur sur ce projet.
3. Ground : **Plage — Beach Cave (grande)** (`plage_bc1_grande_jour`).
4. Raccorder les deux déclencheurs dans `Data/Script/plage_beach_cave_v1/ground/plage_bc1_grande_jour/init.lua`
   (`Exit_Touch`, `Beach_Cave_Entrance_Touch`).

## Ce qui est garanti / ce qui ne l'est pas

- Chaque cellule (1 frame ou 17 frames) est la séquence exacte d'une cellule
  de la carte EoSO ; les feuilles livrées sont identiques octet pour octet aux
  feuilles sources ; aucune image générée, recolorée, tournée ou redimensionnée.
- La mer n'est jamais figée : 315 cellules animées × 17 frames, `FrameLength` 16.
- **Chargé par le vrai PMDO 0.8.12, sans affichage** (`runtime_test.py` →
  `runtime_verification.json` : `DataManager.GetGround` dans un hook Lua du
  binaire officiel, 45 × 20, TexSize 3, 3 calques, cellule de mer à 17 frames).
  Rendu GPU, éditeur, collisions en jeu et déclencheurs **non testés** ; un
  aperçu HTML ne les valide pas non plus.
- La variante crépuscule EoSO (`dusk_beach`) n'est pas produite (flipbook de
  toute la carte avec bulles cuites : non ré-assemblable sans doublons).
