# Entrée Givre sud → nord — projet PMDO 0.8.12

Projet d'édition autonome `entree_givre_sud_nord` : un Ground `egn1_entree_givre` de 424 × 632 px (53 × 79 cases de 8 px, `TexSize=1`).

## Installer

- **Projet séparé** : copier le dossier `entree_givre_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground dans l'éditeur.
- **Dans un mod existant** : fermer PMDO, sauvegarder le mod, puis lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`. Relancer ensuite sans `--dry-run`.

## Calques du Ground (de bas en haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Eau glacée façon rivière de Métano | 4 phases × 10 ticks |
| 01 | Scintillements (pixels Métano recolorés) | 4 phases × 10 ticks |
| 02–10 | Sol complet, neige, sentier, gué gelé, glaçons, souche, sapins et congères, falaises de glace, bouche | fixes |
| 11 | Flocons générés (40 émetteurs décalés, chute de 64 px puis dépôt) | 48 phases × 5 ticks |
| 12 | Vide, `Layer=4` (Top) | — |

La scène complète boucle en 240 ticks (4 s).

## Marqueurs et collisions

- `entrance` : arrivée au sud. `donjon_seuil` : première case libre devant la grotte. **Aucun warp.**
- Zones praticables : neige visible, sentier et gué gelé. Un chemin libre de 16 × 16 px a été vérifié sur la grille, **à contrôler en jeu**.

## Limites

- Terrain et flocons : générés, ce ne sont pas des pixels natifs.
- Gué gelé : dessiné par script, parce que le ruisseau généré coupait le sentier.
- Eau : structure de la rivière de Métano, recalculée.
- Aucun test PMDO.
