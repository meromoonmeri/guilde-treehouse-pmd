# Guilde Treehouse — passages ouverts PMD

Cette reprise conserve l’univers graphique du **premier pack**. Les accès ont été corrigés suivant la dernière consigne : **des ruptures du contour avec un sol continu, pas une porte à chaque sortie**.

## Règles effectivement appliquées

- **Est / Ouest :** le plancher traverse une interruption de la bordure latérale. Pas de battant, de portique ni d’arche ajoutée sur ces accès.
- **Sud :** seul le sol se prolonge vers le passage. Une éventuelle porte se trouve hors caméra et n’est pas dessinée.
- **Nord :** passage de sol ouvert pour les salles 01 et 09 ; les accès par échelle gardent leur fonction.
- **Une seule porte fermée visible :** au nord du hall 02, donnant vers le bureau du maître 12. Le bureau conserve son accès sud, sans porte visible depuis l’intérieur.
- Les anciennes fausses portes de fond et les sorties sud superflues des chambres latérales ont été retirées.
- Dans le hall, **le tronc et l’échelle se prolongent au-delà du bord supérieur**, sans sommet de tronc scié visible.
- Les ombres restent des ombres de contact aux retours du contour ; elles ne forment pas de barre noire bouchant le sol.

Les pièces sont **vides et fixes**. Aucun meuble, paillasse, tapis, plante, bannière ou lampe n’est posé dans les fonds. Les deux tableaux muraux du hall sont conservés comme équipements encastrés. La banque d’objets du pack précédent reste fournie séparément.

## Fenêtres et paysage

Les cadres et croisillons sont conservés, mais **aucun paysage n’est peint dans le calque intérieur**.

- `base_jour_transparente.png` / `base_nuit_transparente.png` : vrais PNG RGBA, avec les ouvertures de fenêtres transparentes.
- `base_jour_magenta.png` / `base_nuit_magenta.png` : variantes de contrôle sur fond **#FF00FF**, visible à travers les fenêtres. Pour le jeu, utiliser de préférence les PNG transparents.
- `fenetres_exterieur/NN/` : six vues déjà positionnées et masquées aux fenêtres de chaque salle.
- `exterieur/` : les six panoramas complets, issus de la géographie de la terrasse approuvée.

Ambiances : **jour, nuit, crépuscule, aube, soir et orageux**. Les montagnes, le village et la rivière restent au même endroit. Les palettes, le ciel et la météo varient. Le paysage et la palette de l’intérieur peuvent être choisis indépendamment.

La salle 01 n’a pas de fenêtre vitrée : son accès nord est désormais une continuité de sol. Les persiennes des salles 08/10 conservent leurs lattes, avec une vue interchangeable dans leurs interstices.

## Onze calques séparés

1. Paysage extérieur interchangeable
2. Sol et continuité des passages
3. Structure, murs et ouvertures
4. Cadres de fenêtres, sans paysage
5. Contenu des tableaux encastrés
6. Porte nord du bureau — uniquement dans le hall
7. Décorations — **vide**
8. Objets — **vide**
9. Ombres de contact des accès
10. Éclairage complémentaire — **vide**
11. Bordure de premier plan, interrompue aux passages

Chaque salle est disponible en **jour et nuit**, avec une seule image par fichier Aseprite. Il n’y a aucune animation dans cette version.

## Contenu du kit

- `apercu_pmd.html` : aperçu autonome, hors ligne. Le bouton **« Base seule — magenta »** retire le paysage pour vérifier les ouvertures. Les cases permettent de masquer chaque calque.
- `salles/` : compositions, bases transparentes, bases magenta et 24 Aseprite fixes.
- `calques/` : 11 PNG transparents par salle et par palette.
- `tiled/` : 24 cartes orthogonales à cellules de **8 × 8 px**, avec des tuiles reconstituant exactement les images.
- `fenetres_exterieur/` : masques et 72 couches de paysage positionnées.
- `exterieur/` : 6 ambiances complètes.
- `sprites/` : banque indépendante du premier kit modulaire ; ces éléments ne sont pas posés dans les salles.
- `kit.json` : dimensions, accès, calques et chemins.
- `source/` : retouches natives retenues, sources du panorama, règles et scripts de reconstruction.

Le hall mesure **1280 × 544 px** ; les autres pièces **648 × 432 px**. Les grilles Aseprite et Tiled sont réglées sur 8 px. Les PNG ne sont pas pixellisés en gros blocs de 8 px.

Les cartes ne sont pas un jeu intégré : collisions, transitions et déclencheurs de porte doivent être configurés dans le moteur. Les accès sont décrits dans `kit.json` et `source/regles_acces.json`.

## Reproduction et contrôles

```bash
pip install -r source/requirements.txt
python source/rebuild_landscapes.py
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
```

Le contrôle relit et recompose les PNG, Aseprite et cartes Tiled ; vérifie les bases transparentes/magenta, les 6 vues alignées, les calques vides et l’unique porte nord. Validation par code, pas par ouverture dans l’interface d’Aseprite.

Les retouches ont été faites avec le générateur à partir des images du kit. Les images du jeu fournies par l’utilisateur ont servi à comprendre le principe des passages, pas à être collées dans les décors. **Le tout premier ZIP de la guilde et les archives de la terrasse approuvée restent inchangés.**

## Ponts suspendus modulaires — ajout indépendant

Voir **`apercu_ponts.html`** et **`sprites/ponts/README.md`** : ponts originaux inspirés de PMD, horizontaux/verticaux, jour/nuit, PNG transparents et tilesets Tiled animés en quatre phases. Cellules de 64 × 64 px, centres répétables entre les ancrages. Cet ajout ne change pas les salles fixes décrites ci-dessus. Reconstruction : `python source/build_bridges.py`.

### Nouvelle version dorée passée au générateur — PMDO / town02

**`apercu_ponts_pmdo.html`** présente la version adaptée à la référence jaune doré. Les assets sont dans **`sprites/ponts_pmdo/`** : deux orientations, quatre phases, jour/nuit, PNG transparents, huit `.tile` natifs en **8 × 8 px** et manifests d'animation. Les modules de dessin font 80 × 80 px (10 × 10 cellules moteur). Voir le README de ce dossier pour la réindexation PMDO et les limites de validation : les ressources Metano ont été inspectées, mais le téléchargement LFS de `WaterfallVillageCapital.rsground` a échoué, donc son TexSize et le placement précis restent à vérifier. Reconstruction et tests : `python source/build_bridges_pmdo.py && python source/verify_bridges_pmdo.py`.

## Dix maisons arrondies — référence Métano Town de Palika

**`apercu_maisons_metano.html`** : dix nouvelles huttes générées avec références originales affichées à la même échelle, jour/nuit, zoom et grille. **`sprites/maisons_metano/`** contient les 20 PNG, les deux atlas et `.tile` PMDO natifs, les TSJ et le manifeste. Cadres **112 × 128 px**, cellules **8 × 8 px**, dessins à une échelle comparable aux maisons de Métano. Les trois références ont été comparées aux ressources originales de `Palikadude/Halcyon` (0 différence sur les pixels opaques). Voir le README du dossier pour l'import, l'attribution et les limites : structures fixes, collisions/entrées à régler, pas de test en jeu. Reconstruction : `python source/build_houses_metano.py`; tests : `python source/verify_houses_metano.py`.

## Eau de Métano — extraction identique des animations originales

**`apercu_eau_metano.html`** présente les **quatre frames de cascade** extraites de `Metano_Town_Animation_Tileset` et les **quatre vraies planches de rivière** de Palika/Halcyon. Fichiers dans **`sprites/eau_metano/`** : PNG natifs, atlas source complet, cascades séparées, banque compacte de rivière, `.tile`, TSJ et provenance. Aucune génération ni retouche de pixels. La carte originale de Métano a été lue : grille 8 px et `FrameLength = 10` vérifiés pour la rivière ; la cadence autonome des rectangles de cascade reste proposée, non prouvée. Comparaisons source/export : zéro différence, voir le README et `verification.json`. Attribution aux auteurs de Halcyon conservée. Reconstruction : `python source/build_water_metano.py`; tests : `python source/verify_water_metano.py`.

## Trois grands layouts de falaises — extensions visuelles de Métano

**`apercu_falaises_metano.html`** : trois cartes de **2048 × 1536 px**, chacune en **256 × 192 cases de 8 px** : grande paroi, plateau isolé et trois terrasses. Textures natives répétées sans agrandissement, escaliers et grandes cascades à quatre phases. **`sprites/falaises_metano/`** contient les calques PNG, les compositions, trois cartes Tiled, l'atlas commun `.tile` PMDO et les métadonnées. Les formes du terrain et des rivières sont nouvelles ; ce ne sont pas des zones officielles ou des raccords déjà intégrés à Métano. Collisions et transitions à configurer. Contrôles : recomposition exacte des cartes sur les quatre phases et relecture de l'atlas natif. Voir le README du pack pour l'import et l'attribution. Reconstruction : `python source/build_cliff_layouts.py`; validation : `python source/verify_cliff_layouts.py`.

## Lot 02 — dix nouvelles maisons, falaises modulaires et rendu PNG

**`sprites/falaises_modulaires_v2/rendu_collection.png`** présente le nouveau décor, les dix nouvelles maisons et les morceaux de falaises. Rendus natifs **2048 × 1536 px** : `rendu_falaise.png` (sans maisons), `rendu_village.png` (avec maisons). **`sprites/maisons_organiques_v2/planche.png`** montre le nouveau lot ; **`sprites/falaises_modulaires_v2/planche_modules.png`** montre 11 fragments natifs et les 4 phases de cascade. La planche importable, les PNG individuels, les `.tile`/TSJ et les cartes Tiled sont fournis séparément, tous sur grille de 8 px. Les anciens lots restent inchangés. Voir les README de ces dossiers pour les commandes de reconstruction et les limites : géométrie nouvelle, morceaux sources inchangés, intégration PMDO et collisions à faire. Les vérificateurs comparent les fragments à leurs sources et recomposent le décor/village aux quatre phases.

## Layouts canoniques pixel-perfect — versions sèches et animées

**`apercu_metano_pixel_perfect.html`** : trois layouts **2048 × 1536 px**, grille **8 px**, avec bascule **sans eau / eau animée**. Dans **`sprites/metano_pixel_perfect/`**, chaque carte possède un PNG sec ne contenant que l'herbe, les falaises et leurs bordures, quatre rendus humides, les calques séparés et deux cartes Tiled. Aucun chemin, escalier ou bâtiment n'est ajouté. Contrairement aux prototypes précédents, chaque tuile utilisée est une copie vérifiée d'une tuile canonique de Métano : aucun dessin généré, aucune berge tracée, aucun agrandissement de texture. La géométrie est nouvelle ; les longues faces et chutes répètent des rangées natives. L'atlas `.tile` PMDO et les références source/Frames sont fournis. Voir `verification.json` et le README du dossier pour la portée exacte du contrôle et les limites d'intégration moteur. Reconstruction : `python source/build_metano_pixel_perfect.py`; tests : `python source/verify_metano_pixel_perfect.py`.

## Falaises côtières nues — générations et calques animés

**`apercu_falaises_cotieres_nues.html`** présente deux terrains sans bâtiments, arbres, campement, objets ni chemins, sur trois calques : terrain transparent, ciel animé (8 frames) et mer animée (5 frames). Les PNG et leur manifeste sont dans `sprites/falaises_cotieres_nues/`, l’archive dans `falaises_cotieres_nues_pack.zip`.

**Statut explicite : les falaises sont générées et guidées par les références Métano, pas composées de tuiles canoniques vérifiées.** Les fonds viennent de la planche côtière fournie par l’utilisateur, avec cadences proposées. L’animation est visible dans l’aperçu ; elle doit être configurée séparément dans PMDO. Voir [le README du lot](sprites/falaises_cotieres_nues/README.md).

## Côte V2 — roche corrigée, overlay de nuages wrap et mer à palette cyclique

**`apercu_cote_v2.html`** présente quatre calques indépendants : ciel généré sans nuages, nuages transparents à défilement horizontal continu avec wrap, mer indexée à huit palettes et terrain. La roche de la **terrasse** a été régénérée avec les modules Métano comme référence ; elle reste un rendu généré, non une copie certifiée des tuiles natives. Le terrain du promontoire est conservé.

Les huit PNG de mer ont **les mêmes indices et chunks IDAT** : seules les entrées de palette tournent, sans déplacement géométrique ni changement de transparence. Les quatre nuages sont exportés séparément et sur un strip wrap de **2200 × 344 px**, sans redimensionnement. Les tests vérifient la jonction du wrap et le cycle de palette. L’import PMDO seul n’active pas ces animations : voir [les instructions](sprites/cote_v2/README.md).

- Assets et paramètres : `sprites/cote_v2/`.
- Comparatif de roche : `sprites/cote_v2/ROCHE_AVANT_APRES_NE_PAS_IMPORTER.png`.
- Pack : `cote_metano_v2_wrap_palette.zip`.
- Scripts : `source/build_cote_v2.py`, `source/verify_cote_v2.py`, `source/package_cote_v2.py`.

## Cartes côtières V2 — Ground PMDO natives

Les deux zones V2 ont désormais un générateur de **vraies `.rsground`** avec
leurs tilesets `.tile`, fonds `.dir`, mer animée et nuages en wrap natif.
Des calques vides permettent d'ajouter sols, structures, avant-plans et objets.

- [Installation, calques, limites et formats vérifiés](source/pmdo_cote/README.md)
- Reproduire le pack : `.venv/bin/python source/pmdo_cote/package.py`
- Sortie par défaut : `~/cote_metano_v2_pmdo.zip` (livrée séparément, hors Git).
- Validation indépendante des ressources et des pixels ; **pas de test dans PMDO**.
- Collisions libres à dessiner avant utilisation comme niveau jouable.
