# Entrée de forêt — sol Vast Steppe, rochers Amp Plains, arbres Halcyon (calque propre)

Composition en trois calques + composite, grille 8 px, **512 × 384 px**.

- `entree_00_sol.png` : sol 100 % canonique, tuiles prises directement dans
  `Vast_Steppe_Base.tile` (Halcyon), deux variantes d'herbe en damier + chemin clair.
- `entree_01_rochers.png` : rochers canoniques **Amp Plains Entrance**
  (ExplorersOfSkyOrigins, 24 px), détourés par propagation depuis les bords.
- `entree_02_arbres.png` : **les mêmes arbres canoniques de Halcyon**
  (`Vast_Steppe_Objects`/`Fringe`), extraits en sprites (`trees_canoniques/HalArbre_*.png`)
  puis posés sur leur propre calque selon un **masque de placement issu du générateur**
  (`generation/placement_arbres.png`). Le générateur ne fournit que le placement ;
  les pixels des arbres sont canoniques.
- `entree_composite.png` : sol + rochers + arbres.
- Tiled : `entree_foret.tmx` + `entree_sol.tsx` / `entree_sol_2tiles.png`.

## Reconstruction et tests

```sh
python source/entree_foret_halcyon_v1/build.py
python source/entree_foret_halcyon_v1/test_build.py
```

Le test vérifie : blocs du sol identiques aux tuiles `Vast_Steppe_Base`, pixels des
rochers et des arbres tous présents dans leurs références canoniques, composite
recomposable, TMX/TSX valides, références byte-intactes (`provenance.json`).

## Limites

Pas d'import PMDO réel ; collisions / warps non configurés. Les arbres conservent leur
frange d'herbe native (ils se fondent dans le sol). Ressources © leurs auteurs.
