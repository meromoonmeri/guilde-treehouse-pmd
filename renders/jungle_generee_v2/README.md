# Jungle generee V2 — terrain strict magenta, 5 calques, echelle PMDO

Map 512×640 sud → nord, **art genere refere PMD (methode magenta), PAS natif**.
Reponse a la correction : generateur strict sur fond magenta, arbres canoniques
generes separement, echelle PMDO.

## Bruts (prompts stricts, references jungle + Southern Jungle)

- `source/jungle_generee_v2/bruts/terrain_strict.png` (848×1264) : 6 chutes coupees
  au bord haut (source cachee), 2 bassins + ecume, falaise, palmiers lateraux,
  clairiere + chemin + buissons. Consigne stricte : pixels nets, pas de ciel,
  pas de source visible, proportions PMD Sky.
- `source/jungle_generee_v2/bruts/arbres_canoniques.png` (1179×896) : 6 arbres
  jungle (troncs noueux + canopees palmees), 2 utilises.
- `source/suite_generee_v1/bruts/jungle_cascades_sol.png` : sol plein cadre (reutilise).

## Normalisation uniforme + echelle PMDO

- Terrain : **NEAREST x0.5** → 424×632 pose a (44,0), pixels nets, jamais anisotrope.
- Arbres : x0.45 (~170px, proportions PMD Sky), halo magenta elimine
  (decontamination + regle min(R,B)-G>25, zero residu teste).
- Scene **512×640 = 64×80 cases de 8 px**, TexSize=1 : prete import
  **PNG to Tileset 8 px sans reechantillonnage**. Grille 8 px dans le viewer.

## Les 5 calques (partition exacte du terrain + sol + arbres)

| # | Calque | Contenu |
|---|--------|---------|
| 01 | sol | sol genere plein cadre (cover + crop centre) |
| 02 | paroi | falaise + frange haute (y<290, hors chutes/eau) |
| 03 | cascades | **calque propre** : 6 chutes, 18 phases × 16 px = boucle 288 px exacte, 80 ms |
| 04 | bassins | eau + ecume (masque colorimetrique, colonnes masquees en pleine ecume) |
| 05 | vegetation | residu terrain + 2 arbres canoniques (premier plan) |

Alpha par inondation magenta depuis les bords + seuils serres. Recomposition
canvas/PIL exacte par construction (testee pixel par pixel).

## Animation (mouvement NOUVEAU, pas un cycle officiel)

Roulement vertical pleine hauteur, offsets par chute, pieds en pleine ecume.
`JungleG2_animation.gif` : boucle 1440 ms. `cascades_phases/` : 18 PNG.

## Recomposition

- `JungleG2_composite_phase_00.png`, `JungleG2_5_calques.ora`, TSX 8 px.
- `apercu_jungle_generee_v2.html` : calques, 18 phases, grille PMDO, zoom, export PNG.

## Limites honnetes

- Art genere : fidelite de style revendiquee, pas de pixels natifs ; V1 native conservee en parallele.
- Decoupe des calques = partition colorimetrique/geometrique, pas objets semantiques parfaits.
- Chemin lisible visuellement ; collisions/warps non implementes, runtime NOT TESTED.

## Reproduire

```sh
.venv/bin/python source/jungle_generee_v2/build.py
.venv/bin/python -m unittest source.jungle_generee_v2.test_build -v
.venv/bin/python source/jungle_generee_v2/package.py
```
