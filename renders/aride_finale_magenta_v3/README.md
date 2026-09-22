# Entrée aride — version finale V3 (magenta → palette native)

Map assemblée depuis **5 bruts générateur sur fond magenta**, guidés par la
référence canonique `entrancearidedungeonpmdsky.png` :
`cliff_magenta` (parois + bouche), `sol_magenta`, `chemin_magenta` (sentier en S),
`props_magenta` (4 arbres + 2 blocs + 6 cailloux), `ombre_magenta`
(bandeau + 2 rondes + 2 ovales). Les 6 éléments demandés, rien d'autre
(pas de FX : `fx_magenta` généré puis écarté sur consigne « seulement »).

## Méthode

Inondation du magenta depuis les bords + pelage 2 px → /3 NEAREST → **remap
100% palette native** (99 couleurs de la référence, plus proche voisin sans
trame) → 6 calques → assemblage 408×288 sud→nord. Rejetés documentés :
`parois_magenta` (bol avec fond rocheux), `guide_compo_v2` (plein cadre,
hors méthode magenta).

## Contenu

- `L00_sol.png` — sable plein cadre (cadre magenta rebouché au sable vrai le plus proche)
- `L01_chemin.png` — sentier en S avec empreintes, arrêté au seuil de la bouche
- `L02_cliff.png` — parois + bouche (bbox [184,40,224,91]), corridor transparent
- `L03_roches.png` — 2 blocs avant-plan sud + 6 cailloux le long du sentier
- `L04_arbres.png` — 4 arbres morts, pieds sur sable, corridor dégagé
- `L05_ombres.png` — bandeau au pied du cliff + ombres sous props (alpha 110, requantifié natif)
- `sprites/` — 12 props + 5 ombres individuels
- `composite.png`, `access_review.png`, `aride_finale_magenta_v3.ora`
- `manifest.json`, `verification.json`

Galerie : `apercu_aride_finale_magenta_v3.html` (racine). Pack : `renders/aride_finale_magenta_v3_pack.zip`.

## Honnêteté du lot

- Motifs **générés**, pixels 1× nets, palette **100% native** (testée : 0 couleur hors palette, 0 magenta résiduel, RGB zéro sous alpha 0).
- Sentier et ombres : créations d'assemblage (alpha 110 documenté), pas des cycles/tiles officiels.
- Accès sud (204,284) → seuil bouche (204,93) vérifié connecté, corridor ≥ 40 px à y=150. Ni collisions ni warps moteur.
- 10 tests PASS. Pas de test PMDO/GPU.

## Reproduction

```sh
.venv/bin/python source/aride_finale_magenta_v3/build.py
.venv/bin/python source/aride_finale_magenta_v3/package.py  # ORA + galerie + ZIP + tests
```
