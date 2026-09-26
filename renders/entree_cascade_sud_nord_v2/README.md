# ECN2 — Entrée Cascade V2 sud → nord, 4:3 vaste, rendu généré référencé Waterfall Cave

Correction de l'utilisateur : « tu dois utiliser ton générateur d'image, tu as mal audité l'ancienne méthode ». La méthode de la série (Vapeur → Jungle) est bien le **rendu généré référencé PMD** : le générateur reçoit le rip canonique en référence et reproduit ses textures. Le premier brut Cascade (V1, `source/entree_cascade_sud_nord_v1/bruts/`) avait été généré sans cette fidélité (« de l'idée, pas les textures canoniques ») ; la V1 livrée en pixels natifs exacts reste conservée telle quelle, et cette V2 refait la map selon la méthode attendue.

- Aperçu : `apercu_entree_cascade_sud_nord_v2.html` (racine) ou `review/ECN2_scene_animee.webp`.
- Pack PMDO 0.8.12 : `ECN2_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `ECN2_`) : `ECN2_calques_png_8px.zip`.
- Source : `source/entree_cascade_sud_nord_v2/`, 9 tests.

## Bruts

- `bruts/decor_magenta.png` (1200 × 896) : généré avec **les deux rips en référence** (`Waterfall_Cave_ledge_TDS.png`, `Waterfall_Cave_gem_TDS.png`), toute l'eau (cascade + bassins) en magenta. Stalactites, rochers bandés bleu-gris, sol de galets, cristaux : textures du rip reproduites.
- `bruts/sol_complet.png` : le générateur n'a pas su effacer les éléments (deux essais gardaient rochers et contours des bassins, supprimés) ; le sol complet est donc **édité par quilting** de blocs 96 px du sol du décor lui-même (`quilt_full`, coutures à coût minimal). Il n'est visible que sous les calques.

## Segmentation mesurée (pleine résolution)

Vide lum ≈ 36–43, sat ≈ 20 ; stalactites/fond lum ≈ 63–68 ; rochers lum ≈ 85 ± 22, b − r ≈ 45 ; sol lum ≈ 110 ± 10, **b − r ≈ 67**. Le sol est donc la composante bleue et claire (b − r lissé 5 px > 52, lum lissée > 92) reliée au bord sud, trous remplis. Cascade = composante magenta reliée au bord haut ; bassins = le reste du magenta. Pierres = lum < 70 dans le sol (30–1500 px). Cristaux = saturation > 110, **palette propre** (trop rares pour la palette commune de 96 couleurs, ils devenaient gris). Parois = reste avec lum lissée ≥ 78 (fermeture 6 px) ; plafond = reste.

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | bassins | structure rivière Métano, **couleurs exactes des sources turquoise du rip** (31,151,167) (31,119,135) (31,143,159) (39,175,191) et liseré (215,215,215) | 4 × 10 ticks |
| 01 | cascade | **frames Métano natives** `cascade_frame_1..4` : pied lignes 102–119 au bas de la bande, corps lignes 66–101 tuilé vers le haut, colonnes 8–55 tuilées (bande de 96 px = 2 × 48) ; translation pure, testée pixel à pixel | 4 × 10 ticks |
| 02 | scintillements | pixels Métano natifs | 4 × 10 ticks |
| 03–08 | sol complet, fond vide, plafond/stalactites, parois, pierres, cristaux | décor généré | — |

## Honnêteté

- Le décor est généré d'après les rips : textures fidèles mais **pas des tuiles natives**.
- Bassins façon Métano (pixels recalculés) ; cascade et scintillements natifs, cadence 10 ticks proposée.
- Le motif « ^^^ » de la cascade se répète tous les 36 px (tuilage de lignes natives) ; aucun cycle officiel de chute n'est récupéré.
- Collisions déduites du sol visible, chemin 16 × 16 vérifié sur la grille ; aucun test PMDO en jeu ; art non approuvé.
