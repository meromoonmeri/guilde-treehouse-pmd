# Falinks (escouade) #0870 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Falinks (escouade) : toutes les animations du sprite d'origine
(`personnages/falinks`) sont reprises, agrandies × 2 au plus proche voisin, entourées d'une aura rouge
tramée et de trois nuages rouges qui tournent autour du corps. Aucun pixel du Pokémon n'est redessiné ; trois
couleurs sont ajoutées (15 couleurs au total). `ShadowSize` passe à 2 (grande ombre).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `falinks.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 128 × 224 (origine 72 × 64) | 6 | 28 ticks | — |
| Attack | 1 | 216 × 312 (origine 112 × 112) | 10 | 19 ticks | Rush 1, Hit 3, Return 6 |
| Strike | 2 | — | — | — | copie de Attack |
| Shoot | 3 | 136 × 240 (origine 72 × 80) | 13 | 29 ticks | Hit 3, Return 7 |
| Sleep | 5 | 112 × 168 (origine 64 × 40) | 2 | 65 ticks | — |
| Hurt | 6 | 144 × 224 (origine 72 × 72) | 2 | 10 ticks | — |
| Idle | 7 | 128 × 240 (origine 72 × 80) | 13 | 60 ticks | — |
| Swing | 8 | 208 × 312 (origine 112 × 112) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 176 × 240 (origine 88 × 72) | 16 | 36 ticks | — |
| Hop | 10 | 128 × 312 (origine 72 × 112) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 128 × 216 (origine 72 × 64) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 128 × 216 (origine 72 × 64) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 2 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

PMDCollab_1 (usage libre avec crédit, dans le cadre des règles de PMDCollab). Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
