# ANALYSE — structure de la plage EoSO et mesures de raccord

Mesures produites par `analyse.py` (→ `analyse.json`) sur la carte
`Data/Ground/beach.rsground` d'Explorers of Sky Origins, commit
`bed944992c32e7e7927cc3480c72edb0b1782e26`. « Raccord » = MSE (RGB 0–255)
entre la dernière ligne/colonne de pixels d'une cellule et la première de la
cellule voisine, sur les 17 frames du composite sauf mention contraire.

## 1. Structure de la carte d'origine (33 × 16 cellules de 24 px)

| Calque | Feuille | Cellules | Contenu |
|---|---|---|---|
| `Back` | `D01P11A_layer1` (528 cellules, 218 images distinctes) | 528, statiques (`FrameLength` 10, 1 frame) | rangées 0–6 mer statique de fond (sous la mer animée), rangée 6 sable mouillé, rangées 7–11 sable, rangées 12–15 et colonnes 0–2/32 remplissage bleu hors champ ; **ombres cuites** des détails (cailloux, buisson, rochers) |
| `Anim` | `beach_animation` (561 × 7 cellules = 17 frames × 33 × 7) | 231, chacune 17 frames, `FrameLength` 16 | mer, écume, rochers côtiers cuits dans la bande ; frame f de la cellule (x, y) = TexLoc (33·f + x, y) |
| `Front` | `D01P11A_layer2` (298 cellules, 182 images distinctes) | 298, statiques | falaises, grotte (rangées 6–7, colonnes 2–3), rampe de gravier (colonnes 2–4, rangées 7–9), chemin de sortie (colonnes 30–32, rangées 7–11, en Front), rochers, palmiers, herbe, détails |

- Animation : 17 frames composites toutes distinctes ; rangées 0–2 immobiles
  d'une frame à l'autre (mer lointaine), rangées 3–6 animées ; 16 ticks par
  frame à 60 Hz = 266,7 ms, cycle ≈ 4,53 s.
- Obstacles : grille 99 × 48 de 8 px ; 948 cases libres (sable, rampe,
  bouche de la grotte, couloir de sortie y 176–239 au bord droit).
- Entités : marqueurs `Entrance` (748, 208, direction 2) et
  `CutsceneEntranceA` ; objets `Exit` (782, 172, 16 × 78) et
  `Beach_Cave_Entrance` (8, 144, 64 × 64), tous deux `triggerType` 2 ; trois
  spawners de cinématique hors carte.

## 2. Largeur : quel bloc de colonnes répéter ?

Raccords existants entre colonnes voisines : médiane **318**, maximum 924.
Raccord de boucle d'un bloc `[a, b)` = raccord entre la colonne b−1 et la
colonne a (ce qui apparaît quand on insère le bloc après lui-même).

| Bloc | Largeur | Raccord de boucle |
|---|---|---|
| **[11, 23)** | **12** | **203,7** |
| [10, 22) | 12 | 326,4 |
| [12, 24) | 12 | 452,3 |
| [11, 19) | 8 | 1181,4 |
| [12, 20) | 8 | 1226,4 |
| [9, 25) | 16 | > 1600 |

Le bloc [11, 23) raccorde mieux que la médiane des colonnes d'origine. Le
module de rochers du bas coupé à la colonne 22 (« 0, 4, 2 ») se termine par
la colonne 11 (« 3 »), sa suite naturelle. Les rangées 3 et 4 de la mer ont
une période horizontale de 2 et 4 cellules ; les rangées 1, 2, 5, 6 n'ont
pas de période (la rangée 6 a 33 cellules distinctes) : un bloc contigu
est préférable à toute recomposition colonne par colonne.

## 3. Hauteur : quelles rangées de sable répéter ?

Raccords du calque `Back` seul, colonnes 5–27 (rangée du haut → rangée du bas) :

| ↓ sur → | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|
| 6 | 3034 | **130** | 1884 | 1885 | 2000 | 1631 | 15154 |
| 7 | 5036 | 1765 | **107** | 276 | 327 | 506 | 16798 |
| 8 | 5483 | 1977 | 134 | **12** | 80 | 312 | 16911 |
| 9 | 5503 | 2089 | 186 | **92** | **23** | 350 | 17020 |
| 10 | 4968 | 1731 | 372 | 292 | 321 | **20** | 16656 |
| 11 | 3652 | 1300 | 471 | 456 | 515 | 496 | 16174 |

Séquences candidates (rangée 7 en haut, 10–11 en bas, six rangées au milieu) :

| Séquence | Raccords | Max |
|---|---|---|
| origine 7, 8, 9, 10, 11 | 107 · 12 · 23 · 20 | 107 |
| **choisie 7, 8, 9, 9, 9, 9, 9, 10, 11** | 107 · 12 · 92 · 92 · 92 · 92 · 23 · 20 | **107** |
| alternance 7, 8, 9, 8, 9, 8, 9, 10, 11 | 107 · 12 · 186 · 12 · 186 · 12 · 23 · 20 | 186 |
| rangée 8 répétée 7, 8, 8, 8, 8, 8, 9, 10, 11 | 107 · 134 · 134 · 134 · 134 · 12 · 23 · 20 | 134 |

La séquence choisie ne crée aucun raccord pire que le raccord 7 → 8 déjà
présent dans la carte. À l'écran (zoom 2× et 3×), l'alternance 8/9 montre des
marches sur la bande claire du chemin de droite ; la répétition de la rangée 8
montre le même défaut. La rangée 9 répétée donne des bords rectilignes.

Colonnes latérales (mur, rampe, chemin), raccord d'une cellule avec elle-même
(RGBA, alpha compris, calque `Front`) :

| Colonne | 8 sur 8 | 9 sur 9 | Choix |
|---|---|---|---|
| 3 (rampe) | **1231** | 10994 | rangée 8 répétée, rangée 9 en dernier |
| 4 (bord de rampe) | 19205 | 17733 | idem (bord diagonal dans les deux cas) |
| 30 (bord du chemin) | 30818 | **16762** | rangée 9 répétée |
| 31 (chemin) | 745 | **539** | idem |

Dans ces colonnes le calque `Back` suit la même séquence que `Front` : le
sable visible sous le bord de la rampe (Front couvrant 71 % / 19 %) et sous
le bord du chemin (31 % / 78 %) garde sa cellule Front d'origine.

## 4. Ombres cuites et détails

Le calque `Back` contient l'ombre de chaque détail posé en `Front` : caillou
(18, 9) → ombre dans Back (18, 9) + (19, 9) ; paire (12–13, 7) → Back
(12, 7) + (13, 7). Le motif de sable a une période de 8 colonnes (rangée 9 :
60 % des cellules identiques à 8 colonnes de distance, rangée 10 : 53 %), et
les cellules propres de même phase sont identiques : (10, 9) = (26, 9),
(11, 9) = (27, 9). Règle appliquée : un détail se déplace **avec** ses
cellules d'ombre, uniquement vers une cellule de même rangée d'origine et de
même colonne modulo 8 ; une ombre orpheline est remplacée par la cellule
propre de même phase. `verify.py` contrôle ces phases et mesure tous les
nouveaux voisinages (calque par calque) : maximum Back 1430 (horizontal,
bord de l'insertion en rangée 5, contre 13072 dans l'origine), Anim 326
(contre 5763), Front 19205 (bord de rampe répété, contre 22818).

## 5. Ce qui a été écarté

- Alternance 8/9 des rangées de sable (marches visibles).
- Blocs de 8 ou 16 colonnes (raccords ≥ 1181).
- Déplacement de détails sans leurs cellules d'ombre (taches orphelines
  constatées au premier rendu, corrigées).
- Variante `dusk_beach` : flipbook de toute la carte (27 frames, bulles
  cuites) ; toute insertion dupliquerait les bulles.
