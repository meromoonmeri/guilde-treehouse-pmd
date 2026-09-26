# Entrée de la fosse du Dark Crater, sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_cratere_fosse_sud_nord`. Il contient un Ground `ecf1_entree_cratere_fosse` de 768 × 576 px (96 × 72 cases de 8 px, `TexSize=1`). Biome choisi par l'agent.

## Installer

- **Projet séparé** : copier `entree_cratere_fosse_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (du bas vers le haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Lave : cellules aux couleurs exactes du rip | 12 × 8 ticks |
| 01 | Bulles de lave (générées) | 24 × 4 ticks |
| 02 | Sol complet | fixe |
| 03 | Sol praticable | fixe |
| 04 | Bordures de roche | fixe |
| 05 | Pics noirs | fixe |
| 06 | Paroi nord | fixe |
| 07 | Bouche de la grotte | fixe |
| 08 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 96 ticks (1,6 s).

## Marqueurs et collisions

- `entrance` est au sud. `donjon_seuil` est en haut du pont de roche, devant la grotte. **Aucun warp.**
- Sont praticables le sol gris et les bordures à plus de 3 px de la lave. **À contrôler en jeu.**

## Limites

- **Terrain et bulles** : générés à partir de la capture `Dark_Crater_Pit_TDS.png`.
- **Lave** : motif et mouvement créés par nous, avec les couleurs exactes de la capture. Ce n'est pas une animation officielle.
- **Tests** : aucun test fait dans PMDO.
