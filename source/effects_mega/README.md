# Méga-Évolution — 10 frames, orbite 2D/3D, symbole canonique

Livrable : [`effects/mega/`](../../effects/mega/)

- `Mega-Anim.png` : planche **800 × 768** — **10 frames × 8 directions**
  de 80 × 96 px (une ligne par direction, une colonne par frame) ;
- `Mega-<direction>.gif` : aperçu animé par direction.

## Les animations de Deeshura passées au générateur

Les frames de l'effet du mod `Deeshura/Mega_Stones` ont été **extraites de son
GIF** (frames 82 à 120, le pic de l'effet) et archivées dans
`ref/deeshura_effect_frames.png`. Cette planche a ensuite été **donnée au
générateur d'image comme référence de mise en scène**, avec consigne de
**changer les formes et les couleurs** :

| Deeshura | Ici |
| --- | --- |
| orbe blanc plat | éclats **cristallins facettés** |
| pics rouge et jaune agressifs | palette **froide** : violet, indigo, cyan, menthe, glace |
| colonnes jaunes | anneau de choc en **perspective** + fragments |

Résultat dans `gen/burst_ring.png`.

## Le symbole

`gen/emblem_fade.png` : le symbole Méga-Évolution en **double hélice d'ADN**,
aux **couleurs canoniques** (dégradé arc-en-ciel pastel rose → or → citron →
aqua → ciel → lilas).

Point important : la plaque générée fait 793 px de haut et le symbole doit en
faire 26. **Réduire directement aurait redonné la bouillie de la version
précédente.** Méthode retenue :

1. la plaque est réduite **une seule fois** pour en extraire la **silhouette** ;
2. cette silhouette 17 × 26 est **figée en dur dans le script** (constante
   `EMBLEM`, en art ASCII) ;
3. à partir de là, le symbole est **colorié pixel par pixel en natif** : bandes
   arc-en-ciel, reflet interne, contour sombre. Plus aucun redimensionnement.

**Taille accordée à l'animation** : 26 px de haut pour un sujet de 48 px, le
symbole tient dans le flash sans déborder du cadre ni écraser le Pokémon.

### Apparition et disparition subtiles

`emblem_strength(t)` est une courbe continue : rien à `t < 0.5`, montée douce,
plein au moment du flash, extinction sur la dernière frame.

Et surtout, tant que le Pokémon est visible, le symbole est dessiné **en
dither** (un pixel sur deux, sans contour) : il flotte dans l'air et **on voit
le Pokémon au travers**. Il ne devient plein que pendant le flash blanc.

## Rappel de la structure

**FLUIDE** : tout est fonction continue du temps normalisé `t`, aucune table
frame par frame, la boucle se referme sans raccord.

**3D** : deux anneaux inclinés contra-rotatifs, chaque particule portant une
profondeur `z = sin(angle)` ; `z < 0` derrière le sprite, `z > 0` devant.

## Couleurs

**44 couleurs**, dont une trentaine appartiennent aux paliers de fondu du
symbole. Contrôlé par script : **zéro couleur parasite**, chacune est soit dans
la palette du sprite, soit un palier de fondu déclaré.

Deux réglages faits pour ça : les fondus sont **quantifiés en 3 paliers** (un
fondu continu produisait 46 teintes), et les reflets sont des **teintes
nommées** par bande plutôt qu'un mélange calculé au tracé, qui générait une
vingtaine de couleurs intermédiaires.

## Reproduction

```bash
python source/effects_mega/build_mega.py
```

## Réserves honnêtes

- Effet **VFX**, pas une animation de personnage SpriteCollab : pas
  d'`AnimData.xml`, ni `-Offsets`, ni `-Shadow`.
- La silhouette du symbole vient d'une image générée, réduite une fois puis
  figée. Les **couleurs**, elles, sont écrites à la main dans le script.
- 44 couleurs, c'est **au-dessus du budget SpriteCollab** (15). Acceptable pour
  un VFX de jeu, à réduire si tu veux viser une soumission.
- Aucun test moteur PMDO.
