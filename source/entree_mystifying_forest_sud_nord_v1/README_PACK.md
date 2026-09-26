# Entrée Mystifying Forest sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_mystifying_forest_sud_nord`. Il contient un Ground `emf1_entree_mystifying_forest` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`), environ 2,4 × 2,4 écrans PMDO.

Biome choisi par l'agent (Mystifying Forest) : **à confirmer**.

## Installer

- **Projet séparé** : copier `entree_mystifying_forest_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau de la mare, façon Métano (couleurs Métano exactes, sans liseré clair) | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet (herbe) | fixe |
| 03 | Herbe de la clairière (praticable) | fixe |
| 04 | Chemin | fixe |
| 05 | Herbes hautes et sous-bois | fixe |
| 06 | Rochers | fixe |
| 07 | Arbres : houppiers, troncs, racines | fixe |
| 08 | Profondeur : ouverture sombre au nord | fixe |
| 09 | Feuilles qui tombent (générées) | 48 × 5 ticks |
| 10 | Lucioles (générées) | 48 × 5 ticks |
| 11 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 240 ticks (4 s).

## Marqueurs et collisions

- `entrance` est au sud, sur le chemin. `donjon_seuil` est au bout nord du chemin, au pied de l'ouverture sombre entre les grands arbres. **Aucun warp.**
- Sont praticables l'herbe de la clairière et le chemin. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, feuilles et lucioles** : dessins générés à partir de la capture `Mystifying_Forest_entrance_TDS.png`. Les trajectoires, les boucles et la chronologie sont créées par nous ; ce ne sont pas des animations officielles.
- **Eau** : façon Métano, pixels recalculés avec les couleurs Métano exactes.
- **Scintillements** : seuls pixels Métano natifs du pack.
- **Tests** : aucun test fait dans PMDO.
