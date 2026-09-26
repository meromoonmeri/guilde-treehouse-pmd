# Entrée Cascade sud → nord (4:3, pixels natifs) — projet PMDO 0.8.12

Projet d'édition autonome `entree_cascade_sud_nord` : un Ground `ecn1_entree_cascade` au **format 4:3 vaste** (768 × 576 px, 96 × 72 cases de 8 px, `TexSize=1`), composé **uniquement de pixels canoniques** copiés tels quels.

## Installer

- **Projet séparé** : copier `entree_cascade_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | Origine native | Animation |
|---|---|---|---|
| 00 | Fond vide | aplat du vide de Waterfall Cave (ledge) | fixe |
| 01 | Sol de galets | couloir de Waterfall Cave (ledge), quilting à phase 24 px | fixe |
| 02 | Eau profonde | mailles de Waterfall Cave (gem), quilting | fixe |
| 03 | Plafond et parois nord | pièces de Waterfall Cave (ledge) | fixe |
| 04 | Murs latéraux | parois entières de Waterfall Cave (ledge) | fixe |
| 05 | Cascade | `cascade_frame_1..4` Métano, corps 48 × 96 posé deux fois | 4 × 10 ticks |
| 06 | Rochers, pierres, cristaux | paires de rochers et cristaux (gem), pierres (ledge) | fixe |
| 07 | Scintillements | tuiles Métano natives | 4 × 10 ticks |
| 08 | vide, `Layer=4` (Top) | — | — |

## Marqueurs et collisions

- `entrance` au sud, au bas de la chaussée ; `donjon_seuil` sur la plateforme au pied de la cascade. **Aucun warp.**
- Praticable = sol visible. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- L'eau profonde est **statique** (aucun cycle natif récupéré) ; seuls la cascade et les scintillements sont animés.
- La cadence de la cascade (10 ticks) est **proposée**, pas prouvée par la map Métano.
- Aucun test dans PMDO.
