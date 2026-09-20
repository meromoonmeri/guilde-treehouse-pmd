# ANALYSE — source `Brine_Cave_Entrance` (EoSO `bed94499`)

Mesures faites sur le rendu composite de la carte source (27 × 21 cellules de
24 px, **1 calque** « New Layer », **chaque cellule = flipbook de 15 frames**,
`FrameLength` 8 ticks ≈ 133 ms, feuille unique `Brine Cave Entrance`).
Scripts : `analyse.py` → `analyse.json`, `analyse2.py` → `analyse2.json`
(les mesures de ce fichier prévalent : `analyse2.py` mesurait la similarité
de strips, pas les coutures d'adjacence — voir §3). « Couture » = MSE
RGB 0-255 entre la dernière colonne (rangée) de pixels d'un bloc et la
première colonne (rangée) du bloc suivant, toutes frames confondues.

## 1. Géographie de la source (carte obstacles + rendu)

```
x→  0         1         2
    0123456789012345678901234566
 0  ###########################
 5  #########+++###############   embouchure (libre) : x 9-11, y 5-6
 8  ######+.......+############   arche de la grotte : x ≈ 8-12, y 3-6
12  #######+.................+#   sol principal : x 8-24, y 8-15
16  ##############++#++#++#++##   rive d'écume horizontale : y 16
17  ###########################   mer profonde : y 17-20 (bloquée)
20  ###########################
```

- **Mer en bas** : diagonale bas-gauche (rive rocheuse qui descend de (0,6) à
  (7,16)) + **rive horizontale** en rangée 16 (x 13-26), mer profonde rangées
  17-20 sur toute la largeur.
- **Embouchure de la grotte** : colonnes 9-11 (arche 8-12), rangées 3-6 —
  déjà sur la moitié gauche.
- Sol de caverne (grès) : x 8-24, y 8-15 ; rebord rocheux colonnes 2-8 ;
  alcôves décoratives dans le mur droit (x 20-21, y 11-12) ; rochers posés
  (15,15), (21,15), (24,15).
- Aucune entité (marqueurs, objets, spawners tous vides) ; obstacles 81×63
  (Tags 0/1) ; `Music` = « Brine Cave.ogg ».

## 2. Animation

- 567 cellules : **387 statiques** (1 payload répété 15×) et **180 animées** ;
  rangées 0-5 entièrement statiques (mur), aucune colonne entièrement
  statique ; la mer est animée sur tout son domaine (17-20), la rive 16 ne
  l'est qu'à gauche de x 13 (trainées d'eau) — état canonique.
- **Flipbook horizontal** : la frame k de la cellule (x, y) est le payload de
  la feuille en (x + 27k, y) — vérifié (pas de 27). Copier une cellule
  (séquence de TexLoc) vers une feuille copie octet pour octet conserve donc
  exactement l'animation.
- 257 flipbooks distincts pour 567 cellules (forte réutilisation naturelle).

## 3. Coutures natives (références)

- horizontales (par cellule, toutes paires x|x+1) : max **750,7** ;
- verticales (toutes paires y|y+1) : max **513,0** par cellule ;
- par bande (colonnes 13-26) : mur (y 0-11) max **192,2** ; sol (y 12-15)
  max **211,5** ; mer (y 16-20) max **63,2**.

## 4. Périodes : ce qui est exact, ce qui est impossible

Familles **pixel-parfaites** de colonnes (similarité de strips MSE 0,0) :

- mur (y 0-11) : période **4** — 17≡21≡25, 18≡22≡26, 19≡23, 20≡24 ;
- mer + rive (y 16-20) : période **3** — {14,17,20,23,26}, {15,18,21,24},
  {16,19,22,25}.

Conséquence (démontrée par mesure) : une boucle de bloc non native ne peut
pas être parfaite à la fois sur le mur (4) et sur la mer (3) — 4 et 3 sont
premiers entre eux, tout pas de rotation k≠0,4×t sur le mur est un saut de
3k mod 12 sur la mer. La boucle théorique « parfaite sur les deux » exigerait
un multiple commun (12 colonnes, [15..27), boucle 26|15) : elle coûte alors
mur 1175,6 / sol 667,0 (la phase du sol, période 8, saute aussi).

**Décision** : privilégier mur + sol parfaits (structures statiques), assumer
un saut de phase **documenté et borné** sur l'eau animée.

## 5. Extension en largeur : module [19..27), boucle 26 → 19

| Bande | Boucle 26|19 | Référence native |
|---|---|---|
| Mur y 0-11 | **135,4** | 18|19 = 135,4 (pixel-parfait, phase 4 respectée) |
| Sol y 12-15 | **113,0** | natif 18|19 = 24,0 ; max natif 211,5 |
| Mer y 16-20 | saut de phase | voir ci-dessous |

Saut de phase mer de la jonction 26|19, par cellule (max source = 750,7) :
rangée 16 : 1138,7 ; 17 : 1322,7 ; **18 : 3236,3** (couronne d'écume décalée
d'une période) ; 19 : 403,7 ; 20 : 584,2. Ce coût, concentré sur la couronne,
est celui d'une phase différente de la même eau — jamais un défaut de pixels.

Candidats mesurés et écartés : boucle 25|17 (module [17..26)) : mur
2233,8-3630 par cellule (périodes 3 et 4 incompatibles) ; boucle 25|18
([18..26)) : mer 2395-3524 ET mur 186 (variante acceptable, mer pire) ;
[15..27) : sol 667 ; [14..26) : mur 2044,6.

**Dimensions** : base [0..19) + module ×2 = **35 colonnes** (crique) ;
×3 = **43 colonnes** (anse). Hauteur inchangée : **21 rangées** — toutes les
adjacences verticales restent exactement celles de la source (la duplication
de rangées de mur, testée à l'étude initiale, est abandonnée : la couture
d'adjacence 3|3 coûte 7593,3 et la similarité de strips ne garantit pas les
jonctions).

## 6. Couloirs traversants (obligatoires)

La fin de chaque copie du module est le **bord droit de la source** : mur en
26, rocher mixte en 25 dont la sous-colonne droite (8 px) est bloquée. Sans
ouverture, chaque copie serait une bande fermée (défaut trouvé par le test
d'accessibilité de `verify.py`). Les colonnes de carte d'origine source 25 et
26 reçoivent donc, **à chaque apparition**, aux rangées 12-13, le sol nu copié
de (24,12)/(24,13) (cellules natives, obstacles libres) : un couloir de 2
cellules de haut traverse chaque jonction et sort à droite. Les rangées 11 et
14 gardent le cadre rocheux. Coût de raccord mesuré : 16,0 / 16,7 (rangées
12-13, sol nu contre sol) — quasi nul.

## 7. Déplacer l'embouchure vers la gauche : mesuré, rejeté

Recoller le mur directement après la colonne 8 casse le rebord et la
diagonale sous le mur : jonctions 4→8 : 2875-7617 selon la bande ; 5→8 :
2019-7449 ; 3→8 : 2850-8539. L'embouchure reste à sa place canonique
(x 9-11), soit la moitié gauche de la carte (54 % en crique, 44 % en anse).
