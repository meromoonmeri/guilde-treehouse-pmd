# Entrée Waterfall Cave V2 sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_waterfall_cave_v2`. Il contient un Ground `ewc2_entree_waterfall_cave` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`).

La V2 reprend la V1 avec trois changements :

- les rives n'ont plus de liseré clair ;
- un couloir de sable mène jusqu'à la grotte, sans eau devant ;
- la cascade marche en deux temps (fermée, puis elle se fend).

## Installer

- **Projet séparé** : copier `entree_waterfall_cave_v2` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
- **Dans un mod existant** : lancer `python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run`, puis relancer sans `--dry-run`.

## Calques (bas → haut)

| # | Calque | État | Animation | Visible au chargement |
|---|---|---|---|---|
| 00 | Eau des bassins, façon Métano, sans liseré de rive | — | 4 × 10 ticks | oui |
| 01 | Scintillements Métano natifs | — | 4 × 10 ticks | oui |
| 02 | Sol complet (sable) | — | fixe | oui |
| 03 | Sable praticable (couloir compris) | — | fixe | oui |
| 04 | Cailloux | — | fixe | oui |
| 05 | Touffes | — | fixe | oui |
| 06 | Plateaux | — | fixe | oui |
| 07 | Berge | — | fixe | oui |
| 08 | Falaises | — | fixe | oui |
| 09 | Arbres | — | fixe | oui |
| 10 | Entrée sombre | — | fixe | oui |
| 11 | Cascade fermée (recouvre la grotte) | fermée | 12 × 4 ticks | **oui** |
| 12 | Cascade qui se fend | ouverture | 24 × 4 ticks, une fois | non |
| 13 | Cascade ouverte (contourne la grotte) | ouverte | 12 × 4 ticks | non |
| 14 | Écume du pied | — | fixe | oui |
| 15 | Écume, bouillons générés | — | 12 × 4 ticks | oui |
| 16 | Bouillons au pied du rideau fermé | fermée | 12 × 4 ticks | **oui** |
| 17 | Bouillons qui s'éteignent et gerbes de la fente | ouverture | 24 × 4 ticks, une fois | non |
| 18 | Embruns générés | — | 12 × 4 ticks | oui |
| 19 | Vide, `Layer=4` (Top) | — | — | oui |

## Ouvrir la cascade (script)

`Data/Script/entree_waterfall_cave_v2/ground/ewc2_entree_waterfall_cave/init.lua` contient la fonction `ouvrir_cascade()`. Elle procède en deux étapes :

1. elle masque les calques 11 et 16, affiche les calques 12 et 17, puis attend 96 frames ;
2. elle masque les calques 12 et 17, puis affiche le calque 13.

Elle s'appelle depuis une coroutine de cinématique.

**Non testé dans PMDO.** Deux points restent à vérifier :

- l'accès Lua à `Layers[i].Visible` ;
- le calage de la phase 0 du calque d'ouverture sur l'horloge d'animation du moteur. Pour un défilement continu, il faut démarrer sur un tick multiple de 48.

## Marqueurs et collisions

- `entrance` est au sud, sur la plage.
- `donjon_seuil` est en haut du couloir, au pied de la grotte.
- **Aucun warp.**
- Les collisions sont fixes : le couloir reste praticable même quand la cascade est fermée. Au script de bloquer l'entrée tant que la cascade n'est pas ouverte.
- Un chemin de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Limites

- **Pixels** : le terrain, la cascade, l'écume et les gerbes sont des pixels générés à partir de la capture `entrancecascade.png` (mêmes bruts que la V1).
- **Animations** : la fente, le défilement, les émetteurs et la chronologie sont créés par nous. Ce ne sont pas des animations officielles.
- **Eau** : façon Métano, pixels recalculés avec les couleurs Métano exactes.
- **Scintillements** : pixels Métano natifs.
- **Tests** : aucun test fait dans PMDO.
