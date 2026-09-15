# Mega Raichu X et Y — packs PMD / SpriteCollab complets

Livrables :

| Forme | Dossier | Archive | Aperçus |
| --- | --- | --- | --- |
| **Mega X** (orange, éclairs jaunes) | [`sprite/0026_mega_x/`](../../sprite/0026_mega_x/) | `sprite-0026-mega-x.zip` | `gifs/0026_mega_x/` |
| **Mega Y** (bleu orage, éclairs cyan) | [`sprite/0026_mega_y/`](../../sprite/0026_mega_y/) | `sprite-0026-mega-y.zip` | `gifs/0026_mega_y/` |

Aperçu animé des deux formes : `apercus/mega_raichu_xy_showcase.gif`.
107 fichiers et 114 GIFs par forme. Import PMDO : **Char Sprites > Import**.

## Conformité au PMD Sprite Guide

Critères tirés du guide d'Emmuffin, tous vérifiés par script :

| Critère du guide | État |
| --- | --- |
| ≤ 15 couleurs + 1 transparence sur **tout** le jeu de feuilles | **14 couleurs** par forme |
| Tailles de frame **multiples de 8** | **oui, les 35** |
| Feuilles à **1 ou 8 lignes** | oui |
| **Animations donjon** (0,1,5,6,7,8,9,10,11,12) | **10/10** → statut « Existing » |
| **Animations starter** (13–34) | **22/22** → statut « Fully Featured » |
| Format **multi sheet** (`-Anim`, `-Offsets`, `-Shadow`, `AnimData.xml`) | oui, format attendu par SpriteBot |
| Marqueurs offsets : noir tête, vert corps, rouge main D, bleu main G | respectés |
| Transparence binaire | oui |

**35 animations × 1275 frames par forme**, aucune `CopyOf`.

Correction majeure de cette passe : la version précédente produisait des frames
en 64 × 68, 96 × 92… — **aucune n'était multiple de 8**, contrairement à ce
qu'exige le guide. Toutes les dimensions sont désormais arrondies au multiple
de 8 supérieur, en conservant les pieds sur le bord bas du cadre.

## Méthode

Le mouvement vient du jeu d'animations canonique de **Raichu #0026** : pattes,
queue et oreilles s'animent réellement, avec vraies poses, vraies durées et
vrais marqueurs. Pour chaque forme :

1. **Recoloration par rôle** — contour, trois tons de fourrure, ventre, tons
   d'éclair, bouche. La table est écrite explicitement parce que les palettes
   ne partagent aucune couleur et que leurs ordres de luminance divergent : un
   classement automatique aurait envoyé de la fourrure dans les éclairs.
2. **Élargissement** de chaque frame au multiple de 8 supérieur, pour loger
   l'envergure. Les marqueurs sont décalés d'autant afin de continuer à
   désigner les mêmes parties du corps.
3. **Greffe des ailes** sur les 1275 frames, ancrée sur le **marqueur de tête**
   de la feuille `-Offsets`. Comme ce marqueur suit le crâne, les ailes suivent
   l'animation au lieu de flotter. La forme d'aile dépend de la direction
   (face, trois-quarts, profil, dos) pour un raccourci correct, et elles sont
   peintes **derrière le corps** pour garder la tête lisible.

### Les deux formes

**X** reprend la palette chaude de ton artwork (commit `a214a07`).
**Y** est le pendant orage : fourrure bleu nuit, ventre bleu clair, éclairs
blanc-cyan. Son design a été produit au générateur d'image
(`gen/mega_y_front.png`), puis **sa palette a été réécrite à la main par
rôle** : la quantification automatique de la plaque laissait des résidus de
clé magenta et des violets parasites.

Le vérificateur contrôle que **les palettes X et Y ne partagent aucune
couleur**.

## Contrôle

```bash
python source/sprites_mega_raichu/build_megas.py
python source/sprites_mega_raichu/verify_megas.py
```

## Réserves honnêtes

- Les ailes sont une **forme statique par direction**, ancrée sur la tête :
  elles suivent le corps mais **ne battent pas**. Une vraie animation d'ailes
  demanderait un dessin par frame, soit 1275 dessins par forme.
- Les **yeux** des designs Mega ne sont pas rendus : le canonique n'a pas de
  pixel d'œil isolable sans retoucher le visage à la main.
- Les dossiers sont nommés `0026_mega_x` / `0026_mega_y` et non
  `sprite/0026/0002` et `0003` : en amont, `Mega_X` a été échangé avec
  `Altcolor` (commit `e50bbab4`) et `sprite/0026/0002` **n'existe pas** (404).
- **Aucun test moteur PMDO ou SkyTemple n'a été effectué.** Le guide recommande
  de tester via PMDO avant soumission.

## Crédits

Design Mega Raichu X : `meromoonmeri` (commit `a214a07`).
Jeu d'animations Raichu #0026 : contributeurs SpriteCollab, CC BY-NC 4.0.
Design Mega Y, recoloration, ailes et assemblage : `Arena.ai Agent`.
