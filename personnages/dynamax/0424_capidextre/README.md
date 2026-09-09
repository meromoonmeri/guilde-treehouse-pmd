# Capidextre (Ambipom) #0424 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Capidextre (Ambipom) : toutes les animations du sprite d'origine
(`source/personnages/reference/0424`) sont reprises, agrandies × 3 au plus proche voisin et entourées d'une aura rouge
animée (anneau plein + trame qui remonte le long du corps). Aucun pixel du Pokémon n'est redessiné ; deux couleurs
sont ajoutées (14 couleurs au total). `ShadowSize` passe à 2 (grande ombre). **Les nuages tournants et la
transformation sont des VFX séparés**, sans personnage, à superposer en jeu : voir
[`personnages/dynamax/vfx/`](../vfx/README.md) et l'entrée `dynamax.vfx` de `kit.json` (taille et décalage).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `capidextre.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 136 × 208 (origine 40 × 56) | 8 | 40 ticks | — |
| Attack | 1 | 224 × 288 (origine 72 × 88) | 9 | 24 ticks | Rush 1, Hit 2, Return 6 |
| MultiStrike | 2 | 232 × 288 (origine 72 × 88) | 15 | 39 ticks | Rush 1, Hit 2, Return 6 |
| Shoot | 3 | 144 × 208 (origine 40 × 56) | 12 | 29 ticks | Hit 2, Return 5 |
| SpAttack | — | — | — | — | copie de RearUp |
| RearUp | 4 | 136 × 224 (origine 40 × 64) | 16 | 36 ticks | Hit 0, Return 7 |
| Sleep | 5 | 128 × 168 (origine 40 × 48) | 2 | 65 ticks | — |
| Hurt | 6 | 144 × 232 (origine 40 × 64) | 2 | 10 ticks | — |
| Idle | 7 | 136 × 216 (origine 40 × 64) | 6 | 39 ticks | — |
| Swing | 8 | 248 × 296 (origine 80 × 88) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 192 × 264 (origine 56 × 80) | 16 | 36 ticks | — |
| Hop | 10 | 136 × 336 (origine 40 × 104) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 128 × 192 (origine 40 × 56) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 120 × 184 (origine 32 × 48) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 3 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

sprite original du jeu (CHUNSOFT), licence non précisée sur SpriteCollab : usage non commercial de fan uniquement. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
