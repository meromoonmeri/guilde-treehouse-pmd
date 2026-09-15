# Animation d'effet — Méga-Évolution, multidirectionnelle

Livrable : [`effects/mega_evolution/`](../../effects/mega_evolution/)

- `MegaEvolution-Anim.png` : planche **1280 × 768**, soit
  **16 frames × 8 directions** de 80 × 96 px ;
  une **ligne par direction**, une **colonne par frame** ;
- `MegaEvolution-<direction>.gif` : un aperçu animé pour chacune des
  8 directions.

Ordre des lignes, conforme au format PMD :
`down, down-right, right, up-right, up, up-left, left, down-left`.

## Art généré, puis transformé en sprite

Les trois éléments de l'effet sont **produits par le générateur d'image**, sur
clé magenta pure, en vrai pixel art. Ils sont archivés dans `gen/` :

| Fichier | Contenu |
| --- | --- |
| `gen/sphere_stages.png` | 6 stades de croissance de la sphère arc-en-ciel opaque |
| `gen/mega_emblem.png` | le symbole Méga-Évolution, double hélice d'ADN |
| `gen/lightning_columns.png` | 4 variantes de grosses colonnes de foudre |

Chaîne appliquée ensuite par `build_mega_animation.py` :

1. **détourage exact** de la clé magenta, alpha binaire ;
2. **recadrage** sur le contenu utile ;
3. **mise à l'échelle en NEAREST** uniquement, pour garder les arêtes dures ;
4. **composition** par-dessus le sprite du sujet, pour les 8 directions ;
5. **verrouillage de palette** : chaque pixel est ramené sur une palette
   d'effet écrite à la main. **12 couleurs** utilisées, transparence binaire.

Le symbole a été vérifié avant génération : c'est bien la **double hélice
d'ADN** du logo Méga-Évolution, pas une forme inventée.

## Déroulé

1. **frames 0–2** : les colonnes de foudre s'abattent, le Pokémon est visible ;
2. **frames 2–7** : la sphère arc-en-ciel **opaque** grandit et l'engloutit ;
3. **frames 6–13** : le symbole brûle devant la sphère ;
4. **frames 13–15** : la sphère s'effondre, le Pokémon réapparaît.

## Multidirectionnel

Chaque ligne utilise **l'artwork propre du sujet pour cette direction**, pris
dans sa feuille `Idle`. Le Pokémon regarde donc dans le bon sens dans les huit
lignes, pendant que l'effet l'engloutit.

Correction appliquée après contrôle visuel : les colonnes étaient d'abord trop
larges et masquaient le sujet. Elles sont désormais **étroites et placées dans
des couloirs qui longent les bords**, le centre reste dégagé.

## Sujet

Par défaut Terapagos forme Stellaire. Pour un autre Pokémon, changer
`SPRITE_SHEET`, `SUBJECT_W` et `SUBJECT_H` en tête du script.

## Reproduction

```bash
python source/effects_mega_evolution/build_mega_animation.py
```

## Réserves honnêtes

- C'est une **animation d'effet VFX**, pas une animation de personnage
  SpriteCollab : pas d'entrée `AnimData.xml`, pas de `-Offsets` ni `-Shadow`.
  SpriteCollab n'a pas de slot pour ce type d'effet.
- Les pixels de l'effet viennent du générateur d'image, contrairement aux lots
  sprite/portrait livrés précédemment. C'est ce qui a été demandé ici, mais
  cela signifie qu'ils ne sont **pas issus d'une source canonique**.
- Aucun test moteur n'a été effectué.
