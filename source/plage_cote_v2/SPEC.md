# SPEC — Plage « côté mer en bas », deux layouts (lot `plage_cote_v2`)

Fiche de composition écrite **avant** l'assemblage et **avant** les images de
guide, conformément à `METHODE_PRODUCTION_MAPS.md`. Deux nouveaux layouts de
la crique de Beach Cave, **plus grands que la source**, grotte **du même côté
(gauche)** que le lot livré `plage_beach_cave_v1`, et **la mer de l'autre
côté** : en bas de carte — seule position de mer canonique possible avec les
cellules de `Brine_Cave_Entrance` (la mer de la plage D01P11A n'existe qu'en
haut de carte ; la mettre en bas exigerait une rotation, interdite).

## 1. Fonction (commune aux deux layouts)

Zone extérieure de transition, jouable en Ground PMDO 0.8.12 :

- le joueur **arrive par la droite** (marqueur `Entrance` dans le couloir de
  sortie, direction ouest) ;
- il traverse le **grand sol de grès** de la crique (zone libre) ;
- le **seuil de donjon** est l'**embouchure de la grotte, à gauche**
  (déclencheur `Beach_Cave_Entrance` copié du lot v1, posé sur l'arche) ;
- la **sortie** est le bord droit (déclencheur `Exit` sur le couloir) ;
- la **mer occupe le bas** de la carte : rive d'écume horizontale, mer
  profonde infranchissable, et la **diagonale rocheuse bas-gauche** de la
  source (caractère de la crique, conservé d'un bloc).

Raccords à prévoir dans le projet cible : `Exit_Touch` et
`Beach_Cave_Entrance_Touch` (squelette Lua fourni, appels en commentaire) ;
comportement de référence : `init.lua` de la plage EoSO.

## 2. Matière (commune)

Uniquement les cellules canoniques de `Brine_Cave_Entrance` telles que livrées
par Explorers of Sky Origins (PMD Sky, commit épinglé `bed94499`) :

| Calque PMDO | Feuille source | Feuille livrée | Contenu |
|---|---|---|---|
| unique (« New Layer » → « Back ») | `Brine Cave Entrance` | `PLAGE_CV2_BRINE` | mur, sol, rebord, rive, mer — flipbooks de 15 frames, `FrameLength` 8 (≈ 133 ms, cycle 2 s) |

La feuille livrée est une **copie octet pour octet** de la feuille EoSO
(renommée pour éviter toute collision dans PMDO). Chaque cellule de la carte
copie la **séquence complète des 15 frames** d'une cellule source : l'animation
de l'eau est canonique par construction. Aucune cellule n'est recolorée,
tournée, redimensionnée ni redessinée. Mesures justifiant chaque recollement :
`ANALYSE.md` / `analyse.json`.

## 3. Extension : en largeur uniquement, module [19..27)

L'agrandissement est **horizontal** (toutes les adjacences verticales restent
exactement celles de la source — aucune rangée insérée, hauteur 21) :

- **Crique** : base [0..19) + module [19..27) ×2 = **35 × 21 cellules
  (840 × 504 px)** ;
- **Grande anse** : module ×3 = **43 × 21 cellules (1032 × 504 px)**.

La boucle 26 → 19 respecte la phase du mur (période 4 : jonction
pixel-parfaite 135,4 = valeur native) et du sol (113,0) ; la mer (période 3,
incompatible avec 4 — ANALYSE §4) prend un saut de phase borné et documenté
sur les rangées 16-18 de chaque jonction intérieure (max 3236,3 sur la
couronne d'écume ; l'eau reste 100 % cellules natives animées).

**Couloirs traversants** : les colonnes de fin de module (25-26, mur/rocher
côtier dans la source) sont ouvertes aux rangées 12-13 avec le sol nu copié
de (24,12)/(24,13) — sinon chaque copie du module serait une bande fermée.
Un couloir de 2 cellules de haut traverse donc chaque jonction et aboutit à
la sortie ; les rangées 11 et 14 gardent le cadre rocheux.

## 4. Bords de carte

- **Nord** : mur de grotte jusqu'au bord.
- **Ouest** : mur, puis la diagonale du rebord et la mer en bas-gauche
  (d'un bloc, non modifiés).
- **Sud** : mer profonde jusqu'au bord (bloquée, animée).
- **Est** : mur en haut, **couloir de sortie** (rangées 12-13) entre les
  bandes rocheuses, marqué `Entrance`/`Exit` ; mer en bas.

## 5. Ordre de profondeur (du fond vers l'avant)

1. Mur de grotte (haut et flancs), embouchure à gauche sur le mur du haut ;
2. rebord rocheux diagonal côté ouest (statique) ;
3. sol de grès praticable (centre-droit), couloirs de sortie à l'est ;
4. rive d'écume (animée à gauche, statique côté plage — état canonique) ;
5. mer profonde animée jusqu'au bord sud.

## 6. Entités

| Entité | Type | Crique (px) | Anse (px) | Rôle |
|---|---|---|---|---|
| `Entrance` | marqueur, direction 2 (ouest) | 820, 292 | 1004, 292 | arrivée dans le couloir (avant-dernière colonne) |
| `Exit` | GroundObject, `triggerType` 2 (contact) | 832, 288, 16 × 48 | 1016, 288, 16 × 48 | sortie bord droit, couloir rangées 12-13 |
| `Beach_Cave_Entrance` | GroundObject, `triggerType` 2 | 216, 144, 72 × 48 | idem | seuil du donjon, arche de la grotte |

Pas de PNJ ni de spawner. Formes JSON copiées des entités de la plage EoSO.

## 7. Garde-fous

- Les images générées servent uniquement de **guide de composition** ; elles
  portent la mention « guide de composition (généré) — aucune tuile n'en
  provient » et ne sont jamais découpées en tuiles.
- Assemblage intégralement décrit par `layout.py` (une correspondance cellule
  source par cellule de carte, journalisée dans `cell_mapping.json`) ;
  vérification octet par octet, coutures, accessibilité dans `verify.py` ;
  chargement natif 0.8.12 des deux grounds dans `runtime_test.py`.
- Hors périmètre : PNJ, spawners, variante nuit, musique additionnelle
  (`Music` conserve la valeur source « Brine Cave.ogg »).
