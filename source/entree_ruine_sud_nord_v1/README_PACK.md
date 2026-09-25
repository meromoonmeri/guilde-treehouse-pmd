# Entrée Ruine sud → nord — projet PMDO 0.8.12

Projet d'édition autonome `entree_ruine_sud_nord` : un Ground `ern1_entree_ruine` (424 × 632 px, 53 × 79 cases de 8 px, `TexSize=1`).

## Installer

- **Projet séparé** : copier `entree_ruine_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run` (l'index des tilesets est fusionné).

## Calques du Ground (de bas en haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Sables mouvants façon rivière de Métano | 4 phases × 10 ticks |
| 01 | Bulles de sable générées | 24 phases × 5 ticks, émetteurs décalés |
| 02–07 | Sol complet, sable, rebords des fosses, rochers, falaises, bouche | fixes |
| 08 | Tourbillons de poussière générés (décoratifs, non bloquants) | 8 phases × 5 ticks |
| 09 | Arbres morts | fixe |
| 10 | vide, `Layer=4` (Top) | pour l'avant-plan |

La scène boucle en 120 ticks (2 s).

## Marqueurs et collisions

- `entrance` au sud, `donjon_seuil` devant la bouche, au nord. **Aucun warp.**
- Seul le sable est praticable. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, bulles et tourbillons** : générés à partir de la référence Sealed Ruin. Ce ne sont ni des pixels natifs, ni des animations officielles.
- **Sables mouvants** : inspirés de la structure de la rivière Métano.
- **Tests** : aucun test dans PMDO.
