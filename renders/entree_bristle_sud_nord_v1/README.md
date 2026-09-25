# EBN1 — Entrée Bristle sud → nord, V1

Cinquième map de la série « entrées sud → nord générées » (après Vapeur, Cratère, Ruine, Givre). L'agent l'a choisie d'après la référence encore inutilisée `Mt_Bristle_entrance_TD.png` : un canyon de sable entre des falaises grises en aiguilles, avec une gorge au nord et un torrent sur le flanc est.

- Aperçu : `apercu_entree_bristle_sud_nord_v1.html` (racine) ou `review/EBN1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EBN1_projet_pmdo_0812.zip`.
- Calques PNG 8 px, préfixe unique `EBN1_` : `EBN1_calques_png_8px.zip`.
- Source : `source/entree_bristle_sud_nord_v1/` (9 tests dans `test_build.py`).

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | torrent | structure et couleurs exactes de la rivière Métano ; l'onde descend vers le sud | 4 × 10 ticks |
| 01 | scintillements | pixels `Metano_Town_River_Sparkles` natifs, non recolorés | 4 × 10 ticks |
| 02 | sol complet | sable généré séparément | — |
| 03–05 | sable, berge de galets, rochers | décor généré | — |
| 06 | touffes au vent | planche générée (24 poses) | 12 × 10 ticks |
| 07–08 | falaises, gorge | décor généré | — |

**Touffes** : la planche générée ne suivait pas l'ordre demandé. Les 24 poses sont donc triées par inclinaison mesurée (décalage du haut par rapport à la base), puis le cycle suit une sinusoïde entre les extrêmes. Aucun pas du cycle ne dépasse 0,25, y compris le passage 11 → 0. Les 8 touffes remplacent celles du décor à leurs positions, avec un décalage de phase par tranche de 40 px (rafale d'ouest).

## Honnêteté

- Le terrain et les touffes sont générés ; le balancement est créé par nous.
- Les couleurs du torrent et les scintillements sont natifs Métano ; les pixels du torrent sont recalculés.
- Les ombres sont incluses dans le décor.
- Aucun test PMDO en jeu, art non approuvé.
