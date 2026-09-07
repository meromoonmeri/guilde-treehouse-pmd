# Export au format SpriteCollab

Arborescence telle qu'on la déposerait sur [PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab) : **rien que les
fichiers du format officiel**, sans aperçu, sans GIF, sans Aseprite, sans `kit.json`.

```
spritecollab/
├── sprite/<num>/    AnimData.xml (CRLF, 2 espaces), <Anim>-Anim/Offsets/Shadow.png, credits.txt
└── portrait/<num>/  <Emotion>.png et <Emotion>^.png en 40 × 40, credits.txt
```

## Sprites — animations de scène ajoutées

| # | Pokémon | Animations au total | Ajoutées | `Eat` | Licence |
| --- | --- | --- | --- | --- | --- |
| 0186 | Politoed | 35 | 22 | dessiné à la main | Unspecified |
| 0241 | Miltank | 36 | 22 | composé | Unspecified |
| 0282 | Gardevoir | 36 | 22 | composé | Unspecified |
| 0297 | Hariyama | 35 | 22 | composé | Unspecified |
| 0424 | Ambipom | 36 | 22 | dessiné à la main | Unspecified |
| 0443 | Gible | 36 | 22 | dessiné à la main | Unspecified |
| 0674 | Pancham | 35 | 22 | généré puis discipliné | CC_BY-NC_4 |
| 0685 | Slurpuff | 34 | 22 | généré puis discipliné | CC_BY-NC_4 |
| 0702 | Dedenne | 33 | 22 | dessiné à la main | CC_BY-NC_4 |
| 0923 | Pawmot | 35 | 22 | dessiné à la main | PMDCollab_1 |

Les 22 animations ajoutées : `EventSleep`, `Wake`, `Eat`, `Tumble`, `Pose`, `Pull`, `Pain`, `Float`, `DeepBreath`, `Nod`, `Sit`, `LookUp`, `Sink`, `Trip`, `Laying`, `LeapForth`, `Head`, `Cringe`, `LostBalance`, `TumbleBack`, `HitGround`, `Faint`.

## Portraits — émotions complétées

| # | Pokémon | Images (émotions + miroirs) | Licence |
| --- | --- | --- | --- |
| 0186 | Politoed | 32 | PMDCollab_2 |
| 0297 | Hariyama | 32 | Unspecified |
| 0424 | Ambipom | 32 | PMDCollab_1 |
| 0923 | Pawmot | 32 | PMDCollab_1 |

## Comment c'est fait

- **Animations de scène** : chaque image est une case officielle du Pokémon lui-même,
  replacée par rapport à son ancre, avec déformation à charnière basse (les appuis au sol
  restent fixes) et membres articulés repérés par les ancres `lhand`/`rhand` de
  `-Offsets.png`. Cadences, cases et créneaux `<Index>` relus sur Bayleef #0155.
  **Aucun pixel repeint** : la palette est incluse dans celle du sprite d'origine.
- **`Eat` dessinés à la main** (Politoed, Ambipom, Gible, Pawmot, Dedenne) : la bouche est
  peinte dans la palette du sprite, à la manière relevée sur les `Eat` de Pichu #0172 et
  Riolu #0447 (palette fermée, cerne noir, ombrage ordonné, changement local).
- **`Eat` produits par générateur d'images** (Gardevoir, Pancham, Slurpuff) : le PNG du sprite
  officiel a été soumis à un générateur, dont la sortie a été ramenée sur la grille exacte,
  rabattue sur la palette du sprite (178 à 251 couleurs → 9 à 11) et limitée au rectangle de
  la bouche. 86 à 90 % du sprite conservé. Hariyama et Miltank, essayés de la même façon,
  ont été **écartés** (68 % et 15 % de conservation : personnage méconnaissable).
- **Portraits** : le `Normal` officiel sert de base et n'est jamais redessiné. Le fond est
  repeint aux **couleurs canoniques de l'émotion** dans la géométrie officielle (ciel plein,
  damier de transition, sol plein) ; les yeux sont transformés par opérations sur leurs
  propres couleurs ; les effets viennent de la palette Chunsoft.

## Contrôle

```
sprite/0186 : 35 animations, format officiel
sprite/0241 : 36 animations, format officiel
sprite/0282 : 36 animations, format officiel
sprite/0297 : 35 animations, format officiel
sprite/0424 : 36 animations, format officiel
sprite/0443 : 36 animations, format officiel
sprite/0674 : 35 animations, format officiel
sprite/0685 : 34 animations, format officiel
sprite/0702 : 33 animations, format officiel
sprite/0923 : 35 animations, format officiel
portrait/0186 : 32 images 40 × 40, miroirs exacts
portrait/0297 : 32 images 40 × 40, miroirs exacts
portrait/0424 : 32 images 40 × 40, miroirs exacts
portrait/0923 : 32 images 40 × 40, miroirs exacts
```

Vérifié à l'export : `AnimData.xml` en CRLF, feuilles aux dimensions déclarées, alpha 0 ou 255,
15 couleurs au plus, portraits 40 × 40 opaques, versions `^` miroirs exacts.

## Licence et statut

Les `credits.txt` **conservent toutes les lignes d'origine** et ajoutent la contribution en
reprenant la licence déjà déclarée sur le sprite. Ces ajouts n'ont été **ni soumis ni
approuvés** sur SpriteCollab : c'est un export prêt à être proposé, pas un contenu officiel.
