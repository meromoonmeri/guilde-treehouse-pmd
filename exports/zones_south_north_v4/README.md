# Sud → nord V4 — entrée aride + couloir violet

Deux nouvelles entrées du programme des 23 références, en **textures canoniques**
(pixels natifs des références PMD Sky, translation seule), livrées en **PNG
multicalques jour/nuit** (import « PNG to Tileset ») **et** en **paquet natif**
`.rsground` + `.tile` PMDO 0.8.12.

- **Aride** `arid_dungeon_entrance`, 408×560 : couronne nord 408×208 translatée
  (paroi ocre, bouche, arbres hauts aplatis), bouche percée sur calque dédié,
  couloir de sable quilté (patches natifs 24×16, coutures sans fondu) + 5 tampons
  contrôlés (2 arbres morts resserrés, 3 semis de cailloux) hors du passage.
  Entrée (206, 90), passage |x−206| ≤ 34 jusqu'au bord sud.
- **Violet** `violet_underground_road`, 504×488 : couronne + colonnes de parois
  translatées (coupes verticales x=136/368, bande d'extension y=408 répétant des
  rangées natives — couture signalée), deux bouches percées (gauche = principale,
  documenté), sol du couloir re-quilté + 3 tampons d'éboulis. Entrées (148, 140)
  et (355, 140), chemin fourchu depuis le sud.

## Calques et fichiers

`SouthNorthV4_<carte>_<calque>_<jour|nuit>.png` (noms uniques), origine commune,
TSX 8 px descriptifs, provenance NPZ `source_sxy` par pixel, `composite_*.png`,
`path_connectivity_mask.png`, `access_review_NOT_RUNTIME.png` (trajet indicatif,
pas une collision moteur). Nuit = filtre Abyss exact appliqué une seule fois
par calque. Les deux bouches violettes sont pixel-identiques dans la référence
(n=1546 chacune) ; aucune n'est inventée.

## Paquet natif (`paquet_natif/`)

4 `.rsground` (2 cartes × jour/nuit, TexSize 1) + 4 `.tile` (une banque dédoublonnée
par carte et par mode) + `manifest.json` + `INSTALLER.py`. Rendu indépendant
(`tools/pmdo_tiles.py`) **pixel-identique aux composites (diff 0)** sur les 4 cartes.
Collisions : première passe automatique (parois/bouches opaques ≥ 50 %, pieds de
troncs arides) **à affiner dans l'éditeur**. Marqueurs `entrance` (sud) et
`donjon_seuil` (bouche) fournis **sans destination** : raccorder dans l'éditeur.

## Limites

- 66 contrôles PNG + 4 rendus natifs PASS (`verification.json`) ; **PMDO non testé**,
  art non approuvé, 16 layouts du programme restants (`FULL_PROGRAMME_STATUS.json`).
- Les arbres morts arides sont aplatis dans le sol (pas d'occlusion) : ils sont
  placés hors du passage et leurs pieds sont bloqués en collision.
- La couture y=408 du couloir violet répète des rangées natives (discontinuité
  de texture possible, pixels natifs des deux côtés).

Galerie : `apercu_entrees_sud_nord_v4.html`. Reconstruction :
`source/zones_south_north_v4/{build,verify,build_native,make_gallery,package}.py`.
