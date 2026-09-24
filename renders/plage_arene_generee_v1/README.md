# Plage / arène côtière V1 — rendu généré référencé PMD, 6 calques

Référence : `arenapmdskybeach.png` (456×480, conservée intacte dans
`source/plage_arene_generee_v1/references/`). Arrivée SUD (ouverture sculptée),
mer et perspective au NORD.

## Méthode (honnête)

- 1 composition complète générée guidée par la référence (même DA, layout
  légèrement différent : arène élargie, champ de blocs central).
- Normalisation uniforme isotrope (×0,4524, recadrage centré 0 px : le brut
  est déjà au ratio exact), jamais d'étirement anisotrope.
- Le brut fermait le sud par un monticule rocheux : ouverture sculptée en
  entonnoir (16/20/24 px depuis y395/405/415) par pavage cyclique du sable
  strict du brut — 3860 px documentés, zone retouchée 100 % sable testée.
- Découpe couleur en partition stricte pleine page + murs par propagation :
  graines (bords, massifs ≥2500 px, dents proches du vide ≥300 px) puis
  absorption des pans à ≤16 px. Reflets bleus enfermés dans la roche (<600 px)
  gardés en falaise ; speckles <12 px rendus aux voisins.
- **Dessins générés, PAS des pixels natifs, PAS une mosaïque de bouts de maps.**

## Contenu

| Fichier | Rôle |
|---|---|
| `couches/PlageAreneV1_01_mer.png` | Mer latérale + bassin nord |
| `couches/PlageAreneV1_02_sable.png` | Sable de l'arène + entonnoir sud |
| `couches/PlageAreneV1_03_falaises.png` | Falaises rouges, mousse, arche nord |
| `couches/PlageAreneV1_04_ecume.png` | Écume, cascade nord, coquillages |
| `couches/PlageAreneV1_05_rochers.png` | 8 blocs/monticules déplaçables |
| `couches/PlageAreneV1_06_vide.png` | Vide hors terrain (coins nord) |
| `scene/scene_complete.png` | Recomposition exacte des 6 calques |
| `review/planche_calques.png` | 6 calques sur damier + scène |
| `PlageAreneV1.ora` | Projet éditable 6 calques |
| `manifest.json` | Tailles, hashes, corridor, méthode |
| `apercu_plage_arene_v1.html` (racine) | Viewer autonome : calques, grille 8 px, zoom |

Corridor : 48/48 colonnes sans falaise sur [420,480] dans l'ouverture, bord sud
en sable, entonnoir connecté au sable de l'arène. Indicatif seulement : pas de
collisions, warps ni test PMDO. Grille 8 px : 57×60 cases.

## Limites

- Les rochers incluent des monticules à teinte sableuse (relief ombré,
  obstacles déplaçables) : teinte du brut, pas une erreur de tri.
- Masquer un calque laisse des trous (partitions de surfaces visibles, pas
  objets complets avec faces cachées).
- Aucune animation (lot statique demandé) ; aucune validation artistique.
- La référence et tous les anciens lots restent inchangés.

## Reproduction

```sh
.venv/bin/python source/plage_arene_generee_v1/build.py
.venv/bin/python source/plage_arene_generee_v1/package.py  # tests + ZIP
.venv/bin/python -m unittest source.plage_arene_generee_v1.test_build -v
```
