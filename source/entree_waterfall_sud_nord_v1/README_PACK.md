# Entrée Waterfall sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_waterfall_sud_nord` : un Ground `ewn1_entree_waterfall` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`, environ 2,4 × 2,4 écrans PMDO).

Réf. DA : `Waterfall_Cave_gem_TDS.png`. Exigence « même endroit, autre lieu » : les bruts décor et sol ont été générés avec la ref canonique en guide ; la roche rouge du décor est mesurée proche de celle de la ref (voir `manifest.json`, champ `canonique`).

## Installer

- **Projet séparé** : copier `entree_waterfall_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau luminescente (8 bassins) | 4 × 10 ticks |
| 01 | Sol complet | fixe |
| 02 | Sol de caverne | fixe |
| 03 | Sentier | fixe |
| 04 | Parois rocheuses | fixe |
| 05 | Stalagmites | fixe |
| 06 | Gemmes | fixe |
| 07 | Passage sombre | fixe |
| 08 | Scintillements | 24 × 5 ticks, boucle de 2 s |
| 09 | vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` au sud, sur le sentier ; `donjon_seuil` sous le passage, au nord. **Aucun warp.**
- Le sol de caverne et le sentier sont praticables. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, eau et scintillements** : dessins générés d'après la référence Waterfall Cave ; cycles créés par nous.
- **Tests** : aucun test dans PMDO. Art non approuvé.
