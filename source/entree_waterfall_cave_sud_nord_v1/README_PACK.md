# Entrée Waterfall Cave sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_waterfall_cave_sud_nord`. Il contient un Ground `ewc1_entree_waterfall_cave` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`), environ 2,4 × 2,4 écrans PMDO.

## Installer

- **Projet séparé** : copier `entree_waterfall_cave_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau des bassins et de la vasque, façon Métano (couleurs Métano exactes) | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet (sable) | fixe |
| 03 | Sable praticable | fixe |
| 04 | Cailloux | fixe |
| 05 | Touffes | fixe |
| 06 | Plateaux (sable en haut des falaises) | fixe |
| 07 | Berge des bassins | fixe |
| 08 | Falaises | fixe |
| 09 | Arbres | fixe |
| 10 | Entrée sombre (bouche derrière la cascade) | fixe |
| 11 | Rideau de la cascade | 12 × 4 ticks |
| 12 | Écume du pied | fixe |
| 13 | Écume, bouillons générés | 12 × 4 ticks |
| 14 | Embruns générés | 12 × 4 ticks |
| 15 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 240 ticks (4 s).

## Marqueurs et collisions

- `entrance` est au sud, sur la plage. `donjon_seuil` est au bord nord du parvis, face à la bouche cachée derrière la cascade : on entre en marchant vers la cascade. **Aucun warp.**
- Sont praticables le sable relié au sud, les cailloux et les touffes enclavées dans ce sable. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, cascade, écume et embruns** : dessins générés à partir de la capture `entrancecascade.png`. Le défilement de la cascade, les émetteurs et la chronologie sont créés par nous ; ce ne sont pas des animations officielles.
- **Eau** : façon Métano, pixels recalculés avec les couleurs Métano exactes.
- **Scintillements** : seuls pixels Métano natifs du pack.
- **Tests** : aucun test fait dans PMDO.
