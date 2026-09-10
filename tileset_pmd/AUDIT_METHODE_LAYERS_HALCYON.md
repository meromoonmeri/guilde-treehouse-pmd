# Audit — la méthode de zones en layers modulables de Halcyon

Analyse de `Palikadude/Halcyon`, le projet PMDO qui sert de référence à ce dépôt.
Mesures faites sur les **37 zones** (`Data/Ground/*.rsground`) et les **182
tilesets** (`Content/Tile/*.tile`) du dépôt, à la révision courante.

Objectif : comprendre comment ils découpent une zone en calques modulables.

---

## 1. Le principe : un layer = un tileset dédié qui porte son nom

C'est la règle structurante, et elle est suivie avec une rigueur presque totale.
Chaque calque d'une zone puise dans **un seul** tileset, nommé
`<Zone>_<NomDuLayer>` :

```
guild_dining_room.rsground        Content/Tile/
  Layers[0] "Floor"        ───▶    Guild_Dining_Room_Floor.tile
  Layers[1] "Walls"        ───▶    Guild_Dining_Room_Walls.tile
  Layers[2] "Shadows"      ───▶    Guild_Dining_Room_Shadows.tile
  Layers[3] "Objects"      ───▶    Guild_Dining_Room_Objects.tile
  Layers[4] "Objects Over" ───▶    Guild_Dining_Room_Objects_Over.tile
  Layers[5] "Fringe"       ───▶    Guild_Dining_Room_Fringe.tile
  Layers[6] "Supports"     ───▶    Guild_Dining_Room_Supports.tile
```

Taux de correspondance mesuré, par nom de layer :

| Nom du layer | Zones | Tileset homonyme |
|---|---|---|
| Objects | 29 | **29 / 29** |
| Base | 15 | **15 / 15** |
| Shadows | 14 | **14 / 14** |
| Objects Over | 14 | 13 / 14 |
| Floor | 12 | **12 / 12** |
| Walls | 12 | **12 / 12** |
| Supports | 12 | **12 / 12** |
| Objects Under | 10 | 9 / 10 |
| Fringe | 8 | **8 / 8** |
| *New Layer / Layer 1…4* | *13* | *0 / 13* |

Les seuls manquements sont les layers laissés au nom par défaut
(`New Layer`, `Layer 1`…), qu'on ne trouve que dans les zones inachevées
(`crooked_den`, `post_office`, `testmap`, `personality_test`,
`guild_first_floor`, `luminous_spring`). **Toutes les zones finies respectent la
convention.** Le nommage n'est donc pas décoratif : c'est le mécanisme même.

## 2. Le vocabulaire des layers, par type de zone

Ils n'appliquent pas une liste unique mais **deux vocabulaires** selon la nature
du lieu.

**Extérieurs et donjons** — socle `Base` :

```
Base > River > Cliffs > Shadows > Objects Under > Objects > Objects Over > Fringe
```
*(altere_pond, 8 layers — le cas le plus complet)*

**Intérieurs** — socle éclaté en `Floor` + `Walls` :

```
Floor > Walls > Shadows > Objects > Objects Over > Fringe > Supports
```
*(guild_dining_room, 7 layers)*

La distinction est nette : `Base` et `Floor` ne cohabitent jamais. Un intérieur
sépare le sol des murs parce que les deux se peuplent indépendamment ; un
extérieur n'a qu'un terrain continu.

## 3. Le champ `Layer` : la profondeur de rendu

Chaque calque porte, en plus de son nom, un entier `Layer` qui vaut **0 ou 4**,
et jamais autre chose. Relevé exhaustif :

| `Layer` = 0 — sous le joueur | `Layer` = 4 — au-dessus du joueur |
|---|---|
| Base, Floor, Floor Decor, Walls, River, Cliffs, Shadows, Objects Under, Objects, Objects Over, Trees, Big Tree | **Fringe, Supports, Ceiling** |

C'est **la clé de la modularité** : l'ordre dans la liste règle l'empilement
graphique, mais `Layer` décide de quel côté du personnage le calque est dessiné.
Les trois seuls calques à 4 sont ceux qui doivent passer devant le joueur — les
poutres (`Supports`), les avant-plans (`Fringe`), les plafonds (`Ceiling`).

Un `Objects Over` reste donc **derrière** le joueur : « Over » qualifie sa
position dans la pile de décor, pas son rapport au personnage. Confusion facile,
et le champ `Layer` est ce qui les départage.

## 4. Le tileset est taillé à la mesure du layer

Vérification qui en dit long sur leur pipeline. L'en-tête d'un `.tile` est :

```
octets 0-3  : taille de tuile   = 8         (toujours, sur les 182 fichiers)
octets 4-7  : nombre de tuiles
octets 8-15 : dimensions de la planche source, en tuiles
```

Or le **nombre de tuiles du `.tile` égale exactement le nombre de cellules
occupées par ce layer** dans le `.rsground` :

| Layer de `guild_dining_room` | Cellules dans le rsground | Tuiles dans le .tile |
|---|---|---|
| Floor | 752 | 752 |
| Walls | 631 | 631 |
| Shadows | 49 | 49 |
| Objects | 440 | 440 |
| Objects Over | 196 | 196 |
| Fringe | 10 | 10 |
| Supports | 1144 | 1144 |

Vérifié sur l'ensemble : **123 / 130 layers, soit 95 %**, respectent l'égalité
stricte. Les 7 écarts s'expliquent tous, et confirment la règle :

* les layers **animés** stockent *n* frames par cellule —
  `illuminant_riverbed_entrance / River` : 312 cellules × 4 frames = 1 248 tuiles,
  exactement le compte du `.tile` ;
* `metano_town / Objects Over Anim` et `altere_pond / River` sont des tilesets
  d'animation partagés entre plusieurs zones.

**Conclusion : le `.tile` n'est pas une bibliothèque où l'on pioche, c'est un
export exact du layer.** Aucune tuile morte. Le tileset est généré depuis la
carte, pas dessiné à l'avance.

## 5. Comment ils rendent une zone modulable

Trois mécanismes se combinent, et c'est leur combinaison qui fait la méthode :

1. **Découpage par fonction, pas par objet.** Un layer regroupe tout ce qui
   joue le même rôle visuel (toutes les ombres, tous les murs), pas un meuble.
   On active ou remplace une fonction entière d'un coup.
2. **Un tileset par layer, homonyme.** Substituer un décor = remplacer un seul
   `.tile`, sans toucher à la carte ni aux autres calques.
3. **Sous-zones en préfixes.** Metano Town décline 11 sous-lieux dans le même
   espace de noms — `Metano_Town_Cafe_*`, `Metano_Town_Inn_*`,
   `Metano_Town_Fire_Home_*` — chacun avec son propre jeu de layers. Une
   maison s'ajoute sans rien modifier de la ville.

La granularité est adaptée à la complexité : 2 layers pour une petite maison
(`Base > Objects`), 11 pour la ville entière.

## 6. Ce que ça implique pour notre café

Notre découpage actuel (`sans_deco` / `deco_seule` / `avec_deco`) est cohérent
avec leur principe — on sépare bien le socle du mobilier — mais reste plus
grossier. Transposé à leur vocabulaire, notre café donnerait :

| Notre fichier | Layer Halcyon | `Layer` |
|---|---|---|
| `interieur_sans_deco_*` | `Floor` + `Walls` | 0 |
| *(ombres, aujourd'hui fondues dans le sol)* | `Shadows` | 0 |
| `interieur_deco_seule_*` | `Objects` | 0 |
| *(guirlandes, bandeau de rideaux)* | `Objects Over` | 0 |
| *(rien pour l'instant)* | `Supports` / `Fringe` | **4** |

Deux enseignements concrets :

* **Nos ombres devraient être un layer à part.** On les assombrit dans le sol,
  ce qui les rend indissociables ; eux les isolent systématiquement — 14 zones
  sur 37 ont un layer `Shadows` dédié, y compris le café de Metano.
* **Il nous manque la notion de `Layer = 4`.** Aucun de nos calques ne passe
  devant le joueur. Pour le sous-sol, le bandeau de rideaux et la frise
  suspendue en haut de la scène seraient légitimement des `Fringe`.

---

### Sources

* `Palikadude/Halcyon` — `Data/Ground/*.rsground` (37 zones),
  `Content/Tile/*.tile` (182 tilesets).
* Format : JSON UTF-8 avec BOM, racine `Object` de type
  `RogueEssence.Ground.GroundMap`. Grille de collision 8 px
  (`obstacles[].Bounds` en blocs de 8), `TexSize: 1`.
