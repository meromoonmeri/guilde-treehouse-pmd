# Cliff — layout de la référence, tileset de Metano Town

Zone `Cliff` en layers modulaires, méthode Halcyon
(`tileset_pmd/AUDIT_METHODE_LAYERS_HALCYON.md`).

## Principes

1. **La falaise est sur un layer unique.** `Cliffs` porte le plateau herbeux
   *et* la paroi rocheuse ensemble. Elle n'est plus redécoupée en
   `Objects` / `Objects_Over` / `Fringe`.
2. **Le plateau est pavé avec une vraie cellule 8 × 8 de Metano Town.**
   `ref2/tile_grass8.png` est prélevée telle quelle dans la référence
   (6 couleurs : `(215,223,87)` … `(239,239,127)`) et répétée sur toute la
   surface — le motif se raccorde donc exactement comme en jeu, sans bande,
   sans couture, sans trace de chemin.
3. **La paroi porte la couleur mesurée sur la falaise de la référence.**
4. **Le ciel et la mer sont animés par cycling de palette**, la technique
   réelle de PMD.
5. **Les nuages défilent en wrap loop parfaite** sur leur propre layer.

## Animation : la méthode réelle de PMD

Point vérifié auprès de la communauté qui a rippé les tilesets d'*Explorers of
Sky* : le jeu **n'anime pas l'eau en changeant les tuiles**.

> « Every dungeon tile in the games are still sprites — they don't ever change
> graphics in order to animate. Water has the illusion of animating because its
> palette row changes color. » — SilverDeoxys563, rip des tilesets EoS
> ([r/MysteryDungeon](https://www.reddit.com/r/MysteryDungeon/comments/5c63op/ive_started_the_longdelayed_journey_of_ripping/))

La cadence est constante et mesurable en frames : **~20 frames à 60 fps** pour
l'eau de Beach Cave. TCRF note la même chose pour les fonds d'écran d'EoS, qui
ajoutent « a palette animation for the water as well as dithering between water
color shades »
([TCRF](https://tcrf.net/Pok%C3%A9mon_Mystery_Dungeon:_Explorers_of_Time_&_Darkness/Unused_Graphics)).

C'est donc exactement ce qui est implémenté, par `cycler_palette()` :

* on ordonne les couleurs du calque par luminosité — c'est la *rampe* ;
* à chaque frame, tout pixel portant la couleur `i` prend la couleur `i+1` ;
* **aucun pixel ne se déplace**, seule sa couleur change.

Vérifié sur la sortie :

| Layer | tuiles figées | pixels recolorés / pas | boucle fermée |
|---|---|---|---|
| `Base` (mer) | oui | 241 830 / 241 920 | oui |
| `Sky` | oui | 345 600 / 345 600 | oui |
| `River` | oui | 1 556 / 1 632 | oui |

| Layer | Type | Frames | Cadence |
|---|---|---|---|
| `Base`, `River` | `palette_cycling` | 8 | 20 frames (60 fps) |
| `Sky` | `palette_cycling` | 8 | 30 frames (60 fps) |
| `Clouds` | `defilement` | 8 | pas de 90 px |

Fichiers : `Cliff_<Layer>_<moment>_c0..c7.png` pour le cycling,
`Cliff_Clouds_<moment>_f0..f7.png` pour le défilement.

### Nuages : wrap loop parfaite

`bande_nuages()` compose une bande de **largeur exactement `CADRE_W`**. Tout
nuage débordant à droite est **redessiné à `x - CADRE_W`** : la bande se
raccorde à elle-même par construction, et un `np.roll` produit un défilement
infini sans couture. Vérifié : `f0→f1 … f7→f0`, **diff = 0 pixel**.

## Structure des layers

| Layer | `Layer` | Rôle | Animation |
|---|---|---|---|
| `Sky` | 0 | dégradé en bandes franches, plein cadre | cycling |
| `Stars` | 0 | étoiles, **nuit seulement** | — |
| `Moon` | 0 | soleil le jour, lune la nuit | — |
| `Clouds` | 0 | nuages | défilement |
| `Base` | 0 | l'océan | cycling |
| **`Cliffs`** | **0** | **la falaise entière : plateau + paroi** | — |
| `River` | 0 | ressac au pied et au flanc | cycling |
| `River_Sparkles` | 0 | scintillements | — |

## Colorimétrie

La référence `IMG_4892.png` est un **upscale ×3 exact** — vérifié en
re-décimant l'image. On travaille donc sur ses **pixels natifs 504 × 384**
(`ref2/ref_metano_scene.png`), sans aucune approximation.

| Élément | Source | Couleurs |
|---|---|---|
| Herbe du plateau | `ref2/tile_grass8.png`, cellule 8 × 8 | 6 |
| Paroi rocheuse | `ref2/ref_paroi.png`, rampe ocre | 50 mesurées |
| Ciel | bandes relevées une par une | 11 |
| Mer | `ref2/gen_sea.png` | 37 |

### Trois pièges rencontrés

* **Séparer herbe et roche par « vert > bleu » ne marche pas.** La roche ocre
  `(167,119,71)` a elle aussi G bien au-dessus de B. Ce qui les distingue,
  c'est que la roche est *chaude* : R domine largement G, alors que l'olive a
  R et G proches. D'où `G >= R - 20 and G > B + 40`.
* **L'ordre des traitements compte.** Projeter d'abord sur la palette globale
  mélangeait les teintes d'herbe et de roche, et la séparation reclassait
  ensuite des pixels de paroi en herbe — mouchetis jaune dans la falaise. On
  habille donc le terrain **avant** toute projection globale.
* **`ref_paroi.png` est un rectangle découpé dans la scène** : il contient
  aussi du ciel et de la mer. Garder ces bleus dans la rampe injectait un
  mouchetis bleu dans la falaise. La rampe est filtrée sur les tons chauds
  (`R > B + 25`).

Projeter « au plus proche » ne recolore pas non plus : la palette contient des
bruns, chaque brun de la génération trouvait un brun. La paroi est donc
remappée **par luminosité** sur la rampe ocre — le modelé est conservé, la
gamme est remplacée.

## Conformité PMDO

Cadre **720 × 480**, horizon **y = 144**. **100 % des tuiles ≤ 16 couleurs,
0 pixel semi-transparent.**

| Layer | jour (cellules / couleurs) | nuit |
|---|---|---|
| Sky | 5400 / 11 | 5400 / 11 |
| Stars | — | 155 / 2 |
| Moon | 26 / 2 | 33 / 2 |
| Clouds | 897 / 475 | 897 / 270 |
| Base | 3780 / 37 | 3780 / 37 |
| Cliffs | 1452 / 46 | 1452 / 46 |
| River | 64 / 14 | 64 / 14 |
| River_Sparkles | 134 / 1 | 134 / 1 |

## Reproduire

```bash
python3 tileset_pmd/construire_cliff_layers.py
```
