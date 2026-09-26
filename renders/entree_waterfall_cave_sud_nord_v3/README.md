# EWC3 — Entrée Waterfall Cave V3 : la cascade se fend en deux (4:3 vaste)

Demande (retours sur EWC1) : « il y a des petits traits blancs au bord des rives, fais une version sans ça, et faut pas d'eau devant l'entrée de la grotte, et faut que la cascade soit en deux temps : la cascade qui prend tout et après une animation où la cascade se fend pour ouvrir la grotte que tu as créée ».

EWC2, poussé plus tôt sur la même branche, répond déjà aux trois points. Sa fente est un trou en forme de grotte qui se découpe dans le rideau. **EWC3 est une autre lecture de « la cascade se fend »** : le rideau se fend **en deux sur toute sa hauteur**, et ses deux moitiés **s'écartent** devant une paroi rocheuse générée. EWC1 et EWC2 restent intacts.

- **Taille** : 768 × 576 px = 96 × 72 cases de 8 px.
- **Base** : EWC2, importé tel quel (eau sans liseré, couloir de sable, texture du rideau, écume, états, collisions). Un test vérifie que les 16 calques hors cascade et paroi sont identiques à ceux d'EWC2, pixel pour pixel.
- **Bruts** : les 3 bruts d'EWC1 (hachés), plus **1 nouveau brut généré** (`source/entree_waterfall_cave_sud_nord_v3/bruts/falaise_sans_cascade.png`) : le décor EWC1 édité par le générateur, sans la cascade. Le prompt est dans le manifest.
- **Aperçu** : `apercu_entree_waterfall_cave_sud_nord_v3.html` (racine). Il a des boutons « Ouvrir la cascade » et « Refermer », et une démo automatique.
- **Autres fichiers** :
  - pack PMDO 0.8.12 : `EWC3_projet_pmdo_0812.zip` ;
  - calques PNG 8 px : `EWC3_calques_png_8px.zip` ;
  - source : `source/entree_waterfall_cave_sud_nord_v3/`, 17 tests.

## 1 et 2. Rives sans traits blancs, couloir de sable jusqu'à la grotte

Repris d'EWC2 sans changement :

- l'eau façon Métano n'a plus le liseré `clair` en tirets contre les rives ;
- un couloir de sable (pixels du sol complet généré) remplace l'eau devant la bouche.

Les tests d'EWC2 sur ces deux points sont repris.

## 3. La cascade se fend en deux

| État | Calques | Durée | Ce qu'on voit |
|---|---|---|---|
| **fermée** (au chargement) | 12 `cascade_fermee`, 17 `ecume_porte_fermee` | boucle 12 × 4 ticks | le rideau recouvre toute la grotte (identique à EWC2) |
| **ouverture** | 13 `cascade_ouverture`, 18 `ecume_porte_ouverture` | 24 × 4 = 96 ticks (1,6 s), une fois | une fissure part de la lèvre et descend jusqu'à la grotte, avec une gerbe à sa pointe ; puis les deux moitiés s'écartent |
| **ouverte** | 14 `cascade_ouverte` | boucle 12 × 4 ticks | deux chutes de part et d'autre ; entre elles, la paroi sèche et la grotte |

- **Fissure** :
  - Elle part de y = 34, sous la lèvre de la falaise, et descend jusqu'au bas de la bouche (y = 182).
  - La rangée y commence à s'ouvrir au temps 0,4 × (y − 34) / (182 − 34). Elle s'élargit ensuite en smoothstep, sur les 60 % restants de la durée.
  - La pointe est arrondie en quart d'ellipse sur 22 px.
- **Largeur finale** : la porte (bouche + éclats de rebord) plus 4 px de chaque côté. Les demi-largeurs valent 34 et 33 px autour de x = 384.
- **Écartement** : l'eau n'est pas découpée, elle est repoussée.
  - Chaque colonne source s est déplacée de largeur × u^1,4 vers l'extérieur. u vaut 0 au bord extérieur du rideau et 1 au centre.
  - Le bord extérieur du rideau ne bouge pas, et l'eau se tasse près de la fente.
  - Autour de la pointe, le champ varie d'une rangée à l'autre : l'eau contourne l'arrondi.
- **Bords d'eau** :
  - 1 px du blanc du rideau le long de la fente ;
  - un 2e px éclairci sur une demi-bande de 12 px sur deux, qui défile avec l'eau ;
  - une ondulation de ±1 px (période 36 px), qui défile aussi.
  - Ce sont des couleurs du rideau, pas le liseré `clair` des rives.
- **Paroi derrière** (calque 09 `roche_derriere`) :
  - pixels du nouveau brut, recalés au pixel près (décalage mesuré (0, 0) : écart 5,4 contre 9,4 à 1 px) ;
  - réduits comme le sol complet, puis ramenés à la palette du terrain (83 couleurs, aucune nouvelle) ;
  - 8 038 px, uniquement derrière le rideau, jamais sur la bouche.
  - Un test vérifie qu'aucune phase ne montre le sable à travers la fente.
- **Raccords vérifiés par test** :
  - l'ouverture phase 0 est identique à l'état fermé phase 0 ;
  - l'ouverture phase 23 est identique à l'état ouvert phase 11, qui enchaîne sur la phase 0 ;
  - la fente ne se referme jamais, et sa pointe descend à chaque phase ;
  - au-dessus de la pointe, le rideau ne change pas ;
  - dans l'état ouvert, la grotte garde au moins 2 px de roche autour d'elle ;
  - hors de l'arrondi, le défilement de l'état ouvert est une translation pure, 11 → 0 compris.
- **Écume** : les bouillons du pied s'éteignent quand la fente atteint leur colonne, et des gerbes jaillissent aux lèvres basses (code EWC2). S'y ajoute une gerbe générée qui suit la pointe de la fissure (phases 1 à 8).
- **Calage** : il faut lancer l'ouverture sur un tick multiple de 48, qui correspond à la phase 0 du rideau. L'aperçu attend ce tick.

Images de contrôle :

- `review/EWC3_ouverture_planche_x2.png` : 8 phases (0, 3, 6, 9, 12, 15, 18, 23) ;
- `review/EWC3_ouverte_v2_v3_x2.png` : l'état ouvert d'EWC2 à gauche, celui d'EWC3 à droite ;
- `review/EWC3_scene_animee.webp` : l'état fermé, l'ouverture, puis l'état ouvert.

## Calques (bas → haut)

| # | Calque | Animation | État |
|---|---|---|---|
| 00 | eau (bassins) | 4 × 10 ticks | — |
| 01 | scintillements natifs | 4 × 10 ticks | — |
| 02–08 | sol complet, sable, cailloux, touffes, plateaux, berge, falaises | fixes | — |
| 09 | roche_derriere (paroi générée) | fixe | — |
| 10–11 | arbres, entrée sombre | fixes | — |
| 12 | cascade_fermee | 12 × 4 ticks | fermée |
| 13 | cascade_ouverture | 24 × 4 ticks | ouverture |
| 14 | cascade_ouverte | 12 × 4 ticks | ouverte |
| 15 | ecume_pied | fixe | — |
| 16 | ecume (bouillons latéraux) | 12 × 4 ticks | — |
| 17 | ecume_porte_fermee | 12 × 4 ticks | fermée |
| 18 | ecume_porte_ouverture | 24 × 4 ticks | ouverture |
| 19 | embruns | 12 × 4 ticks | — |
| 20 | Top vide (`Layer=4`) | — | — |

**Palettes** : terrain ≤ 96 couleurs (paroi comprise), arbres 24, eau dessinée 24 (le rideau des trois états et l'écume du pied), bouche 12.

**Fidélité au rip** des calques finaux (seuil de test : 20) :

| Matière | Distance |
|---|---|
| sable | 7,1 |
| roche | 5,1 |
| paroi derrière la cascade | 10,4 (5,5 des falaises de la carte) |
| feuillage | 2,3 |
| rideau fermé | 9,2 |
| rideau ouvert | 18,1 |

Le rideau ouvert est plus clair parce qu'il ne garde que les côtés de la chute, déjà bordés de blanc dans le dessin généré. Sans ses 2 px de bord, il est à 14,7.

## PMDO

- **Visibilité** : les calques des états ouverture et ouverte sont enregistrés avec `Visible=false`. L'ORA les marque aussi `hidden`.
- **Script** : `init.lua` fournit `ouvrir_cascade()`, comme en V2. **Elle n'a pas été testée dans PMDO**, et deux points restent à vérifier : l'accès Lua à `Layers[i].Visible`, et le calage de la phase de l'ouverture sur l'horloge du moteur.
- **Collisions et marqueurs** : identiques à EWC2.
  - `entrance` (392, 560) est au sud, `donjon_seuil` (376, 184) au pied de la grotte.
  - 760 cases praticables sur 6 912.
  - C'est au script de bloquer l'entrée tant que la cascade est fermée.
- **Tuiles** : 25 474.

## Limites

- **Pixels** : tout est généré ou recalculé ; rien n'est présenté comme natif, sauf les scintillements.
- **Animations** : la fissure, l'écartement et leur chronologie sont créés par nous, ce n'est pas une animation officielle.
- **Ombres** : il n'y a pas de calque d'ombres, car aucune ombre portée n'est séparable dans le rendu généré.
- **Tests** : aucun test dans PMDO (runtime, GPU, jeu).
- **Validation** : `art_approved: false`.

## Commandes

```bash
.venv/bin/python source/entree_waterfall_cave_sud_nord_v3/build.py      # ~70 s ; EWC2 doit être présent
.venv/bin/python -m unittest source.entree_waterfall_cave_sud_nord_v3.test_build -v
.venv/bin/python source/entree_waterfall_cave_sud_nord_v3/package.py    # tests + zips + aperçu
```
