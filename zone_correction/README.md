# Zone corrigée — référence `image.png`

Cette reconstruction utilise **`image.png` comme référence artistique stricte**. La DA, la palette, la texture du sol, les silhouettes de rochers, l'entrée rocheuse et les fleurs sont conservées.

`IMG_4854.png` sert uniquement de référence de construction pour le principe de couloir, l'ouverture entre les falaises et les bordures modulaires. Elle ne remplace pas la palette ni le rendu de `image.png`.

## Correction effectuée

- suppression de l'entité centrale ;
- correction du rendu du sol pour éviter les ruptures de texture et les raccords visibles ;
- entrée de falaise reconstruite avec variantes gauche/droite, coins et ouverture ;
- sol et transitions exportés séparément ;
- rochers exportés comme sprites indépendants ;
- fleurs et végétation des bordures exportées indépendamment ;
- aperçu final sur une grille PMDO de 8 px : `final/zone_corrigee.png`.

Les études de génération sous `source/generation/` sont des références de reconstruction. Elles ne sont pas découpées directement pour faire les tuiles finales.

## Sorties

```text
final/zone_corrigee.png                 528 × 384, rendu final PMDO
final/zone_corrigee_generateur.png      rendu généré haute résolution, sans entité
planches/01_cliff_entree.png             entrée et bordures de falaise
planches/02_sol.png                      sol contrôlé + transitions
planches/03_rochers.png                  sprites indépendants de rochers
planches/04_bordures_fleurs.png          fleurs et végétation indépendantes
sprites/                                 rochers et fleurs séparés
pmd/Content/Tile/*.tile                  feuilles PMDO de 8 × 8 px
tiled/zone_corrigee.tmj                  carte Tiled 66 × 48, cellules 8 × 8
aseprite/zone_corrigee.aseprite          composition inspectable dans Aseprite
```

## Reproduction

```bash
.venv/bin/python zone_correction/build_zone.py
.venv/bin/python zone_correction/verify.py
```

La reconstruction finale reste volontairement proche de l'image fournie : il s'agit d'une correction de structure et de modularité, pas d'une nouvelle direction artistique.
