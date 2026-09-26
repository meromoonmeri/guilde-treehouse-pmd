# Entrée Dark Crater, fosse de lave, sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_dark_crater_pit_sud_nord`. Il contient un Ground `edp1_entree_dark_crater_pit` de 768 × 576 px (96 × 72 cases de 8 px).

## Installer

- **Projet séparé** : copier `entree_dark_crater_pit_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (du bas vers le haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Lave : motif généré, 11 couleurs exactes du rip, cycle de palette | 12 × 8 ticks |
| 01 | Bulles de lave générées | 24 × 4 ticks |
| 02 | Sol complet (pierre) | fixe |
| 03 | Plateau et chemins de pierre (praticables) | fixe |
| 04 | Rebords rocheux | fixe |
| 05 | Grand mur noir | fixe |
| 06 | Aiguilles et débris dans la lave | fixe |
| 07 | Grotte (bouche sombre) | fixe |
| 08 | Vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` est au sud. `donjon_seuil` est en haut du pont de pierre, devant la grotte. **Aucun warp.**
- Seule la pierre grise est praticable. **À contrôler en jeu.**

## Limites

- Le terrain, la lave et les bulles sont générés à partir de la capture. Le cycle de palette, la chronologie et le placement des bulles sont créés par nous ; ce ne sont pas des animations officielles.
- Aucun test fait dans PMDO.
