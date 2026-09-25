# Entrée Vapeur sud → nord V2 — projet PMDO 0.8.12

Projet d'édition autonome `entree_vapeur_sud_nord_v2` : un Ground `esn2_entree_vapeur_jour` (424 × 632 px, 53 × 79 cases de 8 px, `TexSize=1`). La V1 (`entree_vapeur_sud_nord`) reste intacte et peut coexister avec ce projet.

## Installer

- **Projet séparé** : copier le dossier `entree_vapeur_sud_nord_v2` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground dans l'éditeur.
- **Dans un mod existant** : fermer PMDO, sauvegarder le mod, puis lancer
  `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, et relancer sans `--dry-run`. L'installateur fusionne l'index des tilesets ; il n'écrase jamais l'index ni une ressource déjà modifiée.

## Calques du Ground (de bas en haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau façon rivière de Métano | 4 phases × 10 ticks, comme la rivière Métano |
| 01 | Scintillements (pixels Métano recolorés) | 4 phases × 10 ticks |
| 02 | Bulles de marais générées | 24 phases × 5 ticks (2 s), 9 émetteurs décalés |
| 03–09 | Sol complet, herbe, chemin, buissons, falaises, piliers, bouche | fixes (terrain V1) |
| 10 | vide, `Layer=4` (Top) | pour tes éléments d'avant-plan |

La scène complète boucle en 120 ticks (2 s à 60 i/s).

## Marqueurs et collisions

- `entrance` : arrivée au sud. `donjon_seuil` : devant la bouche, au nord. **Aucun warp n'est configuré.**
- Les collisions de base sont identiques à la V1 : l'eau, les buissons, la roche, les piliers et la bouche bloquent. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Eau** : c'est la structure et la cadence de la rivière Métano (Halcyon), recalculées sur nos bassins, avec des couleurs choisies selon les rôles Métano. Ce ne sont pas des tuiles Métano natives.
- **Bulles** : dessin généré, chronologie créée par nous. Ce n'est pas une animation officielle.
- **Terrain** : dessin généré à partir de la référence Steam Cave.
- **Tests** : aucun test dans PMDO (chargement, GPU, gameplay).
