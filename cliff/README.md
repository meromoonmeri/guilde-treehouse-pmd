# Cliff — layout de la référence, tileset de Metano Town

Zone `Cliff` construite en **12 layers modulaires**, selon la méthode Halcyon
auditée dans `tileset_pmd/AUDIT_METHODE_LAYERS_HALCYON.md`.

Deux règles fixent le résultat :

1. **Le layout est celui de la référence.** `IMG_4889.png` / `IMG_4890.png`
   sont la planche ripée du *Pelipper Post Office* : plateau herbeux à gauche,
   paroi qui tombe à pic, océan à droite, horizon haut. Composition reprise
   telle quelle.
2. **Le ciel et l'océan ne sont pas générés.** Ils sont découpés directement
   dans la planche officielle, en **pixels natifs 1×**, sans passer par le
   pipeline de réduction. Seule la falaise est une génération, restylée sur le
   tileset de Metano Town (= Treasure Town).

## Sources

| Fichier | Origine | Taille |
|---|---|---|
| `ref/ref_sky.png` | découpe officielle | 720 × 208 |
| `ref/ref_ocean_deep_1..5.png` | découpe officielle | 48 × 128 |
| `ref/ref_ocean_shallow_1..9.png` | découpe officielle | 48 × 168 |
| `ref/ref_scene_land.png` | découpe officielle, référence de layout | 540 × 470 |
| `ref/gen_cliff_metano.png` | génération restylée Metano | falaise nue |
| `ref/gen_sky_objects.png` | génération | soleil, lune |
| `reference_metano_*.png` | tilesets extraits de `Palikadude/Halcyon` | palette |

Le ciel officiel est séparé en deux par `separer_ciel()` : le dégradé pur va
dans `Sky`, les nuages dans `Clouds`. La version de nuit rejoue **la structure
exacte** du dégradé ripé (mêmes bandes, mêmes hauteurs de transition) en
gamme nocturne.

L'océan est pavé par `construire_ocean()` avec les tuiles officielles : la
bande `deep` (14 couleurs) à l'horizon, puis le `shallow` (4 couleurs) pour le
large — c'est la dégression de la référence.

## Structure des layers

Relevée sur `metano_town.rsground` puis reprise :

```
Metano Town  : Base(0) > Cliffs(0) > River(0) > Objects Under(0) >
               Objects(0) > Objects Over(0) > Fringe(4)

Cliff (nous) : Sky(0) > Stars(0) > Moon(0) > Clouds(0) >
               Base(0) > Cliffs(0) > River(0) > River_Sparkles(0) >
               Objects_Under(0) > Objects(0) > Objects_Over(0) > Fringe(4)
```

| Layer | `Layer` | Rôle | Équivalent Metano |
|---|---|---|---|
| `Sky` | 0 | dégradé officiel, seul calque plein cadre | `Background` |
| `Stars` | 0 | étoiles, **nuit seulement** | — |
| `Moon` | 0 | soleil le jour, lune la nuit | — |
| `Clouds` | 0 | nuages du ciel officiel | — |
| `Base` | 0 | l'océan, tuiles officielles | `Metano_Town_Base` |
| `Cliffs` | 0 | la paroi rocheuse | `Metano_Town_Cliffs` |
| `River` | 0 | ressac au pied et au flanc de la roche | `..._River_Animation_*` |
| `River_Sparkles` | 0 | scintillements sur l'eau | `..._River_Sparkles` |
| `Objects_Under` | 0 | liseré sombre sous l'herbe | `Objects Under` |
| `Objects` | 0 | le plateau herbeux | `Objects` |
| `Objects_Over` | 0 | affleurements de roche sur l'herbe | `Objects Over` |
| **`Fringe`** | **4** | **crête du plateau, DEVANT le joueur** | `Metano_Town_Fringe` |

`River` est séparé de `Base` pour la raison même qui pousse Metano à le faire :
on pourra l'animer en 4 frames sans toucher ni à la mer ni à la falaise.

## Colorimétrie

| Élément | Couleur | Source |
|---|---|---|
| Herbe | `(200, 216, 80)` jaune-olive | `Metano_Town_Cliffs.tile` |
| Roche | `(191, 131, 111)` ocre-sable | `Metano_Town_Cliffs.tile` |
| Ciel zénith (jour) | `(16, 128, 248)` | planche officielle |
| Océan large | 4 couleurs | `ref_ocean_shallow_*` |
| Océan horizon | 14 couleurs | `ref_ocean_deep_*` |

L'herbe de Treasure Town **n'est pas verte, elle est olive**. Projeter sur la
palette complète ne suffit pas — elle contient aussi les verts sombres du
feuillage. `virer_herbe_metano()` force donc tout pixel à dominante verte vers
l'un des quatre tons d'herbe réellement mesurés dans le tileset.

## Conformité PMDO

Cadre **720 × 480**, horizon à **y = 208**. **100 % des tuiles à ≤ 16 couleurs
sur les 12 layers, 0 pixel semi-transparent.**

| Layer | jour (cellules / couleurs) | nuit |
|---|---|---|
| Sky | 5400 / 5 | 5400 / 5 |
| Stars | — | 161 / 2 |
| Moon | 127 / 6 | 175 / 6 |
| Clouds | 898 / 4 | 898 / 4 |
| Base | 3060 / 22 | 3060 / 22 |
| Cliffs | 818 / 55 | 999 / 70 |
| River | 108 / 14 | 108 / 15 |
| River_Sparkles | 119 / 1 | 119 / 1 |
| Objects_Under | 207 / 46 | 122 / 53 |
| Objects | 2317 / 19 | 1961 / 4 |
| Objects_Over | 31 / 7 | 34 / 9 |
| Fringe | 221 / 12 | 151 / 4 |

## Fichiers

* `layers/Cliff_<Layer>_<jour|nuit>.png` — les calques, cadre 720 × 480,
  même offset, superposables au pixel près ;
* `layers/Cliff_layers.json` — manifeste : ordre, champ `Layer`, métriques,
  liste des sources officielles utilisées ;
* `cliff_<jour|nuit>.png` — aperçu composé ;
* `ref/` — les découpes officielles et les générations restylées.

## Reproduire

```bash
python3 tileset_pmd/construire_cliff_layers.py
```
