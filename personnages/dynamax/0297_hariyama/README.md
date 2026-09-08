# Hariyama #0297 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Hariyama : toutes les animations du sprite d'origine
(`source/personnages/reference/0297`) sont reprises, agrandies × 2 au plus proche voisin, entourées d'une aura rouge
tramée et de trois nuages rouges qui tournent autour du corps. Aucun pixel du Pokémon n'est redessiné ; trois
couleurs sont ajoutées (15 couleurs au total). `ShadowSize` passe à 2 (grande ombre).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `hariyama.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 104 × 152 (origine 40 × 48) | 4 | 36 ticks | — |
| Attack | 1 | 184 × 208 (origine 72 × 72) | 13 | 28 ticks | Rush 2, Hit 3, Return 6 |
| Strike | 2 | 184 × 224 (origine 72 × 88) | 12 | 31 ticks | Rush 2, Hit 3, Return 7 |
| Shoot | 3 | 112 × 136 (origine 32 × 40) | 12 | 24 ticks | Hit 5, Return 9 |
| Twirl | 4 | — | — | — | copie de Rotate |
| Sleep | 5 | 96 × 136 (origine 32 × 40) | 2 | 65 ticks | — |
| Hurt | 6 | 128 × 176 (origine 48 × 56) | 2 | 10 ticks | — |
| Idle | 7 | 104 × 168 (origine 40 × 56) | 12 | 77 ticks | — |
| Swing | 8 | 184 × 208 (origine 72 × 72) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 152 × 192 (origine 64 × 72) | 16 | 36 ticks | — |
| Hop | 10 | 104 × 232 (origine 40 × 88) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 112 × 136 (origine 32 × 40) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 104 × 144 (origine 40 × 48) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 2 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

sprite original du jeu (CHUNSOFT), licence non précisée sur SpriteCollab : usage non commercial de fan uniquement. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
