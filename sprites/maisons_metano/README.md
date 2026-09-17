# Dix huttes arrondies — référence Métano Town / Palika

Dix **nouvelles créations générées**, guidées par les maisons de Métano Town dans [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon). Ce ne sont ni des sprites officiels ni des extractions renommées. Formes rondes et matériaux naturels, sans toiture pyramidale ni maison humaine rectangulaire.

1. Feuillue
2. Vannerie
3. Galets
4. Nénuphar
5. Gland
6. Argile
7. Pivoine
8. Mousse
9. Ginkgo
10. Coquille

## Échelle et grille

Références originales : maison normale **80 × 111 px**, roche **96 × 96 px**, feu **110 × 99 px**. Les trois PNG de référence récupérés dans la bibliothèque du dépôt town02 ont été comparés, pixel opaque par pixel opaque, aux ressources `.tile` de Palika : **0 différence** pour les trois. Voir `source/maisons_metano/references/provenance.json`.

- Dessins normalisés à environ 96–104 px de largeur, au maximum 112 px de hauteur, **proportions conservées**, échantillonnage au plus proche et palette de 48 couleurs par maison.
- Cadre individuel **112 × 128 px**, soit **14 × 16 cases de 8 px**.
- Ligne de base : **y = 120 px**, ancre de placement géométrique : **(56, 120)**. Cette ancre n'est **pas** une position d'entrée ou de téléportation : certaines portes sont décentrées.
- Le rectangle de sélection et le placement sont alignés sur 8 px. Les contours du dessin ne sont pas artificiellement quantifiés en blocs de 8 px.
- PNG RGBA, pixels opaques ou transparents, pas de fond magenta ni de grille peinte.

## Fichiers

- `01_feuillue_jour.png` … `10_coquille_jour.png` : dix sprites indépendants.
- Les dix variantes `_nuit.png` : palette nocturne dérivée, géométrie identique. **Pas de lumières ou d'animations de fenêtres ajoutées.**
- `Maisons_Metano_jour.png` / `Maisons_Metano_nuit.png` : atlas **560 × 256 px**, 5 colonnes × 2 rangées de maisons, sans espacement supplémentaire.
- `Maisons_Metano_*.tile` : **deux ressources natives PMDO/RogueEssence**, cellules de 8 px, 70 colonnes × 32 lignes, 2240 entrées. Les cellules vides sont conservées ; les PNG internes identiques partagent leur offset.
- `Maisons_Metano_*.tsj` : exports Tiled sur grille 8 px, pas des fichiers d'import PMDO.
- `maisons.json` : noms, dimensions et rectangles de sélection en pixels et cellules.
- `planche.png` : présentation légendée agrandie ×2, **ne pas importer comme tileset**.
- `../../apercu_maisons_metano.html` : aperçu autonome hors ligne, palette jour/nuit, zoom natif/×2/×3, grille et téléchargement de chaque PNG. Références originales affichées à la même échelle.

## Import dans PMDO

1. Copier les deux nouveaux `.tile` dans `Content/Tile/` du mod (noms indépendants ; aucune ressource existante à remplacer).
2. Réindexer les ressources avec les outils de votre mod ou l'éditeur. **Ne pas écraser `index.idx` avec un index partiel.** Sans entrée d'index, PMDO peut afficher une tuile d'erreur.
3. Pour une Ground à **TexSize = 1**, utiliser le pas de **8 px**. Ne pas modifier la grille d'une carte existante sans vérifier son format.
4. Sélectionner le rectangle de **14 × 16 cellules** de la maison dans l'atlas. Les rectangles exacts sont décrits dans `maisons.json` (`atlas_rect_cells`).
5. Poser le sprite sur un calque de structure. Régler les obstacles, la zone d'entrée et les transitions de porte dans la Ground.

**Limites :** sprites fixes sur un seul calque ; portes ouvertes intégrées, pas de battants animés ni d'intérieurs ; séparation toit/façade et occlusion non fournies. Pas de `.rsground` ni de `.dir` GroundObject généré. Les collisions et les interactions ne sont pas automatiquement configurées. L'ouverture en jeu n'a pas été testée.

## Sources et attribution

Référence : **Palika / Halcyon**, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Le README du projet crédite Palika comme auteur et répertorie les artistes contributeurs : [crédits Halcyon](https://github.com/Palikadude/Halcyon#credits). Les références sont conservées séparément des créations et ne sont pas intégrées aux atlas de livraison. Leur présence dans un dépôt public n'implique pas une licence de redistribution générale.

Les cinq paires issues du générateur sont conservées dans `source/maisons_metano/paire_*.png`. Le script les détoure, enlève les débris isolés, les réduit sans déformation et produit les exports. La conformité artistique au style demandé reste une appréciation visuelle, pas une propriété que les tests peuvent certifier.

## Reconstruction et vérification

```sh
python source/build_houses_metano.py
python source/verify_houses_metano.py
```

Pillow requis. Le test contrôle les 20 PNG, les palettes et l'alpha, les dix dessins distincts, l'assemblage des atlas et le décodage indépendant des deux `.tile` avec comparaison exacte aux PNG. Résultat dans `verification.json`.
