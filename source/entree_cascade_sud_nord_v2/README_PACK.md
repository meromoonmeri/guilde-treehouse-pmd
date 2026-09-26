# Entrée Cascade V2 sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_cascade_sud_nord_v2` : un Ground `ecn2_entree_cascade` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`). Décor **généré d'après les rips Waterfall Cave** (méthode « rendu généré référencé PMD » de la série), bassins façon Métano, cascade et scintillements Métano natifs.

## Installer

- **Projet séparé** : copier `entree_cascade_sud_nord_v2` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Bassins façon Métano (palette des sources turquoise de Waterfall Cave) | 4 × 10 ticks |
| 01 | Cascade (frames Métano natives, translation pure) | 4 × 10 ticks |
| 02 | Scintillements Métano natifs | 4 × 10 ticks |
| 03 | Sol complet (galets) | fixe |
| 04 | Fond vide | fixe |
| 05 | Plafond et stalactites | fixe |
| 06 | Parois de rochers | fixe |
| 07 | Pierres | fixe |
| 08 | Cristaux | fixe |
| 09 | vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` au sud, au bas de la chaussée ; `donjon_seuil` sur la plateforme au pied de la cascade. **Aucun warp.**
- Praticable = sol visible. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- Le décor est généré (pas de tuiles natives) ; les bassins sont des pixels recalculés façon Métano.
- La cadence de la cascade (10 ticks) est proposée, pas prouvée par la map Métano.
- Aucun test dans PMDO.
