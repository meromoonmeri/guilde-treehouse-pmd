# Griknot (Gible) #0443 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Griknot (Gible) : toutes les animations du sprite d'origine
(`source/personnages/reference/0443`) sont reprises, agrandies × 2 au plus proche voisin, entourées d'une aura rouge
tramée et de trois nuages rouges qui tournent autour du corps. Aucun pixel du Pokémon n'est redessiné ; trois
couleurs sont ajoutées (15 couleurs au total). `ShadowSize` passe à 2 (grande ombre).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `griknot.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 72 × 128 (origine 24 × 40) | 4 | 28 ticks | — |
| Attack | 1 | 160 × 200 (origine 64 × 72) | 14 | 30 ticks | Rush 1, Hit 2, Return 7 |
| Strike | 2 | — | — | — | copie de Attack |
| Shoot | 3 | 88 × 136 (origine 32 × 40) | 17 | 35 ticks | Hit 2, Return 11 |
| SpAttack | — | — | — | — | copie de RearUp |
| RearUp | 4 | 72 × 128 (origine 32 × 40) | 11 | 31 ticks | Hit 0, Return 4 |
| Sleep | 5 | 64 × 112 (origine 24 × 32) | 2 | 65 ticks | — |
| Hurt | 6 | 88 × 152 (origine 40 × 48) | 2 | 10 ticks | — |
| Idle | 7 | 72 × 128 (origine 24 × 40) | 4 | 104 ticks | — |
| Swing | 8 | 168 × 208 (origine 72 × 80) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 128 × 176 (origine 48 × 64) | 16 | 36 ticks | — |
| Hop | 10 | 72 × 216 (origine 24 × 88) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 80 × 128 (origine 24 × 40) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 72 × 128 (origine 24 × 40) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 2 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

sprite original du jeu (CHUNSOFT), licence non précisée sur SpriteCollab : usage non commercial de fan uniquement. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
