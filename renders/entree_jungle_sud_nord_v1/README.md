# EJN1 — Entrée Jungle sud → nord, format 4:3 vaste

Demande : « j'aimerais que les map soit plus vaste 4:3 ratio etc stp ! » puis « lance toi la suite ! ». Taille choisie par l'agent : **768 × 576 px = 96 × 72 cases**, soit environ 2,4 écrans PMDO (320 × 240) dans chaque sens. C'est 65 % de cases en plus que les lots 424 × 632 précédents.

- Aperçu : `apercu_entree_jungle_sud_nord_v1.html` (racine) ou `review/EJN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EJN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EJN1_`) : `EJN1_calques_png_8px.zip`.
- Source : `source/entree_jungle_sud_nord_v1/`, 9 tests.

## Normalisation 4:3

Le décor a été généré en 1200 × 896, puis réduit d'un facteur **uniforme** 576/896 = 0,643 → 771 × 576, et recadré au centre à 768 (1 px à gauche, 2 px à droite). Le facteur n'étant pas entier, la réduction se fait par moyenne pondérée **par classe** : la jungle ne bave pas sur la clairière, ni l'eau sur la berge. Chaque pixel est attribué à la classe de poids maximal, puis la palette est ramenée à 96 couleurs communes.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau | structure rivière Métano, palette jungle | 4 × 10 ticks |
| 01 | scintillements | pixels Métano natifs | 4 × 10 ticks |
| 02 | sol complet | herbe générée séparément | — |
| 03–10 | clairière, sentier, terre, berge, rochers, îlots d'arbres, jungle, entrée sombre | décor généré | — |
| 11 | papillons | planche générée (2 couleurs × 6 poses) | 48 × 5 ticks (4 s) |

**Papillons** : 6 trajectoires en huit fermées, avec x = cx + ax·sin u et y = cy + ay·sin 2u. Le battement avance d'une pose par phase, soit 8 battements par boucle, et la phase 47 revient à la phase 0 sans saut (testé).

## Honnêteté

- Le terrain et les papillons sont générés ; les trajectoires sont créées par nous.
- La rivière est façon Métano, avec des pixels recalculés.
- Le sol complet généré est très uni ; il ne se voit que sous les calques.
- Aucun test PMDO en jeu, art non approuvé.
