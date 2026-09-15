# Animation d'effet — Méga-Évolution, multidirectionnelle

Livrable : [`effects/mega_evolution/`](../../effects/mega_evolution/)

- `MegaEvolution-Anim.png` : planche **1920 × 768**, soit
  **24 frames × 8 directions** de 80 × 96 px
  (une ligne par direction, une colonne par frame) ;
- `MegaEvolution-<direction>.gif` : un aperçu animé par direction.

Ordre des lignes, conforme au format PMD :
`down, down-right, right, up-right, up, up-left, left, down-left`.

## Référence étudiée

Le mod PMDO **`Deeshura/Mega_Stones`** (GIF d'aperçu du dépôt). Sa mise en
scène est juste mais volontairement minimale :

1. une **sphère blanche unie** grossit sur le Pokémon ;
2. elle éclate en une **étoile radiale** rouge et blanche ;
3. quelques **colonnes jaunes** tombent ;
4. le Pokémon réapparaît, changé.

Ce qui lui manque, et que cette version apporte :

| Référence | Ici |
| --- | --- |
| sphère blanche unie | sphère **arc-en-ciel opaque** à 6 stades |
| aucun symbole | le **symbole Méga-Évolution** (double hélice d'ADN) qui pulse |
| pas de phase de charge | **flaque de lumière au sol** + **éclats convergents** |
| colonnes fines et rares | **grosses colonnes de foudre** échelonnées |
| une seule direction | **8 directions** |
| ~10 frames utiles | **24 frames** en 6 actes |

Le but n'était pas de copier le rythme mais de le dépasser.

## Les 6 actes

| Frames | Acte | Contenu |
| --- | --- | --- |
| 0–4 | **charge** | une flaque de lumière s'ouvre aux pieds, des éclats d'énergie convergent |
| 4–6 | **implosion** | les éclats percutent, la flaque s'embrase |
| 5–10 | **engloutissement** | la sphère arc-en-ciel **opaque** grandit et masque le sprite |
| 8–16 | **sigil** | le symbole d'ADN brûle devant la sphère, en pulsant |
| 16–21 | **détonation** | l'onde de choc en étoile explose, la foudre redouble |
| 20–23 | **retombée** | tout reflue, le Pokémon réapparaît éclairé par la flaque |

Le sujet n'est masqué que pendant les frames 10–15, là où la sphère est
réellement opaque.

## Art généré, puis transformé en sprite

Six plaques produites par le **générateur d'image**, sur clé magenta pure, en
vrai pixel art. Archivées dans `gen/` :

| Fichier | Contenu |
| --- | --- |
| `sphere_stages.png` | 6 stades de la sphère arc-en-ciel opaque |
| `mega_emblem.png` | le symbole Méga-Évolution, double hélice d'ADN |
| `lightning_columns.png` | 4 variantes de grosses colonnes de foudre |
| `starburst.png` | 4 stades de l'onde de choc en étoile |
| `shards.png` | 4 stades des éclats convergents |
| `ground_pool.png` | 3 stades de la flaque de lumière au sol |

Chaîne appliquée par `build_mega_animation.py` :

1. **détourage exact** de la clé magenta, alpha binaire ;
2. **recadrage** sur le contenu utile ;
3. **mise à l'échelle NEAREST uniquement** — arêtes dures préservées ;
4. **composition par acte** selon des timelines explicites, une valeur par
   frame, lisibles et modifiables en tête du script ;
5. **verrouillage de palette** : chaque pixel ramené sur une palette d'effet
   écrite à la main. **12 couleurs**, transparence binaire.

Le symbole a été vérifié avant génération : c'est bien la **double hélice
d'ADN** du logo officiel.

La flaque au sol est posée sur la **ligne des pieds**, pas au centre du sprite,
pour qu'elle se lise comme du sol et non comme un halo flottant.

## Multidirectionnel

Chaque ligne utilise **l'artwork propre du sujet pour cette direction**, pris
dans sa feuille `Idle`. Le Pokémon regarde dans le bon sens sur les huit
lignes. Les effets radiaux (sphère, étoile, éclats, symbole) sont
symétriques : ils restent justes sous tous les angles.

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
- Les pixels de l'effet viennent du **générateur d'image**, donc pas d'une
  source canonique, contrairement aux lots sprite/portrait livrés avant.
- L'intégration PMDO du mod de référence passe par des **emitters Lua**, pas
  par une planche d'animation. Cette planche est un asset ; **le branchement
  moteur reste à faire et n'a pas été testé.**
