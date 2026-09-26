# Entrée Foggy Forest sans tentes, sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_foggy_forest_sans_tentes`. Il contient un Ground `eff2_entree_foggy_forest_sans_tentes` de 768 × 576 px (96 × 72 cases de 8 px). C'est une variante d'EFF1, sans tentes et avec les arbres en trois calques.

## Installer

- **Projet séparé** : copier `entree_foggy_forest_sans_tentes` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (du bas vers le haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau de la mare, façon Métano (couleurs Métano exactes, sans liseré clair) | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet | fixe |
| 03 | Herbe de la clairière (praticable) | fixe |
| 04 | Chemin | fixe |
| 05 | Sous-bois | fixe |
| 06 | Buissons et fleurs | fixe |
| 07 | Rochers | fixe |
| 08 | Ombres portées des arbres | fixe |
| 09 | Troncs et racines | fixe |
| 10 | Houppiers | fixe |
| 11 | Grotte | fixe |
| 12 | Brume générée, tramée en damier | 48 × 5 ticks |
| 13 | Vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` est au sud. `donjon_seuil` est devant la grotte. **Aucun warp.**
- L'herbe et le chemin sont praticables, y compris l'ancienne place des tentes. **À contrôler en jeu.**

## Limites

- Les pixels sont générés à partir de la capture. Ils sont plus laiteux que la capture : écart de 25 à 38 par matière.
- Les calques des arbres sont un découpage des plans visibles. Il n'y a pas de faces cachées : sous un houppier retiré, on voit le sol, pas un tronc complet.
- Aucun test fait dans PMDO.
