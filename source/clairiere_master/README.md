# Masters de la clairière (source)

Copie brute depuis `meromoonmeri/zone-pmd@0f9805e` :

- `base.png` — `layers/src/clairiere_pmdo/base/clairiere_base_a.png`, 1120 × 960 RGB.
- `eau/etat0..3.png` — les 8 frames `eau/f01..f08` ne contiennent que 4 images
  distinctes (séquence 0,0,1,1,2,2,3,3) : on ne garde que les états.
- `lumiere_simple/etat0..2.png` — rayon (séquence 0,1,2,2,2,2,2,1).
- `lumiere_evolution/etat0..4.png` — étincelles (séquence 0,1,2,3,4,3,2,1).
- `masque_bassin.png`, `masque_arbre.png` — `tiled/clairiere/render_layers/`,
  découpes de l'auteur, gardées pour référence (la collision est relevée par
  couleur sur `base.png`, voir `build_clairiere.py`).

`lumiere_validee` n'a pas été reprise : c'est une variante du rayon (55 % de
différence avec la simple) que l'auteur n'a pas retenue dans son export final.
