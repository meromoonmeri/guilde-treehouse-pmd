# Jungle aux cascades V1 — 5 calques natifs stricts

Map 512×640, orientation sud → nord : arrivee en bas, chemin central vers les bassins
sous les chutes au nord. **Aucun pixel genere dans les exports.**

## Sources natives (pixels exacts, provenance NPZ par pixel)

- `junglewaterfallzonepmdsky.png` : herbe, chemin, falaise, 6 chutes, bassins, ecume,
  mares, buissons, rochers, galet.
- `Southern_Jungle_exit_2_S.png` : 2 arbres jungle canoniques (tronc + canopee).

Le brut `source/suite_generee_v1/bruts/jungle_cascades_terrain.png` est un GUIDE de
composition uniquement. Son rebord montrant la source des chutes est rejete : les
6 chutes sont coupees au bord haut, pieds en pleine ecume.

## Les 5 calques

| # | Calque | Contenu |
|---|--------|---------|
| 01 | sol | herbe sombre plein cadre + chemin clair continu (patchs natifs, coutures sans fondu) |
| 02 | paroi | mur falaise y0-368, modules natifs entiers repetes (joints documentes) |
| 03 | cascades | 6 chutes longues coupees en haut, 26 phases sur calque propre |
| 04 | bassins | 2 bassins + ecume + 2 mares (colonnes masquees jusqu'en pleine ecume) |
| 05 | vegetation | 2 arbres canoniques + franges, murs de buissons, buissons, rochers, galet |

Aucune rotation, miroir, echelle ni recoloration. Fichiers `*_source.npz` = carte
`(source, x, y)` de chaque pixel. TSX 8 px descriptifs joints.

## Animation des chutes (mouvement NOUVEAU, pas un cycle officiel)

- 26 phases × 80 ms = boucle exacte 2080 ms ; roulement vertical 16 px/phase sur
  416 px (26×16=416 : phase 26 ≡ phase 0 pixel par pixel, teste).
- Offsets par chute (0/32/64/16/80/48 px) pour un ecoulement non synchrone.
- Propriete native verifiee : la texture de chute est exactement 96-periodique.
- Jonction anime/statique placee en pleine ecume (turbulence blanche).

`JungleV1_animation.gif` : boucle complete. `cascades_phases/` : 26 PNG + 26 NPZ.

## Recomposition

- `JungleV1_composite_phase_00.png` : pile exacte des 5 calques (teste pixel par pixel).
- `JungleV1_5_calques.ora` : projet multicouche editable.
- `apercu_jungle_cascades_v1.html` : recomposition web (calques isolables, lecture des
  26 phases, grille 8 px, zoom 1×/2×, export PNG de la phase courante).

## Limites honnetes

- Continuite du chemin = controle pixels uniquement, PAS collisions/warps/occlusion.
- Joints du mur falaise et raccords buissons : modules natifs juxtaposes, revoir a 1×.
- Pas d'import PMDO/Tiled ni de test moteur : `runtime NOT TESTED`, art non approuve.
- Le GIF fusionne les durees standards ; la cadence de reference est 80 ms (manifeste).

## Reproduire

```sh
.venv/bin/python source/jungle_cascades_v1/build.py
.venv/bin/python -m unittest source.jungle_cascades_v1.test_build -v
.venv/bin/python source/jungle_cascades_v1/package.py
```
