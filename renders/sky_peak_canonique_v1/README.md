# Sky Peak — layout de la falaise de référence

**Version retenue après la dernière correction : le terrain vient directement du GIF fourni.** Les nouvelles formes de plateau, la plaine sans bordure et le grand promontoire générés précédemment sont abandonnés, conservés seulement en archives.

## Voir
- Galerie autonome : **`apercu_sky_peak_canonique_v1.html`**, à la racine.
- [Composition jour](jour/composition.png) / [nuit](nuit/composition.png)
- [Fleurs animées, jour](jour/fleurs_animation.webp) / [nuit](nuit/fleurs_animation.webp)
- [Planche des 4 clés](planches/fleurs_4_cles.png) / [32 phases](planches/fleurs_32_phases.png)

## Géométrie et texture
Références du commit **8b7e760** : `2cwdrrs469f61.gif` (504×504, 4 frames à 200 ms) et `232233.png` (planche sommet/couches).

La falaise, ses bordures et le terrain visible sont repris du GIF **sans translation ni redimensionnement**. Aucun nouveau plateau n’est substitué. Les pixels conservés hors zones de fleurs sont comparés exactement à la première frame source. Les fleurs sont retirées de la couche de terrain afin d’être animées indépendamment ; le petit fond caché sous les pétales est complété avec les observations disponibles des quatre frames, ou le vert natif dominant quand il n’est jamais visible.

Le panorama montagneux et les nuages sont des générations guidées par les deux références, pas des tuiles de montagne certifiées natives. Les originaux du terrain ne sont pas redessinés pour cette version retenue.

## Calques 504×504, alignement commun
1. `01_ciel`
2. `02_etoiles` (vide en jour)
3. `03_lune_halo` (vide en jour)
4. `04a_nuages_lointains_wrap`
5. `04b_montagnes`
6. `04c_nuages_proches_wrap`
7. `05_sol_et_rebord_herbeux`
8. `06_paroi_et_rochers`
9. `07_fleurs` (frame initiale)

Les fichiers se trouvent dans `jour/` et `nuit/`. Sol/roche sont des partitions de pixels par matériau visible, pas des sols reconstruits intégralement derrière la paroi. Les petites ombres végétales peuvent appartenir au groupe sombre. Leur recomposition restitue le terrain.

## Fleurs animées et couleurs assorties
Les pétales sont extraits des quatre frames du GIF puis regroupés spatialement pour conserver une famille de couleur par fleur/groupe. Quatre teintes harmonisées : **corail doux, pêche, crème, mauve**. Leur emplacement n’est pas redistribué.

- `fleurs/cles/00.png`…`03.png` : quatre clés recolorées, rythme source **200 ms**, boucle **0,8 s**.
- `fleurs/jour/00.png`…`31.png`, et même série en `nuit/` : **32 phases à 50 ms**, boucle **1,6 s**, version plus lente par interpolation alpha prémultiplié.
- Les phases 00,08,16,24 sont exactement les clés. Les phases intermédiaires ne sont pas de nouvelles frames natives dessinées ; l’interpolation peut adoucir les contours des petits pétales.
- Les planches sont réduites à des cellules 252×252 pour consultation ; utiliser les PNG individuels 504×504 pour importer les calques.

La version nuit utilise le filtre Abyss existant pour le terrain, les montagnes, nuages et fleurs. Pas d’effet lumineux ajouté aux fleurs.

## Nuages en wrap
Deux horloges indépendantes : nuages lointains **−2 px/s**, proches **−6 px/s**, wrap X de **504 px**. Périodes spatiales : **252 s** et **84 s**. Dessiner deux copies du calque à x et x+504, x étant le déplacement négatif modulo504. Ne pas remettre les nuages au début à chaque boucle de fleurs.

La galerie montre le wrap réel et permet de passer entre les 4 clés et les 32 phases. Les deux WebP courts montrent **les fleurs seulement**, avec nuages fixes pour ne pas créer de raccord brutal à 1,6 s.

## Contrôles et limites
`verification_terrain.json` : égalité des pixels natifs hors masque fleurs. `verification.json` : deux recompositions initiales exactes, 64 images WebP identiques aux calques, quatre clés préservées exactement, identité du wrap à 504 px. Le terrain conserve son dessin et sa taille ; la scène complète diffère volontairement dans les couleurs des fleurs et le panorama.

Scripts : `source/sky_peak_v1/build_canonique.py`, `gallery_canonique.py`, `verify_canonique.py` et `test_viewer.cjs`. Dépendances Pillow/numpy. Pas d’intégration `.rsground`, collisions, transition ou validation PMDO/GPU.

Sources originales conservées à la racine. Respecter les droits des ressources Pokémon Mystery Dungeon et de leurs contributeurs. Les nouveaux panoramas ne sont pas attribués aux auteurs des ressources canoniques.
