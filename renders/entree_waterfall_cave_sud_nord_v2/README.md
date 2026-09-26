# EWC2 — Entrée Waterfall Cave V2, cascade en deux temps (4:3 vaste)

Demande (retours sur EWC1) : « il y a des petits traits blancs au bord des rives, fais une version sans ça, et faut pas d'eau devant l'entrée de la grotte, et faut que la cascade soit en deux temps : la cascade qui prend tout et après une animation où la cascade se fend pour ouvrir la grotte que tu as créée ».

- **Taille** : 768 × 576 px = 96 × 72 cases de 8 px.
- **Base** : EWC1, avec **les mêmes bruts générés** (`source/entree_waterfall_cave_sud_nord_v1/bruts/`, hachés). Aucune nouvelle génération. EWC1 reste intact.
- **Aperçu** : `apercu_entree_waterfall_cave_sud_nord_v2.html` (racine). Il a des boutons « Ouvrir la cascade » et « Refermer », et une démo automatique.
- **Autres fichiers** :
  - pack PMDO 0.8.12 : `EWC2_projet_pmdo_0812.zip` ;
  - calques PNG 8 px : `EWC2_calques_png_8px.zip` ;
  - source : `source/entree_waterfall_cave_sud_nord_v2/`, 15 tests.

## 1. Plus de petits traits blancs au bord des rives

Ces traits venaient de `water_phases`, que la V1 reprenait du lot Bristle. Cette fonction posait contre chaque rive des tirets de 1 px de couleur `clair` (148, 230, 238). La V2 utilise une copie de la fonction sans cette ligne : la bande sombre (`bande`, 87, 135, 191) touche directement la rive. Les couleurs restantes (surface, inter, accent, bande) sont toutes des couleurs Métano exactes.

Deux tests le vérifient :

- `clair` est absent de l'eau ;
- chaque pixel d'eau qui touche la terre est de la couleur `bande`.

L'image `review/EWC2_rive_avant_apres_x4.png` montre la même rive en V1 (à gauche) et en V2 (à droite). Les scintillements natifs, au large, sont gardés.

## 2. Pas d'eau devant l'entrée de la grotte

La partie centrale de la vasque est remplacée par un **couloir de sable**.

- **Pixels** : ceux du sol complet généré.
- **Forme** : il va du pied de la bouche jusqu'au chemin central, avec un palier devant la bouche, un léger renflement et un évasement vers la plage.
- **Bassins** : la vasque devient deux petits bassins latéraux, au pied des deux moitiés du rideau.
- **Berge de raccord** : le sable, à 3 px au plus de l'eau, est assombri au rapport mesuré berge/sable du décor (0,63 ; 0,62 ; 0,71).
- **Lisière** : le long de l'écume du pied, les blancs de l'écume dessinée restent de l'écume à 5 px au plus du bord. La lisière est ainsi irrégulière, et on n'ajoute pas de berge : elle faisait des traits bruns dans l'écume.
- **Chiffres** : 6 710 px d'eau retirés (pleine résolution).
- **Tests** : aucune eau ni écume dans le cœur du couloir, et plus de 97 % de sable praticable jusqu'à la bouche.

## 3. La cascade en deux temps

La carte a trois **calques d'état**. Tous les trois utilisent la même texture générée périodique du rideau (période 72 px, 6 px vers le sud par phase).

| État | Calques | Durée | Ce qu'on voit |
|---|---|---|---|
| **fermée** (au chargement) | 11 `cascade_fermee`, 16 `ecume_porte_fermee` | boucle 12 × 4 ticks | le rideau recouvre toute la grotte, avec des bouillons au pied sur le haut du couloir |
| **ouverture** | 12 `cascade_ouverture`, 17 `ecume_porte_ouverture` | 24 × 4 = 96 ticks (1,6 s), une fois | la fente naît en haut au centre, descend et s'écarte jusqu'au contour de la grotte ; les bouillons s'éteignent quand la fente les atteint, et des gerbes jaillissent aux lèvres basses |
| **ouverte** | 13 `cascade_ouverte` | boucle 12 × 4 ticks | le rideau contourne la grotte, comme en V1 |

- **Porte** : c'est la zone couverte seulement quand la cascade est fermée. Elle comprend la bouche et les éclats de rebord rocheux autour d'elle (101 px). Sans eux, ces éclats flottaient sur le rideau fermé.
- **Fente** :
  - Chaque pixel de la porte reçoit un temps d'ouverture : 0,7 × l'écart au centre (rapporté à la demi-largeur de sa rangée) + 0,3 × la profondeur. La progression est lissée (smoothstep).
  - Les lèvres de la fente ont 1 px du blanc du rideau et 1 px éclairci. Elles restent dans la porte, donc il n'en reste aucune une fois la cascade ouverte.
- **Raccords vérifiés par test** :
  - la phase 0 de l'ouverture est identique à la phase 0 de l'état fermé ;
  - la phase 23 est identique à la phase 11 de l'état ouvert, qui enchaîne sur la phase 0 ;
  - la fente ne fait que s'agrandir ;
  - hors de la porte, le rideau défile à l'identique ;
  - la fente naît dans la moitié haute de la bouche ;
  - la dernière phase de l'écume de la porte est vide.
- **Calage** : il faut lancer l'ouverture sur un tick multiple de 48, qui correspond à la phase 0 du rideau. L'aperçu attend ce tick.

L'image `review/EWC2_ouverture_planche_x2.png` montre 8 phases de l'ouverture (0, 4, 7, 10, 13, 16, 19, 23). L'image `review/EWC2_scene_animee.webp` enchaîne l'état fermé, l'ouverture puis l'état ouvert.

## Calques (bas → haut)

| # | Calque | Animation | État |
|---|---|---|---|
| 00 | eau (bassins) | 4 × 10 ticks | — |
| 01 | scintillements natifs | 4 × 10 ticks | — |
| 02–10 | sol complet, sable, cailloux, touffes, plateaux, berge, falaises, arbres, entrée sombre | fixes | — |
| 11 | cascade_fermee | 12 × 4 ticks | fermée |
| 12 | cascade_ouverture | 24 × 4 ticks | ouverture |
| 13 | cascade_ouverte | 12 × 4 ticks | ouverte |
| 14 | ecume_pied | fixe | — |
| 15 | ecume (bouillons latéraux) | 12 × 4 ticks | — |
| 16 | ecume_porte_fermee | 12 × 4 ticks | fermée |
| 17 | ecume_porte_ouverture | 24 × 4 ticks | ouverture |
| 18 | embruns (dans les bassins latéraux) | 12 × 4 ticks | — |
| 19 | Top vide (`Layer=4`) | — | — |

Palettes : terrain 96 couleurs, arbres 24, eau dessinée 24 (le rideau des trois états et l'écume du pied), bouche 12.

Fidélité au rip des calques finaux : sable 7,1, roche 5,1, feuillage 2,3, rideau 8,6. Le seuil de test est 20.

## PMDO

- **Visibilité** : les calques des états ouverture et ouverte sont enregistrés avec `Visible=false`. L'ORA les marque aussi `hidden`.
- **Script** : `init.lua` fournit `ouvrir_cascade()`. Elle bascule la visibilité, attend 96 frames, puis passe à l'état ouvert. **Elle n'a pas été testée dans PMDO**, et deux points restent à vérifier : l'accès Lua à `Layers[i].Visible`, et le calage de la phase de l'ouverture sur l'horloge du moteur.
- **Collisions** : elles sont fixes. Le couloir est praticable jusqu'au seuil, et c'est au script de bloquer l'entrée tant que la cascade est fermée.
- **Marqueurs** : `entrance` est au sud en (392, 560). `donjon_seuil` est en (376, 184), en haut du couloir, au pied de la grotte.
- **Praticabilité** : 760 cases praticables sur 6 912.

## Limites

- **Pixels** : tout est généré ou recalculé ; rien n'est présenté comme natif, sauf les scintillements.
- **Animations** : la fente et sa chronologie sont créées par nous, ce n'est pas une animation officielle.
- **Ombres** : il n'y a pas de calque d'ombres, comme en V1, car aucune ombre portée n'est séparable dans le rendu généré.
- **Tests** : aucun test dans PMDO (runtime, GPU, jeu).
- **Validation** : `art_approved: false`.

## Commandes

```bash
.venv/bin/python source/entree_waterfall_cave_sud_nord_v2/build.py      # ~60 s
.venv/bin/python -m unittest source.entree_waterfall_cave_sud_nord_v2.test_build -v
.venv/bin/python source/entree_waterfall_cave_sud_nord_v2/package.py    # tests + zips + aperçu
```
