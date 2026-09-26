# Entrée Underground Lake sud → nord (4:3) — projet PMDO 0.8.12

Ce dossier est un projet d'édition autonome, `entree_underground_lake_sud_nord`. Il contient le Ground `eul1_entree_underground_lake` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`), environ 2,4 × 2,4 écrans PMDO.

Le biome, Underground Lake, a été choisi par l'agent à la demande de l'utilisateur (« go carte suivante choisis ! »).

## Installer

- **Projet séparé** : copier `entree_underground_lake_sud_nord` dans `PMDO/MODS/`, activer le mod, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer la même commande sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau du lac, façon Métano (couleurs exactes du rip, sans liseré clair) | 4 × 10 ticks |
| 01 | Lueur du lac (9 couleurs exactes du rip ; les anneaux respirent) | 12 × 10 ticks |
| 02 | Scintillements Métano natifs | 4 × 10 ticks |
| 03 | Gouttes qui tombent du plafond et ronds dans l'eau (générés) | 24 × 5 ticks |
| 04 | Sol complet (sable ; les parois du brut restent dessous) | fixe |
| 05 | Sable praticable : chemin, plage, chaussée | fixe |
| 06 | Ombres au pied des parois (sable assombri du rendu) | fixe |
| 07 | Berge : rebord entre le lac et le sable | fixe |
| 08 | Parois rocheuses | fixe |
| 09 | Piliers et stalagmites | fixe |
| 10 | Profondeur : entrée sombre au nord | fixe |
| 11 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 120 ticks (2 s).

## Marqueurs et collisions

- **Marqueurs** : `entrance` est au sud, sur le chemin de sable. `donjon_seuil` est en haut de la chaussée, au pied de l'entrée sombre. **Aucun warp.**
- **Collisions** : seul le sable (ombres comprises) est praticable ; le lac, la berge, les parois, les piliers et la bouche sont bloqués. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain et gouttes** : ce sont des dessins générés à partir de la capture `Underground_Lake_shore_TDS.png`.
- **Animations** : la chute, les ronds, la respiration de la lueur et leur chronologie sont créées par nous. Ce ne sont pas des animations officielles.
- **Eau et lueur** : pixels recalculés, avec uniquement des couleurs du rip.
- **Scintillements** : pixels Métano natifs du pack, sans modification.
- **Tests** : aucun test fait dans PMDO.
