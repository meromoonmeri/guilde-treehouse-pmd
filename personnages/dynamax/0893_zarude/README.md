# Zarude #0893 — sprite Dynamax au format SpriteCollab

![Comparaison](apercu_comparaison.png)

Version **Dynamax** du sprite SpriteCollab de Zarude : toutes les animations du sprite d'origine
(`personnages/zarude`) sont reprises, agrandies × 3 au plus proche voisin et entourées d'une aura rouge
animée (anneau plein + trame qui remonte le long du corps). Aucun pixel du Pokémon n'est redessiné ; deux couleurs
sont ajoutées (13 couleurs au total). `ShadowSize` passe à 2 (grande ombre). **Les nuages tournants et la
transformation sont des VFX séparés**, sans personnage, à superposer en jeu : voir
[`personnages/dynamax/vfx/`](../vfx/README.md) et l'entrée `dynamax.vfx` de `kit.json` (taille et décalage).

Construit par `source/personnages/build_dynamax_sprites.py` (méthode et réglages dans
[`personnages/dynamax/README.md`](../README.md)), vérifié par `verify_dynamax_sprites.py`
(`controle_qualite.json`).

## Fichiers

`AnimData.xml`, `<Anim>-Anim.png` / `-Offsets.png` / `-Shadow.png` (8 lignes de directions, ou 1), `nuit/` (filtre
nuit des salles), `zarude.aseprite` (8 calques de directions, une étiquette par animation), `apercu.png` (toutes
les images), `apercu_directions.png`, `apercu_comparaison.png`, `apercu_marche_attente.gif`, `apercu_attaques.gif`,
`apercu.html` (lecteur hors ligne), `kit.json`, `credits.txt`.

## Animations

| Animation | Index | Case | Images | Durée | Repères |
| --- | --- | --- | --- | --- | --- |
| Walk | 0 | 128 × 128 (origine 48 × 64) | 4 | 44 ticks | — |
| Attack | 1 | 200 × 264 (origine 72 × 88) | 13 | 26 ticks | Rush 2, Hit 3, Return 6 |
| Strike | 2 | — | — | — | copie de Attack |
| Shoot | 3 | 144 × 144 (origine 48 × 64) | 11 | 26 ticks | Hit 1, Return 3 |
| Sing | 4 | 128 × 168 (origine 48 × 64) | 16 | 48 ticks | Hit 5, Return 10 |
| Sleep | 5 | 104 × 88 (origine 40 × 40) | 2 | 65 ticks | — |
| Hurt | 6 | 176 × 144 (origine 56 × 72) | 2 | 10 ticks | — |
| Idle | 7 | 128 × 128 (origine 40 × 64) | 1 | 32 ticks | — |
| Swing | 8 | 272 × 248 (origine 88 × 96) | 9 | 16 ticks | Hit 5, Return 5 |
| Double | 9 | 192 × 192 (origine 72 × 88) | 16 | 36 ticks | — |
| Hop | 10 | 128 × 256 (origine 48 × 104) | 10 | 24 ticks | Hit 9 |
| Charge | 11 | 128 × 136 (origine 48 × 64) | 10 | 20 ticks | Hit 5, Return 9 |
| Rotate | 12 | 128 × 128 (origine 48 × 64) | 9 | 18 ticks | Hit 8 |

Les durées, index et repères d'images sont ceux du sprite d'origine ; les cases sont agrandies × 3 puis élargies
par pas de 8 pour contenir l'aura et les nuages, l'ancre au repos restant en (largeur / 2, hauteur / 2 + 4).

## Licence

CC BY-NC 4.0. Les crédits du sprite d'origine sont repris dans `credits.txt`. Forme non officielle, ni soumise ni
approuvée sur SpriteCollab.
