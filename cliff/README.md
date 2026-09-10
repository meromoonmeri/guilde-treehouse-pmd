# Cliff — zone en layers modulables, structure et colorimétrie Metano Town

Une falaise maritime construite **exactement selon la méthode de Halcyon**
auditée dans `tileset_pmd/AUDIT_METHODE_LAYERS_HALCYON.md`, et calée sur la
colorimétrie réelle de Metano Town — qui partage ses tilesets avec Treasure
Town.

## Structure des layers

Relevée sur `metano_town.rsground` puis reprise telle quelle :

```
Metano Town  : Base(0) > Cliffs(0) > River(0) > Objects Under(0) >
               Objects(0) > Objects Over(0) > Fringe(4)

Cliff (nous) : Sky(0) > Stars(0) > Moon(0) > Clouds(0) >
               Base(0) > Cliffs(0) > River(0) > River_Sparkles(0) >
               Objects_Under(0) > Objects(0) > Objects_Over(0) > Fringe(4)
```

| Layer | `Layer` | Rôle | Équivalent Metano |
|---|---|---|---|
| `Sky` | 0 | dégradé de ciel, seul calque plein cadre | `Background` |
| `Stars` | 0 | étoiles et scintillements, **nuit seulement** | — |
| `Moon` | 0 | soleil le jour, lune la nuit | — |
| `Clouds` | 0 | nuages | — |
| `Base` | 0 | la mer : le terrain de fond de la zone | `Metano_Town_Base` |
| `Cliffs` | 0 | la falaise et son plateau | `Metano_Town_Cliffs` |
| `River` | 0 | ressac au pied de la roche | `Metano_Town_River_Animation_*` |
| `River_Sparkles` | 0 | scintillements sur l'eau | `Metano_Town_River_Sparkles` |
| `Objects_Under` | 0 | lisière d'herbe mordant la roche | `Objects Under` |
| `Objects` | 0 | herbe, buissons du plateau | `Objects` |
| `Objects_Over` | 0 | rochers posés sur l'herbe | `Objects Over` |
| **`Fringe`** | **4** | **crête du plateau, DEVANT le joueur** | `Metano_Town_Fringe` |

Comme chez eux, un layer porte le nom de sa fonction et sort dans son propre
fichier `Cliff_<Layer>_<moment>.png`. `River` est séparé de `Base` précisément
pour la raison qui pousse Metano à le faire : on pourra l'animer en 4 frames
sans toucher ni à la mer ni à la falaise.

## Colorimétrie

Les tilesets réels ont été extraits de `Palikadude/Halcyon` et servent de
palette de référence (`reference_metano_*.png` dans ce dossier) :

| Élément | Couleur Metano | Source |
|---|---|---|
| Herbe | `(200, 216, 80)` jaune-olive | `Metano_Town_Cliffs.tile` |
| Roche | `(191, 131, 111)` ocre-sable | `Metano_Town_Cliffs.tile` |
| Eau | `(131, 218, 230)` cyan clair | `Metano_Town_River_Animation_1.tile` |
| Liseré d'eau | `(87, 135, 191)` bleu | idem |
| Écume | `(246, 250, 255)` | `Metano_Town_River_Sparkles.tile` |

L'eau de Metano ne compte que **19 couleurs** : elle est donc projetée sur sa
propre palette restreinte, pour que la mer ne dérive pas vers le vert.

Un point a demandé un traitement explicite : **l'herbe de Treasure Town n'est
pas verte, elle est olive.** Projeter sur la palette complète ne suffisait pas —
elle contient aussi les verts sombres du feuillage, et chaque vert froid de la
génération trouvait un vert froid proche. La fonction `virer_herbe_metano()`
force donc tout pixel à dominante verte vers l'un des quatre tons d'herbe
réellement mesurés dans le tileset.

## Conformité PMDO

**100 % des tuiles à ≤ 16 couleurs sur les 12 layers, 0 pixel semi-transparent.**

| Layer | Cellules | Couleurs | Coul./tuile |
|---|---|---|---|
| Sky | 4374 | 9 | 1,3 |
| Base (mer) | 2592 | 15 | 3,1 |
| Cliffs | 2020 | 28 | 3,7 |
| River | 47 | 7 | 1,7 |
| Objects | 321 | 3 | 1,6 |
| Fringe | 139 | 3 | 1,5 |

## Fichiers

* `layers/Cliff_<Layer>_<jour|nuit>.png` — les calques, cadre 648 × 432,
  même offset, superposables au pixel près ;
* `layers/Cliff_layers.json` — manifeste : ordre, champ `Layer`, métriques ;
* `cliff_<jour|nuit>.png` — aperçu composé ;
* `reference_metano_*.png` — les tilesets Metano extraits, palette de référence.

## Reproduire

```bash
python3 tileset_pmd/construire_cliff_layers.py
```
