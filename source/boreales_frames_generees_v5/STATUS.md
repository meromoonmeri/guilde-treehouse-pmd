# V5 — frames dessinées par génération et palette cycling

Demande : générer les dessins des frames, et ajouter du palette cycling. La V4 déformait un dessin existant : **cette méthode n'est plus utilisée pour les aurores V5**.

## Production
- Nouveau passage au générateur d'images, avec `aurorepmdsky.png` comme référence de style/couleurs uniquement.
- Le prompt demandait 8 poses sur 2×4 cellules ; la sortie réelle comporte **9 poses sur 3×3 cellules**. Elle est conservée sans modification dans `bruts/aurores_8_poses.png` (nom historique de la requête). Extraction faite selon la grille réelle, pas la grille demandée.
- Neuf dessins détourés, réduction uniforme en nearest-neighbor, petite marge transparente pour aligner les tailles. Aucun warp ni reprise des images d'aurore V1/V3/V4.
- **72 étapes de 100 ms = 7,2 s** : 9 dessins et 8 étapes de transition par paire. Les intermédiaires sont des fondus RGBA prémultipliés, **pas 72 dessins générés indépendamment**. Dernier dessin → premier inclus.

## Palette cycling réel sur indices
Chaque pose a un PNG indexé (`*_indexed.png`, mode P) et son masque alpha séparé. Palette de 256 entrées : 16 groupes de teintes froides × 16 niveaux de luminosité. Les groupes parcourent cycliquement cyan/bleu/violet/magenta ; la luminosité des niveaux reste fixe. Les 72 tables RGB sont exportées dans `animation/palettes_72.json`.

Ce sont les entrées RGB de la palette qui évoluent : les indices et l'alpha d'un dessin fixe restent identiques. Le mode « Palette cycling seule · dessin fixe » du lecteur et son WebP dédié le démontrent. Lors des transitions entre dessins, leurs couleurs indexées sont compositées par fondu ; ces couleurs intermédiaires ne sont donc pas toutes des entrées brutes de la palette.

## Livrables
- `keyframes/` : 9 dessins RGBA, leurs indices P et alpha L séparés.
- `animation/frames/` : 72 overlays RGBA 936×240.
- `animation/dessins_et_palette_cycling.webp` : animation complète sur transparence.
- `animation/palette_cycling_seule_pose_fixe.webp` : couleurs cyclées, géométrie fixe.
- `review/scene_dessins_generes_palette.gif` : scène animée, ciel/terrain fixes.
- `review/poses_et_couleurs.png` : exemples de dessins et couleurs.
- `calques/` : ciel, étoiles, terrain large V3 copiés byte-identiques, séparés.
- Aperçu autonome `apercu_boreales_generees_palette_v5.html` à la racine ; `apercu.html` dans le ZIP.

Wrap optionnel : texture936px, déplacement `floor(13*f/4) modulo936`, pose `f modulo72`. Boucle combinée de288étapes /28,8s. Le lecteur démarre sans wrap pour montrer les dessins/couleurs animés ; ajout du wrap par case indépendante. Trois dessins déphasés sont placés dans chaque bande pour peupler le fond large ; ce placement n'est pas une reconstruction du terrain à partir de morceaux de maps.

11tests dédiés : provenance de la génération,9dessins distincts, indices/palettes, couleurs seules sans changement d'alpha, formes animées sans cycling, luminosité des niveaux, fermeture des cycles,72PNG, WebP et GIF, calques fixes préservés. Syntaxe JS contrôlée ; pas de test interactif navigateur/import/collision/runtimePMDO. Les références restent conservées ; autres zones ouvertes.

**Art généré inspiré de la référence canonique, pas pixels natifs certifiés ni cycle officiel extrait.** Référence PMD fournie : Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft. Aucune permission supplémentaire de redistribution présumée. Les PNG font autorité pour les RGBA exacts ; WebP peut modifier les RGB invisibles sous alpha0, GIF réduit les couleurs.

Rebuild : `.venv/bin/python source/boreales_frames_generees_v5/build.py`, puis `package.py` dans le même dossier source.
