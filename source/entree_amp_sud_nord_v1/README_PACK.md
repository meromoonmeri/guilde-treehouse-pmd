# Entrée Amp sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_amp_sud_nord` : un Ground `ean1_entree_amp` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`, environ 2,4 × 2,4 écrans PMDO).

Réf. DA : `Amp_Plains_entrance_TD.png`. Exigence « même endroit, autre lieu » : les bruts décor, sol et touffes ont été générés avec la ref canonique en guide ; l'herbe du décor est mesurée proche de celle de la ref (voir `manifest.json`, champ `canonique`).

## Installer

- **Projet séparé** : copier `entree_amp_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Sol complet | fixe |
| 01 | Plaine herbeuse | fixe |
| 02 | Sentier | fixe |
| 03 | Parois rocheuses | fixe |
| 04 | Blocs rocheux | fixe |
| 05 | Arbres morts | fixe |
| 06 | Grotte sombre | fixe |
| 07 | Touffes d'herbe | 12 × 10 ticks, rafale d'ouest en est |
| 08 | Étincelles électriques | 24 × 5 ticks, boucle de 2 s |
| 09 | vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` au sud, sur le sentier ; `donjon_seuil` sous la grotte, au nord. **Aucun warp.**
- La plaine et le sentier sont praticables. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, touffes et étincelles** : dessins générés d'après la référence Amp Plains ; cycles créés par nous.
- **Tests** : aucun test dans PMDO. Art non approuvé.
