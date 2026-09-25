# Entrée Vapeur sud → nord — projet PMDO 0.8.12

Projet d'édition autonome `entree_vapeur_sud_nord` : un Ground `esn1_entree_vapeur_jour` (424 × 632 px, 53 × 79 cases de 8 px, `TexSize=1`).

## Installer

- **Projet séparé** : copier le dossier `entree_vapeur_sud_nord` dans `PMDO/MODS/`, l'activer puis ouvrir le Ground dans l'éditeur.
- **Dans un mod existant** : fermer PMDO, sauvegarder le mod puis lancer
  `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, et relancer sans `--dry-run`. L'installateur fusionne l'index des tilesets ; il n'écrase jamais l'index ni une ressource déjà modifiée.

## Calques du Ground (de bas en haut)

00 eau animée (12 phases × 10 ticks = 2 s, palette cycling) · 01 ombres des berges · 02 sol complet généré · 03 herbe · 04 chemin de terre · 05 buissons · 06 falaises · 07 piliers de l'entrée · 08 bouche de la grotte · 09 vide, `Layer=4` (Top), pour tes éléments d'avant-plan.

## Marqueurs et collisions

- `entrance` : arrivée au sud. `donjon_seuil` : devant la bouche, au nord. **Aucun warp n'est configuré** : il faut raccorder le seuil à ton donjon.
- Collisions de base déduites des calques : l'eau, les buissons, la roche, les piliers et la bouche bloquent. Un chemin libre de 16 × 16 px de l'arrivée au seuil a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

Le terrain est un **dessin généré** à partir d'une référence PMD Sky (Steam Cave). Ce ne sont pas des pixels natifs certifiés, et le mouvement de l'eau est une création, pas un cycle officiel. Ce pack n'a pas été testé dans PMDO : ni chargement, ni rendu GPU, ni gameplay.
