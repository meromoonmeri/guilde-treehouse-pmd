# Tarpaud (Politoed) #0186 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Tarpaud (Politoed) : toutes les animations du sprite d'origine
(`source/personnages/reference/0186`) sont reprises, agrandies × 3 au plus proche voisin et entourées d'une aura rouge
animée (anneau plein + trame qui remonte le long du corps). Aucun pixel du Pokémon n'est redessiné ; deux couleurs
sont ajoutées (17 couleurs au total). `ShadowSize` passe à 2 (grande ombre). **Les nuages tournants et la
transformation sont des VFX séparés**, sans personnage, à superposer en jeu : voir
[`personnages/dynamax/vfx/`](../vfx/README.md) et l'entrée `dynamax.vfx` de `kit.json` (taille et décalage).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `tarpaud.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 136 × 240 (origine 40 × 72) | 7 | 34 ticks | — |
| Attack | 1 | 224 × 344 (origine 72 × 104) | 12 | 26 ticks | Hit 5, Return 7 |
| Strike | 2 | — | — | — | copie de Attack |
| Shoot | 3 | 144 × 216 (origine 40 × 64) | 14 | 29 ticks | Hit 3, Return 6 |
| RearUp | 4 | 104 × 168 (origine 32 × 48) | 6 | 36 ticks | Hit 1, Return 4 |
| Sleep | 5 | 88 × 128 (origine 24 × 32) | 2 | 65 ticks | — |
| Hurt | 6 | 144 × 200 (origine 40 × 56) | 2 | 10 ticks | — |
| Idle | 7 | 104 × 224 (origine 32 × 64) | 5 | 57 ticks | — |
| Swing | 8 | 224 × 272 (origine 72 × 80) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 168 × 256 (origine 48 × 72) | 16 | 36 ticks | — |
| Hop | 10 | 104 × 312 (origine 32 × 96) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 96 × 184 (origine 24 × 48) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 104 × 168 (origine 32 × 48) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 3 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

sprite original du jeu (CHUNSOFT), licence non précisée sur SpriteCollab : usage non commercial de fan uniquement. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
