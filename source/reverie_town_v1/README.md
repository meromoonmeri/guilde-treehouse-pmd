# Reverie Town v1 — kit « Falaises Métano » natif + deux cartes de village (NE / NO)

Chantier repris le 22/09/2026 : l'utilisateur veut des cartes aux **textures canoniques** (natives Métano),
livrées en **calques PNG 8 px** (import « PNG to Tileset » de PMDO Dev) **et** en **paquet natif** (.rsground + .tile),
chacune **en version jour et nuit**.

## Ce qui est livré

| Élément | Emplacement |
|---|---|
| Kit de modules natifs (planche importable jour/nuit + planche de contrôle 2× + index JSON) | `kit/REVERIE_KIT_Falaises_Metano_{jour,nuit}.png`, `kit/REVERIE_KIT_Falaises_Metano_planche.png`, `kit/kit_index.json`, `kit/modules.json` |
| Carte **Nord-Est** `RVT_NE` (123×99 tuiles = 984×792 px = 41×33 cases) | `exports/reverie_town_v1/RVT_NE/` |
| Carte **Nord-Ouest** `RVT_NO` (même format) | `exports/reverie_town_v1/RVT_NO/` |
| Calques PNG 8 px, noms uniques : `RVT_<carte>_00_sol`, `01_falaises`, `02_anim_p1..p4`, `03_objets`, chacun `_jour` / `_nuit` | idem |
| Composites de contrôle jour/nuit (phase 1 et phases 1–4) + `provenance.json` (feuille, tx, ty de chaque tuile) | idem |
| Aperçu HTML (jour/nuit, animation, calques) | `exports/reverie_town_v1/index.html` |
| Paquet natif PMDO 0.8.12.0 : 4 `.rsground` (NE/NO × jour/nuit) + 6 `.tile` personnalisés + `manifest.json` + `INSTALLER.py` | `exports/reverie_town_v1/paquet_natif/` |

## Méthode (résumé)

1. **Lecture de la feuille native** `Metano_Town_Cliffs` (1512×544, calée sur la Base en (0,0)) : la falaise
   Métano est faite de **blocs arrondis** = bord gauche clair + face + bord droit sombre (avec fentes natives),
   couronne d'herbe, face de **12 rangées (96 px)**, texture **périodique sur 32 px** avec la même phase partout
   (couronnes natives à y ≡ 5 mod 32). Les marches entre blocs valent ±32 ou ±64 px. Il n'existe **aucun bord
   orienté est** (seulement faces sud + liseré ouest) : les cartes évitent donc les bords est nativement, avec les
   motifs natifs « terrasses descendantes vers l'est » (T0..T7) et « terrasses montantes vers l'est » (U1..U3).
2. **Kit** (`kit/modules.json`, construit par `build_kit.py`) : rectangles exacts en tuiles de 8 px ; chaque tuile
   du kit est vérifiée identique à sa tuile source (jour et nuit `Metano_Town_Cliffs_Night`).
   Modules : `bord_gauche`, `bord_droit`, faces `face_a/b/c` (petites pierres) et `face_grosses_pierres_t1/u2`,
   `escalier`, `porte`, `cascade_statique`, `rim_ouest*`, `herbe_plateau`, macros `terrasses_descendantes_A`
   et `terrasses_montantes_C`.
3. **Assemblage** (`assemble.py`, `carte_ne.py`, `carte_no.py`) : une tuile posée = une tuile native copiée telle
   quelle (jamais recolorée, tournée, retournée, agrandie). Herbe = tuiles d'herbe pures natives tirées selon leur
   fréquence native. Chemins = **couloirs de sable natifs** de `Metano_Town_Base` (tuiles entières, composante
   connexe du pied de l'escalier, relocalisée avec le même décalage que l'escalier ; les extrémités coupées sont
   masquées par un bâtiment ou sortent de la carte). Cascade = image fixe native dans le mur + 4 images natives
   de `Metano_Town_Animation_Tileset` (calage vérifié : boîte d'eau identique 58×120). Mare = 3 images natives.
   Objets = rectangles de `Metano_Town_Objects` ; les **objets propres** sont des tuiles natives entières ; les
   bâtiments dont le rectangle natif contient des taches de sable voisines sont **découpés** (pixels étrangers
   retirés, aucun pixel repeint ; tuiles marquées « découpe », 29 tuiles par carte).
4. **Nuit** : feuilles natives `*_Night` pour sol (Base) et falaises (Cliffs) ; pour objets et eau animée (pas de
   feuille nuit native) : filtre Abyss exact (`source/cote_v4_abyss/night.py`) appliqué une seule fois par tuile.
5. **Paquet natif** (`build_native.py`) : les tuiles natives entières référencent directement les feuilles du jeu
   (`Metano_Town_Base`, `_Cliffs`, `_Objects`, `_Animation_Tileset`, `_River_Animation_1..4`, `*_Night`) ; seules
   les tuiles découpées / filtrées vont dans `RVT_<carte>_<mode>_<calque>.tile` (écrivain `.tile` validé des
   paquets précédents). Animation : 4 images, `FrameLength 10` comme l'eau native. Collisions : première passe
   automatique (`Tags 1` = bloqué, convention de `cliffdaytest.rsground`) — rochers des faces, eau, tuiles d'objets
   couvertes ≥ 90 % ; planches d'escalier et seuil de porte libres. **À affiner dans l'éditeur.** Un marqueur
   `entrance` est posé sur une case libre près du bord sud (arrivée par le sud, objectif au nord).
6. **Vérifications** (`verify.py`) : chaque `.rsground` rendu par le décodeur indépendant `tools/pmdo_tiles.py`
   (lecture des `.tile` du jeu + personnalisés) est identique pixel à pixel au composite PNG, pour les 4 phases,
   jour et nuit (nuit : 8 pixels semi-transparents à ±1 par carte, arrondi de la prémultiplication alpha imposée par
   le format `.tile`). En amont, `Scene.verify()` contrôle chaque tuile posée contre sa tuile source.

## Limites et suites

- **Aucun test dans le moteur PMDO** (absent du bac à sable) : ouvrir d'abord dans PMDO Dev.
- Pas d'ombres portées séparées ni de calque avant-plan (les objets natifs Métano sont entiers, dessinés sous les
  personnages comme dans la ville native).
- La rivière native n'est pas utilisée (ses coupes ne se cachent pas) ; la cascade se jette dans une mare native.
- Objets « L jaunes » (raccords d'herbe de la feuille Objects) volontairement écartés.
- Étapes suivantes possibles : rivière + pont natifs, tuiles de collision affinées, PNJ/portes (script), variantes
  de largeur des terrasses avec `bord_droit` + `bord_gauche` (jonctions ±32 px composées), grande carte fusionnée.

## Reproduire

```bash
.venv/bin/python source/reverie_town_v1/build_kit.py        # kit + planches + vérification tuile à tuile
.venv/bin/python source/reverie_town_v1/carte_ne.py         # calques PNG + composites + provenance (NE)
.venv/bin/python source/reverie_town_v1/carte_no.py         # idem (NO)
.venv/bin/python source/reverie_town_v1/build_native.py     # .rsground + .tile + manifest
.venv/bin/python source/reverie_town_v1/verify.py           # recomposition indépendante (16 rendus)
.venv/bin/python source/reverie_town_v1/make_viewer.py      # exports/reverie_town_v1/index.html
```
