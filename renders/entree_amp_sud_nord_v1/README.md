# EAN1 — Entrée Amp sud → nord, format 4:3 vaste

Deuxième map au format 4:3 demandé : **768 × 576 px = 96 × 72 cases**, soit environ 2,4 écrans PMDO (320 × 240) dans chaque sens.

- Aperçu : `apercu_entree_amp_sud_nord_v1.html` (racine) ou `review/EAN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EAN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EAN1_`) : `EAN1_calques_png_8px.zip`.
- Source : `source/entree_amp_sud_nord_v1/`, 9 tests.

## « Même endroit, autre lieu »

Réf. DA : `Amp_Plains_entrance_TD.png`. Une première version générée sans guide était trop saturée (herbe jaune vif) : écartée après comparaison colorimétrique. Les bruts décor, sol et touffes retenus ont été générés **avec la ref canonique en guide** : herbe olive (133,5, 138,6, 107,1) contre (138,5, 145,6, 110,8) pour la ref, soit une distance de **9,6** (test `test_canonical_grass`, seuil 35). Le layout est inédit : sentier en S du sud vers une grotte au nord, parois tout autour, blocs et arbres morts.

## Normalisation 4:3

Le décor a été généré en 1200 × 896, puis réduit d'un facteur **uniforme** 576/896 = 0,643 → 771 × 576, et recadré au centre à 768. Le sol (1091 × 976) est normalisé par cover uniforme + recadrage centré. La réduction se fait par moyenne pondérée **par classe** : attribution exclusive de chaque pixel à la classe de poids maximal, puis palette commune de 96 couleurs.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | sol complet | plaine générée séparément | — |
| 01–06 | plaine, sentier, parois, blocs, arbres morts, grotte | décor généré | — |
| 07 | touffes (10) | planche générée (8 poses) | 12 × 10 ticks, rafale ouest→est |
| 08 | étincelles (7) | planche générée (8 poses) | 24 × 5 ticks, boucle de 2 s |

**Touffes** : inclinaisons mesurées (0,025 à 0,338), cycle sinusoïdal pleine amplitude sur 12 phases ; les poses quasi identiques (0,308/0,309) sont sautées par la sélection au plus proche. Palette olive propre de 7 couleurs.
**Étincelles** : lifecycle 8 poses × 2 phases + 8 phases de repos ; émetteurs décalés de 3 phases, toujours au moins une étincelle active. Palette propre de 12 couleurs.

## Honnêteté

- Le terrain, les touffes et les étincelles sont générés ; les cycles et trajectoires sont créés par nous.
- La pose « point » de l'étincelle reste un carré jaune un peu brut (2 phases sur 24) : c'est le dessin généré, accepté tel quel.
- Aucun test PMDO en jeu, art non approuvé.
