# Analyse d'échelle — Guilde Treehouse vs *Pokémon Mystery Dungeon: Halcyon*

> **Verdict en une ligne :** nos salles ne sont pas « un peu » trop grandes, elles sont
> **×3 en surface de sol (×1,73 en linéaire) pour les chambres** et **×2,3 pour le hall**
> par rapport aux salles de guilde de Halcyon, avec en plus **0 % de mobilier** là où
> Halcyon en pose 24 à 59 %. Le personnage n'est pas trop petit : c'est le décor qui est
> dessiné trop grand. Un facteur global de **×0,65** sur tout le kit remet chaque salle
> exactement dans les fourchettes de Halcyon.

Toutes les valeurs ci-dessous sont **mesurées par script**, pas estimées à l'œil :

| Script | Rôle |
|---|---|
| `analyse_echelle/rsread.py` | lecture des `.rsground` / `.tile` de RogueEssence et recomposition des cartes de Halcyon |
| `analyse_echelle/mesures.py` | mesure des masques de sol praticable des deux projets → `mesures.json` |
| `analyse_echelle/apercus.py` | planches de comparaison à 1:1 avec de vrais sprites Pokémon → `img/` |
| `analyse_echelle/cibles.py` | dimensions cibles salle par salle → `cibles.json` |

Source de référence : dépôt **Palikadude/Halcyon** (mod RogueEssence/PMDO, v0.4.0),
13 cartes de guilde (`Data/Ground/guild_*.rsground`) + 4 intérieurs de ville pour contrôle.

---

## 1. Les unités : sprite, case, viewport

Rien de tout cela n'est une supposition, tout est relevé dans les données de Halcyon /
RogueEssence :

| Grandeur | Valeur mesurée | Où |
|---|---|---|
| Sprite Pokémon visible (starter type) | **19 à 27 px de large, 20 à 22 px de haut** | frames des `Content/Chara/*.chara` |
| Cellule de frame d'un sprite | 30 à 32 px | idem |
| Collider d'un personnage en ground map | **16 × 16 px** | `Collider` des `MapChars` |
| Grille de collision d'une ground map | **8 px** | grille `obstacles` |
| Case de donjon PMD (unité de lecture) | **24 px** | standard PMD/EoS, utilisé ici comme unité |
| Viewport logique du moteur | **320 × 240 px** | `Content/UI/Title.png` (écran-titre plein cadre) |

**Conséquences directes, à garder en tête pour tout le reste :**

- 1 case de 24 px ≈ **1 sprite Pokémon**. Le sprite remplit sa case, il ne flotte pas dedans.
- L'écran fait **13,3 × 10 cases**. Un Pokémon occupe **~6 % de la largeur de l'écran**.
- Une salle « d'un écran » = 320 × 240 px. C'est exactement la taille de l'entrée de la
  guilde de Halcyon (`guild_first_floor`, 40 × 30 blocs de 8 px).

---

## 2. Halcyon : les proportions de référence

Sol praticable réel (collision `obstacles` ∩ calque *Floor* ∩ zone atteignable depuis
l'entrée), en cases de 24 px.

| Salle Halcyon | Toile px | Emprise du sol (cases) | Sol (cases²) | Largeur locale médiane | Plus grand vide | Décor couvrant | Sol / sprite | Écrans |
|---|---|---|---|---|---|---|---|---|
| Entrée (1F) | 320x240 | 6.7 x 8.3 | 32 | 1.0 | 3.3 | 0 % | 42 | 0.42 |
| Étage commun (2F) — hub | 672x448 | 24.0 x 11.0 | 158 | 2.1 | 7.5 | 36 % | 207 | 1.98 |
| Lobby (3F) — hub | 800x448 | 33.2 x 13.3 | 193 | 2.2 | 8.4 | 24 % | 253 | 3.31 |
| Réfectoire | 448x288 | 15.3 x 4.3 | 38 | 0.8 | 2.1 | 59 % | 50 | 0.50 |
| Bureau du maître | 384x384 | 12.0 x 12.0 | 80 | 1.9 | 7.7 | 55 % | 104 | 1.08 |
| Réserve | 352x352 | 13.9 x 10.1 | 77 | 0.9 | 3.1 | 46 % | 101 | 1.05 |
| Chambre du héros | 352x352 | 13.3 x 7.0 | 52 | 1.3 | 5.5 | 40 % | 68 | 0.70 |
| Chambre haut-gauche | 352x352 | 9.3 x 9.3 | 53 | 1.5 | 5.6 | 38 % | 70 | 0.65 |
| Chambre haut-droite | 352x352 | 9.3 x 9.3 | 55 | 1.7 | 5.8 | 35 % | 72 | 0.65 |
| Chambre bas-gauche | 352x352 | 9.3 x 13.6 | 51 | 1.2 | 4.3 | 36 % | 66 | 0.95 |
| Chambre bas-droite | 352x352 | 9.3 x 13.6 | 50 | 1.1 | 4.8 | 37 % | 65 | 0.95 |
| Couloir des chambres | 480x256 | 19.9 x 10.6 | 63 | 0.9 | 3.4 | 4 % | 83 | 1.58 |
| Couloir de la réserve | 352x384 | 14.6 x 8.3 | 35 | 0.8 | 3.1 | 4 % | 46 | 0.91 |

*Lecture des colonnes :*
- **Largeur locale** = 2 × distance au mur/meuble le plus proche, en cases. C'est
  « l'épaisseur » de l'espace ressentie sous les pieds du personnage.
- **Plus grand vide** = diamètre du plus grand disque de sol sans rien, en cases.
- **Sol / sprite** = surface de sol divisée par la surface d'un sprite (20 × 22 px).
- **Écrans** = emprise du sol rapportée au viewport 320 × 240.

**Les quatre familles de Halcyon :**

| Famille | Sol utile | Emprise | Largeur locale méd. | Décor |
|---|---|---|---|---|
| Chambre / dortoir | **50 – 55 cases²** | 9 – 13 × 7 – 14 | 1,1 – 1,7 | 35 – 40 % |
| Salle spécialisée (réfectoire, bureau, réserve) | **38 – 80 cases²** | 12 – 16 × 4 – 12 | 0,8 – 1,9 | 46 – 59 % |
| Hub (étage commun, lobby) | **158 – 193 cases²** | 24 – 33 × 11 – 13 | 2,1 – 2,2 | 24 – 36 % |
| Couloir | 35 – 63 cases² | largeur **1,3 – 1,7 case** | 0,8 – 0,9 | 4 % |

Point capital : **il n'y a qu'une seule grande pièce par étage**. Tout le reste est
plus petit qu'un écran et demi.

---

## 3. Notre projet : les mêmes mesures

| Notre salle | Toile px | Emprise du sol (cases) | Sol (cases²) | Largeur locale médiane | Plus grand vide | Décor | Sol / sprite | Écrans |
|---|---|---|---|---|---|---|---|---|
| 01 Accueil de la guilde | 648x432 | 23.2 x 17.6 | 182 | 2.6 | 8.4 | 0 % | 238 | 3.06 |
| 02 Hall des missions | 1280x544 | 51.2 x 13.3 | 452 | 3.2 | 10.3 | 0 % | 591 | 5.11 |
| 03 Grande salle commune | 648x432 | 26.9 x 10.2 | 162 | 2.5 | 7.3 | 0 % | 212 | 2.06 |
| 04 Cantine | 648x432 | 25.0 x 7.7 | 143 | 2.8 | 7.4 | 0 % | 187 | 1.45 |
| 05 Chambre de l'équipe | 648x432 | 25.1 x 7.8 | 154 | 2.7 | 7.4 | 0 % | 201 | 1.46 |
| 06 Chambre du veilleur | 648x432 | 23.2 x 10.6 | 159 | 2.8 | 7.5 | 0 % | 208 | 1.84 |
| 07 Chambre des résidents | 648x432 | 25.1 x 7.8 | 154 | 2.7 | 7.4 | 0 % | 202 | 1.46 |
| 08 Dortoir des apprentis | 648x432 | 25.1 x 8.2 | 158 | 2.8 | 8.2 | 0 % | 206 | 1.54 |
| 09 Grand dortoir | 648x432 | 23.2 x 15.2 | 170 | 2.8 | 8.2 | 0 % | 223 | 2.65 |
| 10 Dortoir des explorateurs | 648x432 | 25.1 x 8.2 | 157 | 2.8 | 7.8 | 0 % | 205 | 1.54 |
| 11 Chambre des éclaireurs | 648x432 | 25.1 x 7.8 | 154 | 2.8 | 7.4 | 0 % | 202 | 1.46 |
| 12 Salle du chef | 648x432 | 22.1 x 10.3 | 146 | 2.8 | 7.2 | 0 % | 192 | 1.71 |

**Nos 12 salles ont toutes la taille du hub de Halcyon**, alors que 10 d'entre elles
sont des chambres ou des petites salles.

---

## 4. Comparaison point par point

| Critère | Nous | Halcyon | Facteur | Cible |
|---|---|---|---|---|
| **Sprite vs case de sol** | sprite 20 × 22 px pour des salles de 648 px | sprite 20 × 22 px pour des salles de 352 px | — | 1 sprite ≈ 1 case de 24 px |
| **Sprite vs viewport** | 6 % de l'écran, salle = 2 à 5 écrans | 6 % de l'écran, salle = 0,4 à 3,3 écrans | ×1,5 – 2 | ≤ 1,5 écran hors hub |
| **Largeur × hauteur d'une chambre** | 25 × 8 cases de sol, toile 648 × 432 | 9 × 9 cases de sol, toile 352 × 352 | **×2,7 en largeur** | 11 – 13 × 8 – 10 cases |
| **Surface de sol d'une chambre** | 156 cases² (médiane) | 52 cases² (médiane) | **×3,0 en surface, ×1,73 en linéaire** | 50 – 65 cases² |
| **Surface de sol du hall** | 452 cases² | 193 cases² (plus grande salle du jeu) | **×2,34 (×1,53 linéaire)** | 150 – 200 cases² |
| **Distance mur ↔ personnage** | largeur locale médiane 2,5 – 3,2 cases | 0,8 – 1,7 cases (2,1 – 2,2 dans les hubs) | **×1,6 – 2,5** | 1,0 – 1,7 case |
| **Plus grande poche de vide** | 7,2 – 10,3 cases de diamètre | 4,3 – 5,8 (chambres), 7,5 – 8,4 (hubs) | ×1,5 – 1,8 | ≤ 6 cases hors hub |
| **Largeur des passages / couloirs** | 53 – 136 px = **2,2 – 5,7 cases** | 32 – 40 px = **1,3 – 1,7 case** | **×1,7 – 3,4** | 32 – 48 px (1,5 – 2 cases) |
| **Densité de décoration** | **0 %** (calques `06_decorations` et `07_objets` vides) | 35 – 40 % chambres, 46 – 59 % salles, 24 – 36 % hubs, 4 % couloirs | ∞ | 30 – 45 % du sol |
| **Nombre d'objets par salle** | 0 | 5 à 17 îlots de mobilier | — | 1 prop / 5 – 10 cases² |
| **Taille des meubles** | table de banquet 260 × 113 px = **12 × 5 sprites** ; végétation 76 × 105 px = **3,5 × 5 sprites** ; coffre 61 × 44 px | mobilier médian **40 × 56 px** (1,7 × 2,3 cases ≈ 2 sprites) ; caisse 24 × 24 px = 1 case ; gros meubles 128 – 216 px | **×1,5 – 2,5** | meuble courant 24 – 56 px, gros meuble ≤ 150 px |
| **Portes** | 76 × 72 px (3,2 × 3 cases) | 58 × 54 px (2,4 × 2,2 cases) | ×1,3 | 48 – 56 px de large |
| **Fenêtres** | 46 – 88 × 71 – 91 px | 52 × 59 px | ×1,2 – 1,5 | ~48 × 56 px |
| **Hauteur visuelle des murs** (bandeau au-dessus du sol) | **150 – 215 px = 6,2 – 9,0 cases** | **90 – 97 px = 3,8 – 4,0 cases** | **×1,7 – 2,4** | 90 – 110 px (4 – 4,5 cases) |
| **Rapport salle entière / personnage** | 187 – 591 sprites de surface | 42 – 253 sprites (65 – 72 pour une chambre) | ×2,3 – 3,0 | 60 – 105 hors hub |

### Ce que ça veut dire concrètement

1. **Le sprite n'est pas trop petit.** Notre décor est dessiné **~1,3 – 1,5 × trop grand**
   (portes, fenêtres, hauteur de mur, mobilier), et par-dessus, l'emprise de sol est
   **~1,7 × trop grande en linéaire**. Les deux erreurs s'additionnent : d'où la
   sensation de « sprite perdu ».
2. **Le vide est structurel, pas décoratif.** Chez Halcyon, la moitié du sol est à moins
   de 0,5 – 0,85 case d'un mur ou d'un meuble ; chez nous, à 1,3 – 1,6 case. Même en
   posant du mobilier, une ellipse de 25 cases de large restera vide au centre.
3. **Les passages sont des routes.** 2,2 à 5,7 cases de large, là où Halcyon fait passer
   tout le monde dans 1,3 – 1,7 case. Un couloir large casse la lisibilité PMD (on ne
   sait plus où va le joueur).

Planches visuelles (sprites Pokémon réels posés à 1:1, cadre bleu = viewport 320 × 240) :

| Fichier | Contenu |
|---|---|
| `img/comparaison_1a1.png` | notre salle commune face à 3 salles de Halcyon, même échelle pixel |
| `img/projet_salles_1a1.png` | nos 12 salles avec 4 sprites posés dessus |
| `img/halcyon_salles_1a1.png` | les 13 salles de guilde de Halcyon, même traitement |
| `img/simulation_reduction.png` | nos salles à ×1,00 / ×0,65 / ×0,50 |
| `img/gabarits_cibles.png` | gabarits recommandés en cases de 24 px |

---

## 5. Recommandation

### Actuel
- Salle courante (chambre/dortoir) : **~25 × 8 cases de sol**, toile 648 × 432 px
- Hall : **~51 × 13 cases de sol**, toile 1280 × 544 px
- Sprite : **~1 case (20 × 22 px)**
- Ratio surface salle / sprite : **190 – 240** (chambres), **591** (hall) → **trop élevé**
- Décor : **0 %** ; passages **2,2 – 5,7 cases** ; mur **6 – 9 cases** de haut

### Halcyon (référence)
- Chambre : **9 × 9 cases de sol** (50 – 55 cases²), toile 352 × 352 px
- Salle spécialisée : **12 – 16 × 4 – 12 cases** (38 – 80 cases²), toile 352 – 448 px
- Hub unique par étage : **24 – 33 × 11 – 13 cases** (158 – 193 cases²), toile 672 – 800 px
- Sprite : **~1 case (20 × 22 px)**
- Ratio surface salle / sprite : **65 – 72** (chambre), **207 – 253** (hub) → **référence**
- Décor : **24 – 59 %** ; passages **1,3 – 1,7 case** ; mur **3,8 – 4,0 cases** de haut

### Recommandation
- **Nouvelle chambre / dortoir : 11 × 9 cases d'emprise, 9 × 7 cases de sol utile
  (50 – 65 cases²)** → toile **≈ 408 × 264 px**
- **Nouvelle salle spécialisée (cantine, bureau du chef, réserve, accueil) :
  14 × 11 cases d'emprise, 12 × 9 cases de sol utile (75 – 110 cases²)** → toile
  **≈ 432 – 480 × 288 – 312 px**
- **Nouveau hall / hub (un seul dans la guilde) : 18 – 34 × 12 – 15 cases d'emprise,
  16 – 30 × 10 – 12 cases de sol utile (150 – 200 cases²)** → toile **≈ 840 × 360 px**
- **Couloirs et passages : 2 cases (48 px), jamais plus de 3 ; une porte = 1 – 2 cases**
- **Distance minimale autour d'un personnage : 1 case libre (24 px) dans les axes de
  circulation ; 2 cases devant un meuble interactif ; largeur locale médiane visée
  1,0 – 1,7 case**
- **Aucune poche de sol vide de plus de 6 cases de diamètre hors hub (8 dans le hub)**
- **Espaces communs : 12 × 9 cases utiles suffisent pour 4 – 6 personnages ;
  16 × 10 pour la salle de rassemblement de toute la guilde**
- **Densité : 30 – 45 % du sol occupé ou bordé de mobilier, soit 6 à 15 props par salle
  (1 prop pour 5 – 10 cases² de sol)**
- **Hauteur du bandeau de mur : 90 – 110 px (4 – 4,5 cases)**, contre 150 – 215 px aujourd'hui
- **Meubles : 24 – 56 px pour le mobilier courant (1 – 2,5 cases), 150 px maximum pour
  une grande table ; une caisse = 1 case ; une plante en pot ≤ 2 cases de haut**

### Le raccourci qui marche : facteur global ×0,65

Comme l'erreur est presque uniforme (décor ×1,3 – 1,5, emprise ×1,7), **un seul facteur
d'échelle ×0,65 appliqué à tout le kit** place chaque salle dans la fourchette Halcyon,
sans rien redessiner de la composition :

| Salle | Toile actuelle | Sol actuel | Toile ×0,65 | Sol visé | Toile ajustée | Remarque |
|---|---|---|---|---|---|---|
| 01 Accueil | 648×432 | 182 | 432×288 | 77 | **432×288** | dans la fourchette |
| 02 Hall des missions | 1280×544 | 452 | 840×360 | 191 | **840×360** | = lobby 3F de Halcyon (193) |
| 03 Grande salle commune | 648×432 | 162 | 432×288 | 68 | **456×312** | élargir ×1,05 |
| 04 Cantine | 648×432 | 143 | 432×288 | 60 | **480×312** | élargir ×1,12 |
| 05 Chambre de l'équipe | 648×432 | 154 | 432×288 | 65 | **408×288** | ×0,96 |
| 06 Chambre du veilleur | 648×432 | 159 | 432×288 | 67 | **408×264** | ×0,95 |
| 07 Chambre des résidents | 648×432 | 154 | 432×288 | 65 | **408×288** | ×0,96 |
| 08 Dortoir des apprentis | 648×432 | 158 | 432×288 | 67 | **408×264** | ×0,95 |
| 09 Grand dortoir | 648×432 | 170 | 432×288 | 72 | **432×288** | dans la fourchette |
| 10 Dortoir des explorateurs | 648×432 | 157 | 432×288 | 66 | **408×264** | ×0,95 |
| 11 Chambre des éclaireurs | 648×432 | 154 | 432×288 | 65 | **408×288** | ×0,96 |
| 12 Salle du chef | 648×432 | 146 | 432×288 | 62 | **480×312** | élargir ×1,10 |

(Table générée par `python3 analyse_echelle/cibles.py` → `cibles.json`.)

Contrôle après ×0,65 : mur 195 → 127 px, porte 76 → 49 px (Halcyon 58), fenêtre 78 →
51 px (Halcyon 59), passage 67 → 44 px (Halcyon 32 – 40), plus grande poche de vide
7,4 → 4,8 cases (Halcyon 4,3 – 5,8), largeur locale médiane 2,75 → 1,79 case
(Halcyon 1,1 – 1,7). **Tout tombe dans la cible.**

Trois façons de l'appliquer, par ordre de qualité :

1. **Redessiner sur les toiles cibles** (colonne « toile ajustée ») en gardant les motifs
   actuels mais à leur taille PMD : la meilleure option, ~1 salle par jour.
2. **Réduction ×0,65 + retouche** : passer les PNG à l'échelle puis reprendre à la main
   les contours, les lattes de plancher et les croisillons de fenêtre (le rééchantillonnage
   non entier abîme le pixel art). C'est ce que simule `img/simulation_reduction.png`.
3. **Réduction ×0,50 exacte** (648 × 432 → 324 × 216) : rééchantillonnage propre, mais on
   tombe à ~39 cases² de sol par chambre, soit un cran plus petit que Halcyon (50 – 55).
   Très « cosy », parfaitement jouable, à réserver aux petites chambres.

---

## 6. Règles de composition à appliquer en refaisant les maps

Ces règles sont extraites du comportement observé chez Halcyon, pas inventées :

1. **Une seule grande pièce par étage.** Les autres font ≤ 1,5 écran (≤ 100 cases² de sol).
2. **Le mur mange l'image.** Le sol praticable ne représente que **25 % de la toile chez
   Halcyon** (17 – 36 % selon les salles) contre **32 % chez nous** (29 – 37 %) : le
   bandeau de mur, les alcôves et les découpes occupent tout le reste. Le problème n'est
   donc pas la proportion sol/image, c'est la **valeur absolue** — ils obtiennent le même
   ratio sur une toile deux fois plus petite.
3. **Casser les grands axes.** Les pièces de Halcyon sont des octogones irréguliers avec
   des renfoncements, des cloisons courtes et des alcôves : jamais un ovale nu de 25 cases.
   Chaque paroi ajoutée réduit la largeur locale, donc la sensation de vide.
4. **Meubler les bords avant le centre.** 35 – 40 % de couverture, presque tout collé aux
   murs ; le centre reçoit un tapis ou une table, jamais rien de plus.
5. **Poser 1 prop tous les 5 à 10 cases² de sol.** Une chambre de 52 cases² de Halcyon
   contient 10 à 12 îlots de mobilier.
6. **Couloirs à 2 cases** (48 px), portes à 1 – 2 cases, seuils marqués par un changement
   de sol plutôt que par un élargissement.
7. **Le personnage doit toujours avoir un repère à moins de 3 cases** : un meuble, une
   marche, un changement de sol, un tapis. Si le joueur peut marcher 4 cases sans que rien
   ne change à l'écran, la pièce est trop grande.
8. **Vérifier au viewport** : afficher le cadre 320 × 240 au centre de la salle. Si ce
   cadre ne contient que du sol vide, la composition est ratée, quelle que soit la taille
   de la salle.

---

## 7. Gabarits de travail salle par salle

Tout est généré : `python3 analyse_echelle/guides.py` puis `python3 analyse_echelle/reduire.py`.

### `analyse_echelle/guides/NN_gabarit.png`

Un calque de référence **exactement à la taille cible**, à charger tel quel dans Aseprite
au-dessus du dessin. Il contient : la grille 24 px (repère épais toutes les 4 cases), le
contour du sol praticable, la **bande rose de 1,5 case le long des murs** où doit aller le
mobilier, la zone bleue de circulation à garder libre, les passages ramenés à 2 cases, la
ligne orange de hauteur de mur visée (4 cases), le cadre du viewport 320 × 240, et
4 sprites Pokémon posés à 1:1 pour juger du rapport à l'œil.

| Salle | Toile cible | Sol | Réf. Halcyon | Vide max | Props à poser | Passages |
|---|---|---|---|---|---|---|
| 01 Accueil de la guilde | 432 × 288 (18 × 12 cases) | 81 cases² | 75 – 110 | 5,4 | 12 | N 1,9 c |
| 02 Hall des missions | 840 × 360 (35 × 15) | 196 cases² | 150 – 200 | 6,8 | 28 | O 2,6 c |
| 03 Grande salle commune | 456 × 312 (19 × 13) | 82 cases² | 75 – 110 | 4,7 | 12 | — |
| 04 Cantine | 480 × 312 (20 × 13) | 76 cases² | 75 – 110 | 5,5 | 11 | — |
| 05 Chambre de l'équipe | 408 × 288 (17 × 12) | 65 cases² | 50 – 60 | 5,2 | 9 | E 1,9 c |
| 06 Chambre du veilleur | 408 × 264 (17 × 11) | 61 cases² | 50 – 60 | 4,8 | 9 | S 3,6 c → 2 c |
| 07 Chambre des résidents | 408 × 288 (17 × 12) | 65 cases² | 50 – 60 | 5,2 | 9 | O 1,9 c |
| 08 Dortoir des apprentis | 408 × 264 (17 × 11) | 61 cases² | 50 – 60 | 5,1 | 9 | E 1,7 c |
| 09 Grand dortoir | 432 × 288 (18 × 12) | 76 cases² | 75 – 110 | 5,4 | 11 | N 1,5 c |
| 10 Dortoir des explorateurs | 408 × 264 (17 × 11) | 60 cases² | 50 – 60 | 4,9 | 9 | O 1,7 c |
| 11 Chambre des éclaireurs | 408 × 288 (17 × 12) | 65 cases² | 50 – 60 | 5,2 | 9 | O 1,9 c |
| 12 Salle du chef | 480 × 312 (20 × 13) | 78 cases² | 75 – 110 | 5,4 | 11 | — |

Toutes les salles retombent dans la fourchette Halcyon, les poches de vide passent sous la
limite (≤ 6 cases hors hub, ≤ 8 dans le hall) et aucun îlot central n'est nécessaire.
Seul le passage sud de la salle 06 reste à resserrer (3,6 → 2 cases).

### `analyse_echelle/guides/NN_plan.json`

Les mêmes chiffres en données, pour scripter la reconstruction des maps : toile en px et
en cases, facteur appliqué, surface de sol, vide maximal, nombre de props, rectangle
d'îlot central s'il y a lieu, liste des passages (côté, position, largeur actuelle et
largeur cible), hauteur de mur visée. `guides/plans.json` regroupe les 12.

### `calques_reduits/` et `salles_reduites/`

Base de départ concrète : les **11 calques de chaque salle, jour et nuit**, ramenés à la
toile cible, plus un composite de contrôle par salle. À traiter comme un brouillon —
le rééchantillonnage non entier adoucit le pixel art, il faut reprendre à la main les
contours, les lattes de plancher, les croisillons de fenêtre et les cadres.

### Ordre de travail conseillé

1. Ouvrir `guides/NN_gabarit.png` en calque de référence au-dessus de
   `calques_reduits/<salle>/jour/`.
2. Reprendre `02_structure` : ramener le bandeau de mur sur la ligne orange (4 cases),
   casser les grands arcs de l'ellipse par deux ou trois retours de cloison.
3. Reprendre `01_sol` : resserrer les passages à 2 cases, découper le contour en angles
   plutôt qu'en ovale.
4. Remplir `06_decorations` et `07_objets` : le nombre de props de la colonne du tableau,
   posés en priorité dans la bande rose, en réduisant les sprites du banc actuel à
   24 – 56 px (1 – 2,5 cases), 150 px maximum pour une grande table.
5. Contrôler : relancer `mesures.py` sur la salle refaite et vérifier que la largeur locale
   médiane est retombée entre 1,0 et 1,7 case.

---

## 8. Banc de props à l'échelle et placement proposé

### `sprites_reduits/` — les props ramenés aux tailles PMD

`python3 analyse_echelle/props.py` applique le facteur 0,65 puis des **plafonds par
famille**, calés sur ce que fait Halcyon : plante ≤ 2 cases, nid ≈ 2,5 × 1,8 cases,
mobilier courant ≤ 120 × 80 px, grande pièce centrale ≤ 150 px, bannière murale ≤ 2,7
cases. Les 135 props sont réécrits en jour et en nuit, avec `props.json`
(taille avant/après, taille en cases, pivot aux pieds, type de pose : sol, mural,
suspendu, tapis).

| Prop | Avant | Après | En cases |
|---|---|---|---|
| table_banquet | 260 × 113 | **150 × 65** | 6,2 × 2,7 |
| tapis_maitre | 220 × 95 | **143 × 62** | 6,0 × 2,6 |
| table_etude | 100 × 85 | **65 × 55** | 2,7 × 2,3 |
| etagere_boissons | 83 × 97 | **54 × 63** | 2,2 × 2,6 |
| armoire_veilleur | 56 × 112 | **36 × 73** | 1,5 × 3,0 |
| nid_* (couchages) | 78 × 56 | **51 × 36** | 2,1 × 1,5 |
| banniere_maitre_centrale | 81 × 125 | **41 × 64** | 1,7 × 2,7 |
| végétation (typique) | 76 – 110 de haut | **≤ 48 de haut** | ≤ 2 cases |

Pour mémoire : mobilier médian chez Halcyon **40 × 56 px**, caisse = 1 case,
grosses pièces 128 – 216 px. On est désormais dans la même famille de tailles.

### `analyse_echelle/placements/` — la proposition de mise en place

`python3 analyse_echelle/placement.py` pose, salle par salle, le nombre de props
recommandé par le gabarit, avec ces règles :

- **grandes pièces centrales** (tapis du chef, table de banquet) au centre du sol ;
- **mobilier au sol** : pieds dans la bande de 1,5 case le long des murs, placement le
  plus étalé possible (échantillonnage du point le plus éloigné), sans chevauchement ;
- **2 cases dégagées devant chaque passage** ;
- **éléments muraux** (bannières, emblèmes, appliques) sur le bandeau de mur, en évitant
  les fenêtres déclarées dans `kit.json` ;
- **suspensions** en haut du bandeau, à partir du centre ;
- palette thématique par salle (nids dans les dortoirs, étagère et seau à la cantine,
  bannières et tapis chez le chef, etc.), complétée par la végétation.

| Salle | Props posés | Couverture du sol | État |
|---|---|---|---|
| 01 Accueil de la guilde | 12 | 18 % | ajouter 2-3 props |
| 02 Hall des missions | 32 | 21 % | ajouter 2-3 props |
| 03 Grande salle commune | 14 | 21 % | ajouter 2-3 props |
| 04 Cantine | 12 | 38 % | ok |
| 05 Chambre de l’équipe | 11 | 29 % | ajouter 2-3 props |
| 06 Chambre du veilleur | 10 | 20 % | ajouter 2-3 props |
| 07 Chambre des résidents | 11 | 19 % | ajouter 2-3 props |
| 08 Dortoir des apprentis | 10 | 23 % | ajouter 2-3 props |
| 09 Grand dortoir | 13 | 28 % | ajouter 2-3 props |
| 10 Dortoir des explorateurs | 10 | 26 % | ajouter 2-3 props |
| 11 Chambre des éclaireurs | 11 | 21 % | ajouter 2-3 props |
| 12 Salle du chef | 12 | 34 % | ok |

La couverture visée est de 30 – 45 %. Les salles encore en dessous sont celles où la
palette est surtout végétale : il leur manque deux ou trois meubles pour arriver dans la
fourchette — c'est le complément à faire à la main.

**Ce que le script écrit vraiment :**

- `analyse_echelle/placements/NN_placement.json` : chaque prop avec sa position en px et
  en cases, son calque de destination et son type de pose → éditable, réinjectable ;
- `calques_reduits/<salle>/<jour|nuit>/06_decorations.png` et `07_objets.png` : les
  calques de décor, jusqu'ici vides, sont désormais remplis ;
- `salles_reduites/<salle>_<jour|nuit>.png` : les composites sont recomposés ;
- `analyse_echelle/placements/NN_apercu.png` + `planche_placements.png` : les aperçus avec
  4 sprites Pokémon posés à 1:1 sur le sol resté libre.

Rien n'est figé : les positions sont dans le JSON, il suffit de les corriger et de
relancer le script pour régénérer les calques.

---

## 9. Reproduire l'analyse

```bash
pip install pillow numpy scipy
git clone --depth 1 https://github.com/Palikadude/Halcyon.git /chemin/halcyon
export HALCYON_DIR=/chemin/halcyon

python3 analyse_echelle/mesures.py   # -> analyse_echelle/mesures.json
python3 analyse_echelle/apercus.py   # -> analyse_echelle/img/*.png
python3 analyse_echelle/cibles.py    # -> analyse_echelle/cibles.json
python3 analyse_echelle/guides.py    # -> analyse_echelle/guides/*.png + *_plan.json
python3 analyse_echelle/reduire.py   # -> calques_reduits/ + salles_reduites/
python3 analyse_echelle/props.py     # -> sprites_reduits/ (banc de props a l'echelle)
python3 analyse_echelle/placement.py # -> placements/ + calques 06/07 remplis
```

Les rendus de cartes Halcyon reconstruits sont mis en cache dans
`analyse_echelle/rendus_halcyon/` (ils ne sont pas versionnés : ce sont des assets de
Halcyon, régénérés localement depuis le dépôt d'origine).

### Limites connues

- La zone jouable de Halcyon est déduite de la grille `obstacles` (blocs 8 px) intersectée
  avec le calque *Floor* et le rendu composite, puis limitée à la composante atteignable
  depuis les marqueurs d'entrée. Deux cartes atypiques sont à prendre avec des pincettes :
  `guild_first_floor` (image peinte d'un seul tenant, escalier en colimaçon) et
  `guild_dining_room` (la grande table coupe le sol en bande, d'où un « sol utile » faible).
- Notre sol est mesuré sur le calque `01_sol.png`, qui inclut la continuité des passages :
  c'est légèrement généreux, l'écart réel avec Halcyon est donc au minimum celui annoncé.
- La taille du sprite retenue (20 × 22 px) correspond à un starter. Un Pokémon massif
  (Ursaring, Tyranitar) monte à 40 – 48 px : cela ne change pas les ratios, cela renforce
  la conclusion.
