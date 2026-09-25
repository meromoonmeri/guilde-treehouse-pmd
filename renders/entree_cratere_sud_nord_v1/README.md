# ECN1 — Entrée Cratère sud → nord, V1

Map suivante après l'Entrée Vapeur V2. L'agent a choisi le biome d'après la référence encore inutilisée `Dark_Crater_entrance_TDS.png` ; ce choix reste à confirmer.

- Aperçu : `apercu_entree_cratere_sud_nord_v1.html` (racine) ou `review/ECN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `ECN1_projet_pmdo_0812.zip`. Calques PNG 8 px (PNG to Tileset, préfixe unique `ECN1_`) : `ECN1_calques_png_8px.zip`.
- Source : `source/entree_cratere_sud_nord_v1/` (`build.py`, `package.py`), avec 11 tests dans `test_build.py`.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | lave | structure rivière Métano, palette de la matière de lave générée | 4 × 10 ticks |
| 01 | éclats | pixels `Metano_Town_River_Sparkles` recolorés | 4 × 10 ticks |
| 02 | sol complet | sol de cendre généré séparément | — |
| 03 | bulles de lave | planche générée, 12 poses | 24 × 5 ticks |
| 04 | cendre | décor généré | — |
| 05 | rebords des mares | décor généré | — |
| 06 | falaises | décor généré | — |
| 07 | bouche du cratère | décor généré | — |
| 08 | braises | pixels orange du décor, pulsation créée | 6 × 10 ticks |

**Cycle d'une bulle** : point → petite → ronde → dôme → dôme fissuré → éclatement → couronne → croûte → anneau → anneau pâle → étincelles → fin, puis repos. L'anneau pâle généré était mêlé au magenta : il a été dérivé de l'anneau. La pulsation des braises suit les décalages 0,1,2,2,1,0, de sorte que la phase 5 revient sans saut à la phase 0 (testé).

## Honnêteté

Le terrain, les bulles et la pulsation sont générés ou créés par nous : ce ne sont ni des pixels natifs, ni des animations officielles. La lave est « façon Métano » (structure et cadence), pas faite de tuiles natives. Aucune ombre séparée : les ombres sont cuites dans le décor généré. Aucun test PMDO en jeu, art non approuvé.
