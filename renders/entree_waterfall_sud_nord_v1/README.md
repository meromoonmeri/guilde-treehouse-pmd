# EWN1 — Entrée Waterfall sud → nord, format 4:3 vaste

Quatrième map au format 4:3 demandé : **768 × 576 px = 96 × 72 cases**, soit environ 2,4 écrans PMDO (320 × 240) dans chaque sens.

- Aperçu : `apercu_entree_waterfall_sud_nord_v1.html` (racine) ou `review/EWN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EWN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EWN1_`) : `EWN1_calques_png_8px.zip`.
- Source : `source/entree_waterfall_sud_nord_v1/`, 9 tests.

## « Même endroit, autre lieu »

Réf. DA : `Waterfall_Cave.png` (grotte aux gemmes, roche rouge sombre). Les bruts décor et sol ont été générés **avec la ref canonique en guide** : roche décor (71,6, 25,7, 47,2) contre (87,1, 19,7, 50,8) pour la ref, soit une distance de **17,0** (test `test_canonical_rock`, seuil 40). Le layout est inédit : salle close aux murs de stalactites, sentier pâle en S du sud vers un passage au nord, **8 bassins d'eau luminescente** et gemmes incrustées.

## Normalisation 4:3

Le décor a été généré en 1200 × 896, puis réduit d'un facteur **uniforme** 576/896 = 0,643 → 771 × 576, et recadré au centre à 768. Le sol (1120 × 960) est normalisé par cover uniforme + recadrage centré. La réduction se fait par moyenne pondérée **par classe** : attribution exclusive de chaque pixel à la classe de poids maximal, puis palette commune de 96 couleurs.

## Segmentation

- **Bassins** : grandes composantes magenta (> 1500 px), 8 exactement ; les gemmes violettes confondent la règle magenta, elles sont détectées **avant** l'eau et exclues de sa dilatation.
- **Gemmes** : saturées et lumineuses (sat>75, lum>65), composantes 30–2500 px hors bassins.
- **Sentier** : pâle (lum>90), composante touchant le bas.
- **Passage** : plus grosse composante très sombre (lum<35) de la boîte nord-centre (430–770, y<230).
- **Stalagmites** : gris-bleu (b>r), tons moyens, composantes ≥ 500 px.
- **Parois** : sombre (lum<75) touchant les bords gauche/droit/haut ; le sol est le reste.

## Eau et scintillements

L'eau des 8 bassins suit la structure Métano adaptée à la grotte : 4 phases (2 calques eau : surface + profondeur), cycle de 40 ticks. Les scintillements viennent d'une planche 1×8 générée sans grille : 8 poses lues deux fois + 8 ticks de repos, 24 × 5 ticks, boucle de 2 s, **7 émetteurs** sur les gemmes (décalages 0, 3, …, 18 ticks). La scène boucle en 120 ticks.

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau (surface + profondeur) | palette cave adaptée Métano | 4 phases × 10 ticks |
| 01–07 | sol complet, sol, sentier, parois, stalagmites, gemmes, passage | décor et sol générés | — |
| 08 | scintillements (7) | planche 1×8 générée | 8 poses ×2 + 8 repos, 24 × 5 ticks |
| 09 | vide, `Layer=4` (Top) | — | — |

## Marqueurs et collisions

- `entrance` [376, 560] au sud sur le sentier ; `donjon_seuil` [376, 112] sous le passage, au nord. **Aucun warp.**
- Bloqué : 3152/6912 cases (bassins, parois, passage). Un chemin libre de 16 × 16 px a été vérifié sur la grille. **À contrôler en jeu.**

## Honnêteté

- Le terrain, l'eau et les scintillements sont générés ; les cycles et la chronologie sont créés par nous.
- Aucun test PMDO en jeu, art non approuvé.
