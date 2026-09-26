# Entrée Foggy Forest — camp de base sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_foggy_forest_sud_nord`. Il contient un Ground `eff1_entree_foggy_forest` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`).

## Installer

- **Projet séparé** : copier `entree_foggy_forest_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (du bas vers le haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau de la mare, façon Métano (couleurs Métano exactes, sans liseré clair) | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet (herbe pâle) | fixe |
| 03 | Herbe du camp (praticable) | fixe |
| 04 | Chemin | fixe |
| 05 | Sous-bois (herbe sombre) | fixe |
| 06 | Buissons et fleurs | fixe |
| 07 | Rochers | fixe |
| 08 | Tentes Grodoudou | fixe |
| 09 | Arbres | fixe |
| 10 | Grotte : encadrement de pierre et bouche sombre | fixe |
| 11 | Brume générée, tramée en damier | 48 × 5 ticks |
| 12 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 240 ticks (4 s).

## Marqueurs et collisions

- `entrance` est au sud, sur le chemin. `donjon_seuil` est au nord, devant la bouche de la grotte. **Aucun warp.**
- Sont praticables l'herbe du camp et le chemin ; tentes, rochers, buissons, mare, arbres et grotte bloquent. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain et brume** : dessins générés à partir de la capture `Foggy_Forest_Base_Camp_TDS.png`. Le rendu généré est plus clair et plus laiteux que la capture : l'écart de couleur par matière va de 25 à 38 (contre 3 à 15 sur les lots précédents). Il n'a pas été corrigé, pour ne pas recolorer.
- **Brume** : la dérive, la trame et la boucle sont créées par nous ; ce n'est pas une animation officielle. La trame n'utilise que l'alpha 0/255, ce qui évite les problèmes d'alpha prémultiplié.
- **Eau** : façon Métano, pixels recalculés avec les couleurs Métano exactes. **Scintillements** : pixels Métano natifs.
- **Tests** : aucun test fait dans PMDO.
