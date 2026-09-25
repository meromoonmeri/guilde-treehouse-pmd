# Entrée Jungle sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_jungle_sud_nord` : un Ground `ejn1_entree_jungle` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`, environ 2,4 × 2,4 écrans PMDO).

## Installer

- **Projet séparé** : copier `entree_jungle_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Rivière et mare façon Métano | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet | fixe |
| 03 | Clairière | fixe |
| 04 | Sentier | fixe |
| 05 | Terre | fixe |
| 06 | Berge | fixe |
| 07 | Rochers | fixe |
| 08 | Îlots d'arbres | fixe |
| 09 | Jungle | fixe |
| 10 | Entrée sombre | fixe |
| 11 | Papillons générés | 48 × 5 ticks, boucle de 4 s |
| 12 | vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` au sud, sur le sentier ; `donjon_seuil` sous l'entrée sombre, au nord. **Aucun warp.**
- La clairière, le sentier et la terre sont praticables. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain et papillons** : dessins générés d'après la référence Southern Jungle ; les trajectoires sont créées par nous.
- **Rivière** : façon Métano, pixels recalculés.
- **Tests** : aucun test dans PMDO.
