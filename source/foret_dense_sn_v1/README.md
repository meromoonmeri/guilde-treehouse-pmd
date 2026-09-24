# source/foret_dense_sn_v1 — méthode hybride « texture canonique exacte + éléments retouchés »

Map : entrée de forêt dense sud → nord (références D24P11A / D24P31A). Livrable dans `renders/foret_dense_sn_v1/`, galerie `apercu_foret_dense_sn_v1.html`.

Aucun module n'écrit de fichier à l'import. Seuls `build.py` et `viewer.py` écrivent, et seulement s'ils sont lancés comme scripts.

| Module | Rôle |
|---|---|
| `refs/` | copies PNG pixel-identiques des deux GIF de la racine |
| `labels.py` | classes de matière par pixel (herbe, herbe sombre, mur d'arbres, chemin, fleur, rocher, buisson, tunnel, canopée) à partir des couleurs exactes et du voisinage |
| `pmdsynth.py` | quilting guidé au pixel (patchs, coupe minimale, pixels imposés, pénalité de réutilisation), provenance `(source, y, x)` |
| `strips.py` | **parois périodiques exactes** (bloc de 192 lignes de D24P31A) et **chemin par segments** rigides de D24P11A |
| `synth.py` | sol (herbe stricte), antichambre sombre (distance signée au bord du cercle sombre de B), étapes de synthèse |
| `layout.py` | carte 512×672 : ligne médiane et largeur du chemin, forme d'ombre, boîte d'entrée, parois (décalage, phase) |
| `pixelize.py` | retouche 1:1 des générations : magenta explicite, grille, vote majoritaire, sous-palettes de matière, alpha binaire |
| `sprites.py` | découpe canopée / sol des sprites retouchés ; fleurs et buissons canoniques exacts |
| `build.py` | assemblage des 9 calques, composite, ORA, provenance, manifest, galerie, pack |
| `viewer.py` | galerie autonome (calques, solo, zoom, grille 8 px, provenance) |
| `test_build.py` | 7 tests du livrable |
| `bruts/` | générations brutes sur magenta (`gen_*.png`) et références de style découpées dans D24P11A (`ref_*.png`) |

## Leçons de méthode
1. **Le quilting à patchs carrés ne convient qu'aux textures stochastiques** (herbe, herbe d'ombre). Sur des objets structurés, il hache tout : parois d'arbres en blocs, pavés du chemin tranchés. Les deux essais ont été rejetés à la revue visuelle.
2. **Chercher la structure de la référence avant de synthétiser.** Les parois de D24P31A se répètent tous les 192 px, avec des lignes où `B[y] == B[y+192]`. Empiler la bande à partir d'une de ces lignes donne une paroi exacte, sans aucun raccord inventé.
3. **Formes linéaires (chemin) : segments rigides le long de l'axe**, en pleine largeur avec les bords flous, sans étirement ni cisaillement. Coupe minimale horizontale entre segments, coupes verticales dans l'herbe côté sol.
4. **Ombre : forme à liseré canonique** (distance signée au bord du vrai cercle sombre), et non un dégradé de niveau : le dégradé donnait des blocs et des bandes.
5. Générations : références de style = vrais pixels détourés sur magenta et agrandis ×4 ou ×6 au plus proche voisin. Pour la retouche, exclure la frange magenta (3 px) des votes : sinon des points orange apparaissent sur la silhouette. Le noir du tunnel se projette sur les verts les plus sombres, les références n'ayant aucune couleur de valeur < 0,2.
6. Le gate refuse les calques de petits sprites qui contiennent trop de couleurs rares. Comme le jeu, réutiliser peu de modèles canoniques, mais plusieurs fois.
