# Cliff — layout de la référence, tileset de Metano Town

Zone `Cliff` en **12 layers modulaires**, méthode Halcyon
(`tileset_pmd/AUDIT_METHODE_LAYERS_HALCYON.md`).

Quatre règles fixent le résultat :

1. **Layout de la référence** — plateau herbeux à gauche, paroi à pic, océan à
   droite, horizon haut.
2. **La falaise touche les bords** — elle mord le bord gauche et court sur tout
   le bord bas ; aucun liseré de ciel ne peut apparaître derrière elle. Elle ne
   couvre pas toute la largeur : la mer reste visible à droite.
3. **Texture et couleurs de `IMG_4892.png`** — roche en grès finement moucheté
   par strates horizontales avec veines mauves, herbe olive clair mouchetée de
   touffes.
4. **Le ciel est un overlay, les nuages défilent en wrap loop parfaite.**

## La référence `IMG_4892.png`

La capture est un **upscale ×3 exact** — vérifié en re-décimant l'image, la
reconstruction est identique au pixel près. On en récupère donc les **pixels
natifs 504 × 384** (`ref2/ref_metano_scene.png`), ce qui donne la palette
authentique sans aucune approximation. Trois patches en sont découpés et
servent de référence directe au générateur d'image :

| Fichier | Contenu |
|---|---|
| `ref2/ref_rock_texture.png` | grès moucheté, strates, veines mauves |
| `ref2/ref_grass_texture.png` | turf olive moucheté de touffes |
| `ref2/ref_cliff_edge.png` | bord herbe/roche, liseré de sable, ressac |

Palettes mesurées : ciel **4 couleurs**, mer **19**, roche **55**, herbe **48**.
Horizon natif à `y = 117`, soit `y = 144` dans notre cadre.

## Structure des layers

```
Metano Town  : Base(0) > Cliffs(0) > River(0) > Objects Under(0) >
               Objects(0) > Objects Over(0) > Fringe(4)

Cliff (nous) : Sky(0) > Stars(0) > Moon(0) > Clouds(0) >
               Base(0) > Cliffs(0) > River(0) > River_Sparkles(0) >
               Objects_Under(0) > Objects(0) > Objects_Over(0) > Fringe(4)
```

| Layer | `Layer` | Rôle | Équivalent Metano |
|---|---|---|---|
| `Sky` | 0 | dégradé en bandes franches, plein cadre | `Background` |
| `Stars` | 0 | étoiles, **nuit seulement** | — |
| `Moon` | 0 | soleil le jour, lune la nuit | — |
| `Clouds` | 0 | **8 frames en boucle** | — |
| `Base` | 0 | l'océan | `Metano_Town_Base` |
| `Cliffs` | 0 | la paroi rocheuse | `Metano_Town_Cliffs` |
| `River` | 0 | ressac au pied et au flanc | `..._River_Animation_*` |
| `River_Sparkles` | 0 | scintillements | `..._River_Sparkles` |
| `Objects_Under` | 0 | liseré de sable sous l'herbe | `Objects Under` |
| `Objects` | 0 | le plateau herbeux | `Objects` |
| `Objects_Over` | 0 | affleurements de roche | `Objects Over` |
| **`Fringe`** | **4** | **crête, DEVANT le joueur** | `Metano_Town_Fringe` |

## Nuages : wrap loop parfaite

`bande_nuages()` compose une bande de **largeur exactement `CADRE_W`**. Tout
nuage qui déborde du bord droit est **redessiné à `x - CADRE_W`** : la bande se
raccorde donc à elle-même par construction, et un simple `np.roll` horizontal
produit un défilement infini sans couture.

8 frames, pas de **90 px** (`720 / 8`). Vérifié :

```
f0→f1 … f7→f0 : diff = 0 pixel   ⇒ WRAP LOOP PARFAITE
```

Fichiers `layers/Cliff_Clouds_<moment>_f0..f7.png`, à jouer en boucle sur leur
propre layer, par-dessus `Sky` et sous `Base`.

## Colorimétrie

| Élément | Couleur | Source |
|---|---|---|
| Herbe | `(215,223,87)`, `(231,239,103)` olive clair | `IMG_4892` |
| Herbe, ombre | `(167,191,47)`, `(55,103,31)` | `IMG_4892` |
| Roche | `(207,151,95)`, `(167,119,71)`, `(151,95,55)` | `IMG_4892` |
| Veines de roche | `(159,95,79)`, `(175,103,95)` mauve | `IMG_4892` |
| Ciel zénith | `(111,167,255)` | `IMG_4892` |
| Écume | `(199,239,247)`, `(223,247,255)` | `IMG_4892` |

Deux pièges traités explicitement dans le code :

* **l'herbe de Treasure Town est olive, pas verte** — `virer_herbe_metano()`
  force tout pixel à dominante verte vers l'un des cinq tons mesurés ;
* **séparer herbe et roche par « vert > bleu » ne marche pas** — la roche ocre
  `(167,119,71)` a elle aussi G nettement au-dessus de B. Ce qui les distingue,
  c'est que la roche est *chaude* : son rouge domine largement son vert, alors
  que l'herbe olive a R et G proches. D'où le test
  `G >= R - 20 and G > B + 40`.

## Conformité PMDO

Cadre **720 × 480**, horizon **y = 144**. **100 % des tuiles ≤ 16 couleurs sur
tous les layers, 0 pixel semi-transparent.**

| Layer | jour (cellules / couleurs) | nuit |
|---|---|---|
| Sky | 5400 / 11 | 5400 / 11 |
| Stars | — | 155 / 2 |
| Moon | 26 / 2 | 33 / 2 |
| Clouds | 897 / 475 | 897 / 270 |
| Base | 3780 / 37 | 3780 / 37 |
| Cliffs | 556 / 54 | 556 / 52 |
| River | 84 / 19 | 84 / 19 |
| River_Sparkles | 124 / 1 | 124 / 1 |
| Objects_Under | 165 / 32 | 172 / 34 |
| Objects | 1603 / 5 | 1629 / 7 |
| Objects_Over | 15 / 3 | 15 / 3 |
| Fringe | 160 / 4 | 165 / 5 |

## Fichiers

* `layers/Cliff_<Layer>_<jour|nuit>.png` — les calques, cadre 720 × 480,
  superposables au pixel près ;
* `layers/Cliff_Clouds_<moment>_f0..f7.png` — la boucle de nuages ;
* `layers/Cliff_layers.json` — manifeste : ordre, `Layer`, métriques, et le
  bloc `nuages` (frames, sens du wrap, pas en px) ;
* `cliff_<jour|nuit>.png` — aperçu composé ;
* `ref2/` — la référence en pixels natifs et les patches de texture.

## Reproduire

```bash
python3 tileset_pmd/construire_cliff_layers.py
```
