# Entrée Grotte de cristal sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_crystal_cave_sud_nord`. Il contient un Ground `ecc1_entree_crystal_cave` de 768 × 576 px (96 × 72 cases de 8 px, `TexSize=1`). Référence : la salle du joyau de Waterfall Cave (biome choisi par l'agent).

## Installer

- **Projet séparé** : copier `entree_crystal_cave_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (du bas vers le haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Bassins, façon Métano, couleurs exactes de la capture, sans liseré clair | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet | fixe |
| 03 | Sol de galets (praticable) | fixe |
| 04 | Vide ardoise | fixe |
| 05 | Fond marron | fixe |
| 06 | Stalactites (paroi du fond) | fixe |
| 07 | Rochers | fixe |
| 08 | Racines | fixe |
| 09 | Cristaux et joyau | fixe |
| 10 | Tunnel | fixe |
| 11 | Éclats générés sur les cristaux | 48 × 5 ticks |
| 12 | Vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` est au sud. `donjon_seuil` est en haut du sol de galets, sous le joyau et le tunnel. Le tunnel est sur la paroi du fond, derrière les rochers : **le raccord reste à scripter. Aucun warp.**
- Le sol de galets est praticable ; les petits cristaux posés dessus se traversent. **À contrôler en jeu.**

## Limites

- Terrain et éclats générés à partir de la capture. La chronologie des éclats est créée par nous ; ce n'est pas une animation officielle.
- Aucun test fait dans PMDO.
