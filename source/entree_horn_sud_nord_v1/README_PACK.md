# Entrée Horn sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_horn_sud_nord` : un Ground `ehn1_entree_horn` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`, environ 2,4 × 2,4 écrans PMDO).

Réf. DA : `Mt_Horn_entrance_Sky.png`. Exigence « même endroit, autre lieu » : les bruts décor et sol ont été générés avec la ref canonique en guide ; le sable du décor est mesuré proche de celui de la ref (voir `manifest.json`, champ `canonique`).

## Installer

- **Projet séparé** : copier `entree_horn_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Sol complet | fixe |
| 01 | Cour de sable | fixe |
| 02 | Sentier | fixe |
| 03 | Parois rocheuses | fixe |
| 04 | Blocs rocheux | fixe |
| 05 | Buissons secs | fixe |
| 06 | Grotte sombre | fixe |
| 07 | Éboulis | 24 × 5 ticks, boucle de 2 s |
| 08 | Poussières | 24 × 5 ticks, boucle de 2 s |
| 09 | vide, `Layer=4` (Top) | — |

## Marqueurs et collisions

- `entrance` au sud, sur le sentier ; `donjon_seuil` sous la grotte, au nord. **Aucun warp.**
- La cour et le sentier sont praticables. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain, éboulis et poussières** : dessins générés d'après la référence Mt Horn ; cycles créés par nous.
- **Tests** : aucun test dans PMDO. Art non approuvé.
