# Entrée Cratère sud → nord — projet PMDO 0.8.12

Projet d'édition autonome `entree_cratere_sud_nord` : un Ground `ecn1_entree_cratere` (424 × 632 px, 53 × 79 cases de 8 px, `TexSize=1`).

## Installer

- **Projet séparé** : copier le dossier `entree_cratere_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground dans l'éditeur.
- **Dans un mod existant** : fermer PMDO, sauvegarder le mod, puis lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run` ; relancer ensuite sans `--dry-run`. L'installateur fusionne l'index des tilesets et n'écrase rien de ce qui a déjà été modifié.

## Calques du Ground (de bas en haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Lave façon rivière de Métano | 4 phases × 10 ticks |
| 01 | Éclats (pixels Métano recolorés) | 4 phases × 10 ticks |
| 02 | Sol complet (cendre générée, aussi sous la roche) | fixe |
| 03 | Bulles de lave générées | 24 phases × 5 ticks, émetteurs décalés |
| 04–07 | Cendre visible, rebords des mares, falaises, bouche du cratère | fixes |
| 08 | Braises des roches | pulsation 6 phases × 10 ticks |
| 09 | vide, `Layer=4` (Top) | pour tes éléments d'avant-plan |

La scène complète boucle en 120 ticks (2 s).

## Marqueurs et collisions

- `entrance` : arrivée au sud. `donjon_seuil` : devant la bouche, au nord. **Aucun warp.**
- Seule la cendre visible est praticable ; la lave, la roche, les rebords et la bouche bloquent. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain** : dessin généré à partir de la référence PMD Sky Dark Crater. Ce ne sont pas des pixels natifs.
- **Lave** : structure et cadence de la rivière Métano, recalculées sur nos mares.
- **Bulles et pulsation des braises** : créées par nous, ce ne sont pas des animations officielles.
- **Tests** : aucun test dans PMDO.
