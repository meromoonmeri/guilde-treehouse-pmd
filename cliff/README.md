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

## La texture de la roche est DESSINÉE, pas remappée

Remapper le bruit de la génération sur une rampe ocre donnait la bonne *gamme*
mais gardait un mouchetis aléatoire pixel par pixel — rien à voir avec le pixel
art de la référence. La paroi et l'herbe sont donc **entièrement redessinées** :
on ne conserve que la **silhouette** du layer `Cliffs`, et on repeint dedans.

En agrandissant `ref_cliff_edge.png`, la roche de Metano est faite de :

* des **amas arrondis** de taille moyenne dans une gamme ocre serrée
  (`ROCHE_METANO`, 9 tons relevés au compte-gouttes) ;
* des **veines mauves obliques** (`183,103,135`), à moitié fondues dans la
  roche ;
* un **contour brun foncé** d'un pixel sur tout le pourtour ;
* une **occlusion franche** sous la lèvre herbeuse.

Les amas viennent d'un bruit à trois échelles quantifié en paliers, éclairé en
comparant le champ à lui-même décalé d'un pixel — là où la plaque monte elle
prend la lumière, là où elle descend elle passe dans l'ombre. C'est ce gradient
qui donne le galbe.

Deux approches ont été essayées puis **jetées**, ne pas y revenir :

1. **Mouchetis pixel par pixel** — aucune structure lisible.
2. **Strates horizontales** — effet velours côtelé ; en rendant les lits
   irréguliers pour casser la période, la paroi virait aux veines de bois.

De même, les veines mauves tirées d'un bruit isotrope seuillé donnaient des
**confettis** ; il faut un bruit tiré dans une grille aplatie puis étirée, et
cisaillé en diagonale (facteur 1.6 — à 0.6 elles tombaient en coulures
verticales). Posées en aplat pur elles ressortaient trop : elles sont fondues
à 50 % dans la roche, seul leur cœur est en teinte pure.

Le résultat descend `Cliffs` de **46 à 20 couleurs** — de vrais aplats.

Projeter « au plus proche » ne recolore pas non plus : la palette contient des
bruns, chaque brun de la génération trouvait un brun. La paroi est donc
remappée **par luminosité** sur la rampe ocre — le modelé est conservé, la
gamme est remplacée.

## Conformité PMDO

Cadre **720 × 480**, horizon **y = 144**. **100 % des tuiles ≤ 16 couleurs,
0 pixel semi-transparent.**

| Layer | jour (cell. / coul.) | crépuscule | nuit |
|---|---|---|---|
| Sky | 5400 / 11 | 5400 / 11 | 5400 / 11 |
| Stars | — | — | 155 / 2 |
| Moon | 26 / 2 | 41 / 2 | 33 / 2 |
| Clouds | 897 / 475 | 897 / 365 | 897 / 270 |
| Base | 3780 / 37 | 3780 / 238 | 3780 / 69 |
| Cliffs | 1452 / 20 | 1452 / 20 | 1452 / 20 |
| River | 64 / 14 | 64 / 132 | 64 / 37 |
| River_Sparkles | 134 / 1 | 134 / 1 | 134 / 1 |

## Crépuscule et nuit : gammes relevées, pas inventées

Les deux ambiances sont **échantillonnées sur les photos de référence**
`IMG_4888.jpeg` (crépuscule) et `IMG_4889.png` (nuit), placées à la racine du
dépôt. Ces images sont en 3840 × 2400 et **ne sont pas des agrandissements
entiers** — un test à tous les pas de 2 à 6 laisse une différence résiduelle,
donc pas de re-décimation `[::k, ::k]` : elles sont ramenées en 720 × 480 par
un `resize` LANCZOS.

Relevé, pour chaque image :

1. **Horizon** détecté par la plus forte rupture verticale sur une colonne
   libre de tout relief : **y = 221** au crépuscule, **y = 223** de nuit.
2. **Médiane par ligne** sur la moitié droite du cadre (sans falaise), ce qui
   élimine les nuages et l'écume et ne garde que la gamme de fond.
3. Ré-échantillonnage sur le cadre du jeu (`HORIZON = 144`, mer sur 336 px)
   puis quantification en **11 aplats de ciel** et **12 de mer**.

Les gammes de mer sont stockées comme planches d'une colonne de couleur par
ligne dans `ref2/mer_crepuscule.png` et `ref2/mer_nuit.png`.

⚠️ La médiane du ciel de nuit est un **aplat** `(0, 39, 127)` sur presque toute
la hauteur : quantifier tel quel aurait supprimé tout dégradé. La rampe est
ré-étalée autour de cette valeur mesurée, de `(0, 26, 96)` à `(34, 88, 180)`.

La mer ne se contente pas de recevoir la nouvelle gamme : `construire_ocean()`
**conserve la structure de vagues du jour** et ne remplace que les couleurs,
ligne à ligne, en modulant chaque pixel par son relief local. Ce facteur est
**quantifié sur 5 crans** avant application — en continu, il créait une couleur
par pixel et faisait tomber la conformité de la mer à 95 %.

Les nuages sont teintés par moment (`"nuages"` dans `MOMENTS`) : sans cela, des
cumulus de plein midi flottaient au-dessus d'un ciel orange.

## Les GIF de rendu final

Un GIF par moment, à la racine de `cliff/` :

| Fichier | Contenu |
|---|---|
| `cliff_jour.gif` | 8 frames, 720 × 480, 330 ms |
| `cliff_crepuscule.gif` | idem |
| `cliff_nuit.gif` | idem |

Chaque frame rejoue **le même empilement de layers** : les layers fixes sont
réutilisés tels quels, `Clouds` prend sa variante de défilement `_f<i>`, les
layers à cycling prennent leur variante `_c<i>`. Le GIF boucle donc exactement
comme le ferait le moteur — il illustre le rendu, il ne le remplace pas : la
livraison reste les layers séparés.

## Reproduire

```bash
python3 tileset_pmd/construire_cliff_layers.py
```
