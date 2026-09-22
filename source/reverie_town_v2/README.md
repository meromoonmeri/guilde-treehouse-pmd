# Reverie Town v2 — plateaux « plus libres » avec la feuille MIROIR (option « comme CLIFF MIROR »)

Suite du chantier v1 (`source/reverie_town_v1/`). L'utilisateur a choisi, pour les bords de plateau orientés est
(inexistants dans la feuille native `Metano_Town_Cliffs`), la solution **miroir** : comme sa propre feuille
« CLIFF MIROR », les tuiles nécessaires sont le **miroir horizontal exact** des tuiles natives. Rien d'autre n'est
transformé (pas de recoloration, rotation, agrandissement ni repeinte) et tout est marqué **miroir**.

## Livré

| Élément | Emplacement |
|---|---|
| Feuille miroir jour/nuit (`RVT_Cliffs_Miroir.png`, `RVT_Cliffs_Miroir_Nuit.png` = miroir de `Metano_Town_Cliffs[_Night]`) | `source/reverie_town_v1/kit/` |
| 7 modules miroir dans le kit (`rim_est`, `rim_est_vers_bloc`, `rim_est_crans`, `bord_droit_clair_miroir`, `bord_gauche_sombre_miroir`, macros `terrasses_*_ouest_miroir`), contour **rouge** sur la planche de contrôle | `kit/modules.json` (`modules_miroir`), `kit/kit_index.json`, `kit/REVERIE_KIT_Falaises_Metano_planche.png` |
| Carte **RVT2_NE** — 100 % natif : coin sud-ouest du plateau en escalier (face haute, descente native T3→T5→T7), bande ouest basse avec la route nord native (sortie nord), village au sud | `exports/reverie_town_v2/RVT2_NE/` |
| Carte **RVT2_NO** — vrai plateau de coin nord-ouest : côté est visible (montée miroir T7→T5→T3, bord droit clair miroir, liseré est miroir), bande est basse avec la route native qui sort par l'est | `exports/reverie_town_v2/RVT2_NO/` |
| Calques PNG 8 px à noms uniques `RVT2_<carte>_00_sol`, `01_falaises`, `02_anim_p1..p4`, `03_objets` × `_jour`/`_nuit`, composites, `provenance.json` (`mirror_tiles` = nombre de tuiles miroir : NE 0, NO 249) | idem |
| Paquet natif 0.8.12.0 : 4 `.rsground` (`rvt2_ne_jour/nuit`, `rvt2_no_jour/nuit`), `.tile` personnalisés `RVT2_*`, **`RVT_Cliffs_Miroir.tile` + `RVT_Cliffs_Miroir_Nuit.tile`** (222 tuiles chacune, disposition = feuille miroir), `manifest.json`, `INSTALLER.py` | `exports/reverie_town_v2/paquet_natif/` |
| Aperçu HTML | `exports/reverie_town_v2/index.html` |

Format : 123 × 99 tuiles de 8 px = 984 × 792 px = 41 × 33 cases (comme les tests de l'utilisateur).

## Géométrie (identique sur les deux cartes)

- Couronne du niveau haut rangée **14**, couronne du mur principal rangée **30** (= 14 + 16 : deux marches natives
  de 64 px, colonnes natives `tx 81..91` posées verbatim : fin de face T3, bloc T5, raccord, début T7) ; pied du
  mur rangée 41, village rangées 42–98.
- RVT2_NE : liseré ouest natif (col 18) → `bord_gauche` → 12 colonnes de face haute → descente native → cascade,
  `face_b`, porte, face, escalier, face, colonne native `tx 164` → terrasses montantes natives U1..U3 jusqu'au
  bord est. Plateau = nord-est, bande ouest (cols 0–17) = terrain bas.
- RVT2_NO : face haute depuis le bord ouest → descente native → escalier, `face_b`, porte, `face_a`, cascade,
  22 colonnes de face → **montée miroir** (`Scene.mirror_blit(81, 91, …)`) → 10 colonnes de face haute natives →
  `bord_droit_clair_miroir` → `rim_east` (miroir de la colonne native 57). Plateau = nord-ouest, bande est
  (cols 104–122) = terrain bas.
- Chemins : couloirs de sable natifs de `Metano_Town_Base` (tuiles entières). Route nord native (tuiles 26–47 ×
  0–46) posée avec **dy = +6** pour que son virage passe sous le pied du mur et non « derrière » le bord du
  plateau ; les 6 rangées du haut reprennent les rangées natives 0–5 de la même route (seule répétition de
  tuiles : 48 px de route droite au bord de carte, signalée ici). Le chemin du pied d'escalier est la composante
  native du pied d'escalier correspondant ; ses extrémités coupées sont masquées par un bâtiment (dojo en NE,
  maison Shellder en NO) ou sortent de la carte.
- Nuit : feuilles natives `_Night` (sol, falaises **et** feuille miroir nuit = miroir de `Metano_Town_Cliffs_Night`) ;
  filtre Abyss exact pour objets et eau animée (pas de feuille nuit native).

## Correctifs appliqués à l'occasion (aussi régénérés dans v1)

1. `RVT_NE` v1 : la colonne native `tx 164` était lue à `ty = R` (tuile vide) → **fente d'herbe de 8 px** dans le
   mur entre l'escalier et la terrasse U1. Corrigé (`ty = 56`).
2. Tuiles de sol natives **à trous transparents** (dans la ville native elles sont recouvertes par un objet) : elles
   laissaient voir le fond noir de la carte (barre noire près du carrefour). `blit_masked` n'écrase plus le sol
   qu'avec des tuiles entièrement opaques.
3. Tuiles de **berge de rivière** (eau) prises dans la composante de sable : exclues dans `sand_tile_mask`.

## Vérifications

- `build_kit.py` : chaque tuile du kit identique à sa source ; chaque tuile miroir = retournement exact de la tuile
  native `(188 − tx′, ty)` ; miroir(miroir) = feuille native.
- `Scene.verify()` : chaque tuile posée identique à sa tuile source (feuille native ou miroir), nuit comprise.
- `verify.py` : les 4 `.rsground` rendus par le décodeur indépendant `tools/pmdo_tiles.py` (avec les `.tile` du jeu +
  `RVT2_*` + `RVT_Cliffs_Miroir*`) sont identiques pixel à pixel aux composites, 4 phases, jour et nuit (nuit :
  8 pixels à ±1 par carte, arrondi de l'alpha prémultiplié du format `.tile`).
- **Aucun test dans le moteur PMDO** (absent du bac à sable) : ouvrir d'abord dans PMDO Dev. Collisions =
  première passe automatique (`Tags 1` bloqué), à affiner dans l'éditeur.

## Limites

- Éclairage : les blocs miroir ont leur côté clair à droite (l'original l'a à gauche) — inhérent à l'option miroir,
  visible seulement en comparant les deux extrémités du plateau. Utilisé uniquement sur le côté est de RVT2_NO.
- Pas de rivière/pont natifs ; pas d'ombres portées ni de calque avant-plan séparés.

## Reproduire

```bash
.venv/bin/python source/reverie_town_v1/build_kit.py     # kit (natif + miroir) + feuilles miroir + planche
.venv/bin/python source/reverie_town_v2/carte_ne.py      # RVT2_NE (calques, composites, provenance)
.venv/bin/python source/reverie_town_v2/carte_no.py      # RVT2_NO
.venv/bin/python source/reverie_town_v2/build_native.py  # paquet natif (+ .tile miroir)
.venv/bin/python source/reverie_town_v2/verify.py        # recomposition indépendante (16 rendus)
.venv/bin/python source/reverie_town_v2/make_viewer.py   # exports/reverie_town_v2/index.html
```
