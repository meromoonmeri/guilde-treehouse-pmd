# ERN1 — Entrée Ruine sud → nord, V1

Troisième map de la série, après l'Entrée Vapeur et l'Entrée Cratère. Biome choisi par l'agent d'après la référence encore inutilisée `Sealed_Ruin_entrance_TDS.png` (à confirmer).

- Aperçu : `apercu_entree_ruine_sud_nord_v1.html` (racine) ou `review/ERN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `ERN1_projet_pmdo_0812.zip`. Calques PNG 8 px (préfixe unique `ERN1_`) : `ERN1_calques_png_8px.zip`.
- Source : `source/entree_ruine_sud_nord_v1/` (`build.py`, `package.py`, `test_build.py`).

## Calques (bas → haut)

| # | Calque | Animation |
|---|---|---|
| 00 | sables mouvants (structure rivière Métano) | 4 × 10 ticks |
| 01 | bulles de sable générées (12 poses, 8 émetteurs décalés) | 24 × 5 ticks |
| 02–07 | sol complet, sable, rebords des fosses, rochers, falaises, bouche | — |
| 08 | tourbillons de poussière générés (2, décoratifs, non bloquants) | 8 × 5 ticks |
| 09 | arbres morts (palette grise propre) | — |

## Honnêteté

Le terrain, les bulles et les tourbillons sont générés. Ce ne sont ni des pixels natifs, ni des animations officielles. Les couleurs des tourbillons sont remappées par rang de luminance sur la rampe de sable, faute de quoi ils étaient trop pâles. La bande d'ombre devant la bouche est rocheuse, donc le seuil est placé sur la première case libre en dessous. Aucun test PMDO en jeu, art non approuvé.
