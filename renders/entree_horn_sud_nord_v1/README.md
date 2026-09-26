# EHN1 — Entrée Horn sud → nord, format 4:3 vaste

Troisième map au format 4:3 demandé : **768 × 576 px = 96 × 72 cases**, soit environ 2,4 écrans PMDO (320 × 240) dans chaque sens.

- Aperçu : `apercu_entree_horn_sud_nord_v1.html` (racine) ou `review/EHN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EHN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EHN1_`) : `EHN1_calques_png_8px.zip`.
- Source : `source/entree_horn_sud_nord_v1/`, 9 tests.

## « Même endroit, autre lieu »

Réf. DA : `Mt_Horn_entrance_Sky.png`. Les bruts décor et sol ont été générés **avec la ref canonique en guide** : sable décor (217,3, 162,2, 92,5) contre (189,2, 145,6, 80,4) pour la ref, soit une distance de **34,8** (test `test_canonical_sand`, seuil 40 — le décor est un peu plus clair que la ref). Le layout est inédit : cour de sable, sentier en S du sud vers une grotte au nord, parois tout autour, blocs et 6 buissons secs.

## Normalisation 4:3

Le décor a été généré en 1200 × 896, puis réduit d'un facteur **uniforme** 576/896 = 0,643 → 771 × 576, et recadré au centre à 768. Le sol (1276 × 832) est normalisé par cover uniforme + recadrage centré. La réduction se fait par moyenne pondérée **par classe** : attribution exclusive de chaque pixel à la classe de poids maximal, puis palette commune de 96 couleurs.

## Segmentation (tout est ocre)

- **Roche** : germes sombres (lum<125 et r-b<105) + croissance bornée 8 px ; parois au bord, blocs intérieurs ≥ 400 px.
- **Buissons** : micro-relief dense (fraction de std3>12 en fenêtre 31 px > 0,40), détectés **avant** la roche pour ne pas être mangés par sa croissance ; 6 composantes, aucun extra.
- **Sentier** : zone lisse (std11<9) et claire touchant le bas.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | sol complet | sable généré séparément | — |
| 01–06 | cour, sentier, parois, blocs, buissons, grotte | décor généré | — |
| 07 | éboulis (6) | planche 1×8 générée | 8 poses ×2 + 8 repos, 24 × 5 ticks |
| 08 | poussières (6) | planche 2×5 générée, lue en ligne | 10 poses ×2 + 4 repos, 24 × 5 ticks |

Les planches ont des lignes de grille magenta (claires ou sombres) : le fond est détecté par règle élargie et les cases par extremum local près de chaque multiple du pas. Érosion anti-frange 1 px avec repli, palettes propres de 12 couleurs. Les deux cycles durent 2 s ; la scène boucle en 120 ticks.

## Honnêteté

- Le terrain, les éboulis et les poussières sont générés ; les cycles et la chronologie sont créés par nous.
- Aucun test PMDO en jeu, art non approuvé.
