# Entrée Waterfall Cave V3 sud → nord (4:3) — projet PMDO 0.8.12

Projet d'édition autonome `entree_waterfall_cave_v3`. Il contient un Ground `ewc3_entree_waterfall_cave` au **format 4:3 vaste** : 768 × 576 px, soit 96 × 72 cases de 8 px (`TexSize=1`).

La V3 garde les deux premiers changements de la V2 :

- les rives n'ont plus de liseré clair ;
- un couloir de sable mène jusqu'à la grotte, sans eau devant.

Elle change la façon dont la cascade s'ouvre. Au lieu d'un trou en forme de grotte, **la cascade se fend en deux sur toute sa hauteur** :

- une fissure part de la lèvre de la falaise et descend jusqu'à la grotte, puis elle s'élargit ;
- les deux moitiés du rideau s'écartent : l'eau est repoussée et se tasse sur les côtés ;
- derrière apparaissent la paroi rocheuse sèche (pixels générés) et la grotte.

## Installer

- **Projet séparé** : copier `entree_waterfall_cave_v3` dans `PMDO/MODS/`, l'activer, puis ouvrir le Ground.
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
| 09 | Paroi derrière la cascade (générée) | — | fixe | oui (cachée par le rideau fermé) |
| 10 | Arbres | — | fixe | oui |
| 11 | Entrée sombre | — | fixe | oui |
| 12 | Cascade fermée (recouvre la grotte) | fermée | 12 × 4 ticks | **oui** |
| 13 | La cascade se fend et s'écarte | ouverture | 24 × 4 ticks, une fois | non |
| 14 | Cascade ouverte : deux chutes de part et d'autre de la grotte | ouverte | 12 × 4 ticks | non |
| 15 | Écume du pied | — | fixe | oui |
| 16 | Écume, bouillons générés | — | 12 × 4 ticks | oui |
| 17 | Bouillons au pied du rideau fermé | fermée | 12 × 4 ticks | **oui** |
| 18 | Gerbe de la fissure, bouillons qui s'éteignent, gerbes aux lèvres | ouverture | 24 × 4 ticks, une fois | non |
| 19 | Embruns générés | — | 12 × 4 ticks | oui |
| 20 | Vide, `Layer=4` (Top) | — | — | oui |

## Ouvrir la cascade (script)

`Data/Script/entree_waterfall_cave_v3/ground/ewc3_entree_waterfall_cave/init.lua` contient la fonction `ouvrir_cascade()`. Elle procède en deux étapes :

1. elle masque les calques 12 et 17, affiche les calques 13 et 18, puis attend 96 frames ;
2. elle masque les calques 13 et 18, puis affiche le calque 14.

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

- **Pixels** : le terrain, la cascade, l'écume et les gerbes sont des pixels générés à partir de la capture `entrancecascade.png` (mêmes bruts que la V1). La paroi derrière la cascade vient d'un brut généré en plus : le décor de la V1 édité, sans la cascade.
- **Animations** : la fissure, l'écartement, le défilement, les émetteurs et la chronologie sont créés par nous. Ce ne sont pas des animations officielles.
- **Eau** : façon Métano, pixels recalculés avec les couleurs Métano exactes.
- **Scintillements** : pixels Métano natifs.
- **Tests** : aucun test fait dans PMDO.
