# Animation d'effet — Méga-Évolution (réécriture complète)

Livrable : [`effects/mega/`](../../effects/mega/)

- `Mega-Anim.png` : planche **1920 × 768** — **24 frames × 8 directions**
  de 80 × 96 px (une ligne par direction, une colonne par frame) ;
- `Mega-<direction>.gif` : un aperçu animé par direction.

Ordre des lignes : `down, down-right, right, up-right, up, up-left, left,
down-left`.

## Pourquoi la version précédente a été jetée

Elle était ratée, et pour une raison précise : **je faisais générer des images
de ~1500 px puis je les réduisais à 40–70 px.** Du pixel art réduit n'est plus
du pixel art — les arêtes deviennent molles, les couleurs bavent, le nombre de
teintes explose. Trois conséquences visibles :

1. un **arc-en-ciel saturé** étranger à toute palette PMD, qui faisait sticker
   posé sur l'image ;
2. des **colonnes de foudre verticales** qui formaient un rideau et mangeaient
   tout le cadre ;
3. **cinq éléments empilés** en même temps — plus rien n'était lisible, et
   l'effet écrasait le Pokémon au lieu de le servir.

## Ce qui change, à la racine

- **Tout est dessiné nativement en 80 × 96, pixel par pixel.** Aucun
  redimensionnement nulle part : les arêtes sont dures par construction.
  Plus aucune plaque générée par IA n'entre dans le rendu.
- **La palette est extraite du sprite du sujet lui-même** (14 teintes issues de
  Terapagos Stellaire). L'effet appartient au Pokémon au lieu de lui être
  plaqué dessus. **13 couleurs** dans le rendu final.
- **Vocabulaire PMD classique** : anneaux, particules convergentes, flaque de
  lumière au sol. Pas de barres verticales.
- **Sobriété** : deux idées maximum à l'écran. Le Pokémon reste lisible en
  permanence, **sauf pendant les 3 frames de flash** — un choix assumé, c'est
  le pic de l'animation.

## Les 5 phases

| Frames | Phase | Contenu |
| --- | --- | --- |
| 0–5 | **rassemblement** | des particules spiralent vers l'intérieur, la flaque s'ouvre aux pieds |
| 6–10 | **resserrement** | deux anneaux se referment sur le Pokémon |
| 11–13 | **flash** | voile blanc net, seul moment où le sprite est masqué |
| 14–18 | **émergence** | l'onde de choc s'écarte en s'éteignant, éclats radiaux |
| 19–23 | **retombée** | la flaque faiblit, les dernières particules se dispersent |

Correction appliquée après contrôle : l'onde de choc débordait du cadre et se
découpait en **arcs brisés** — ça se lisait comme un bug. L'onde est désormais
**plafonnée à 36 px de rayon** (le demi-cadre fait 40) et s'assombrit
progressivement au lieu de sortir de l'image.

## Multidirectionnel

Chaque ligne utilise l'artwork propre du sujet pour cette direction, pris dans
sa feuille `Idle`. Les effets sont radiaux et symétriques : ils restent justes
sous les huit angles.

## Sujet

Par défaut Terapagos forme Stellaire. Pour un autre Pokémon, changer
`SPRITE_SHEET`, `SUBJECT_W` et `SUBJECT_H` en tête du script — la palette, elle,
mérite d'être réextraite du nouveau sprite.

## Reproduction

```bash
python source/effects_mega/build_mega.py
```

## Réserves honnêtes

- C'est une **animation d'effet VFX**, pas une animation de personnage
  SpriteCollab : pas d'entrée `AnimData.xml`, pas de `-Offsets` ni `-Shadow`.
- **Il n'y a pas de symbole Méga-Évolution dans cette version.** Le dessiner
  lisiblement en pixel art natif à cette taille est un travail à part entière ;
  la version précédente ne « marchait » que parce qu'elle réduisait une grande
  image, ce qui était précisément le défaut. À faire proprement si tu le veux.
- Aucun test moteur PMDO n'a été effectué.
