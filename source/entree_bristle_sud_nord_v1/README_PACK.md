# Entrée Bristle sud → nord — projet PMDO 0.8.12

Projet d'édition autonome `entree_bristle_sud_nord` : un Ground `ebn1_entree_bristle` (424 × 632 px, 53 × 79 cases de 8 px, `TexSize=1`).

## Installer

- **Projet séparé** : copier le dossier `entree_bristle_sud_nord` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground dans l'éditeur.
- **Dans un mod existant** : fermer PMDO, sauvegarder le mod, puis lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run` ; relancer ensuite sans `--dry-run`.

## Calques du Ground (de bas en haut)

| # | Calque | Animation |
|---|---|---|
| 00 | Torrent façon rivière de Métano (couleurs Métano exactes) | 4 × 10 ticks |
| 01 | Scintillements Métano natifs | 4 × 10 ticks |
| 02 | Sol complet (sable généré, aussi sous la roche) | fixe |
| 03 | Sable visible | fixe |
| 04 | Berge de galets | fixe |
| 05 | Rochers | fixe |
| 06 | Touffes d'herbe au vent (générées) | 12 × 10 ticks, rafale d'ouest en est |
| 07 | Falaises | fixe |
| 08 | Gorge | fixe |
| 09 | vide, `Layer=4` (Top) | pour tes éléments d'avant-plan |

La scène complète boucle en 120 ticks (2 s).

## Marqueurs et collisions

- `entrance` : arrivée au sud. `donjon_seuil` : sous la gorge, au nord. **Aucun warp.**
- Le sable est praticable ; le torrent, la berge, les rochers, les falaises et la gorge bloquent. Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Terrain et touffes** : dessins générés d'après la référence Mt. Bristle ; ce ne sont pas des pixels natifs.
- **Balancement des touffes** : cycle créé par nous.
- **Torrent** : structure et couleurs Métano, pixels recalculés.
- **Scintillements** : pixels Métano natifs.
- **Tests** : aucun test dans PMDO.
