# Caps / terrasses V3 — présentation rapprochée face à la mer

## Demande et méthode
L’utilisateur veut davantage de calques similaires à Terrasse V2 et Cap V2 : falaise très proche de la caméra, latérale, face à la mer, avec roche Métano. La méthode confirmée est conservée : **références V2 + matière roche/herbe Métano → générateur sur magenta → détourage**, pas des layouts en aplats ni une reconstruction procédurale de la roche.

Six générations séparées : cap gauche, cap droit, terrasse droite, terrasse gauche, corniche gauche, balcon droit. Entrées du générateur : `references/cap_v2_magenta.png` pour 01/02/05, `references/terrasse_v2_magenta.png` pour 03/04/06, et `source/falaises_generees/reference_canonique.png` pour les six. Les deux références de layout viennent des terrains RGBA V2, simplement posés sur magenta. Empreintes dans `references.json`.

Les consignes imposaient une grande masse de terrain au premier plan, une ouverture latérale destinée à la mer, les textures Métano, et excluaient ciel/océan/nuages/structures du dessin de terrain. Les images sorties font toutes 1640 × 656 pixels. La variante 01 comporte des plaques de terre dans son herbe ; aucun chemin fonctionnel n’a été ajouté. Ces créations reprennent la référence, sans certification de pixels canoniques.

## Exports
`build.py` extrait le chroma (R>210, G<70, B>210). Les pixels conservés ne sont pas recolorés ni redimensionnés. La variante 04 est translatée de -256 px horizontalement puis recadrée dans le même canevas pour l’ancrer à gauche et ouvrir davantage la mer à droite. La sortie brute reste intacte ; les exports transparent et magenta uniforme partagent le cadrage corrigé.

Le filtre nocturne vient directement de `source/cote_v4_abyss/night.py`. Les plans de terrain regroupent herbe, parois et bordures : ce ne sont pas des calques sémantiques séparés. En revanche le terrain, le ciel, les nuages et l’océan sont bien indépendants. Les images de scène sont seulement des aperçus recomposés, avec les fonds V2 ajustés en nearest-neighbor. Les fonds sources sont aussi disponibles à leur résolution originale.

## Océan — demande précédente reprise
64 phases, 50 ms par phase, boucle 3,2 s. On interpole les palettes V2, pas les images ni la géométrie. Les huit palettes originales sont exactement conservées toutes les huit sous-phases. Le pas maximal entre deux phases, raccord final inclus, passe de 56 à 7 niveaux RGB par canal. Les indices, le fond statique et l’alpha restent inchangés. La variante nuit applique le filtre Abyss aux palettes.

L’aperçu compare ce cycle au cycle de l’ancien aperçu PNG (8 × 160 ms). Le mod natif antérieur utilisait plutôt 8 × 10 ticks, soit environ 1,33 s à 60 Hz. Une intégration ultérieure utilisera 64 × 3 ticks. **Aucune banque native, aucun Ground ni ZIP du mod n’a été modifié ici** : le nouveau cycle est livré en PNG indexés et dans l’aperçu autonome. Les nuages sont fixes dans cet aperçu ; le comportement wrap du précédent mod reste intact.

## Reconstruction et tests
Dépendances : Pillow et numpy.

```sh
python source/caps_terrasses_v3/build.py
python source/caps_terrasses_v3/gallery.py
python source/caps_terrasses_v3/verify.py
node source/caps_terrasses_v3/test_viewer.cjs
```

Les scripts ne régénèrent pas les six créations IA : ils utilisent leurs PNG bruts versionnés. `verification.json` vérifie le détourage, les pixels conservés, la nuit, les 128 phases indexées, les huit images-clefs originales, la constance des indices/alpha/IDAT et le raccord cyclique. Le test de galerie contrôle les douze sélections lieu/ambiance, visibilité des quatre plans, pause/reprise et horloges dans un DOM simulé, pas dans un vrai navigateur.

Les originaux Cap V2 / Terrasse V2, le témoin Métano et le mod existant sont préservés. Pas de validation GPU, de collisions ou d’intégration native revendiquée.
