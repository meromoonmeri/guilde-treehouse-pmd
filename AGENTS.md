# Méthode de production approuvée — zones Métano

## Correction utilisateur du 13 septembre 2026 — nouvelles entrées indépendantes

Pour les nouvelles entrées de donjon indépendantes, l’utilisateur autorise expressément des **textures inventées dans la DA PMD**, via le générateur, avec de nombreux layouts et biomes. La contrainte des falaises/structures Métano exactes ne s’applique que lorsqu’il demande d’étendre Métano. Ne pas réimposer cette contrainte aux nouvelles entrées. Consulter les Ground PMD Sky comme références et publier des PNG visibles avec leurs chemins GitHub.

La première collection de 12 images est dans `renders/entrees_pmd_collection/`, avec variantes Abyss. Ce sont des illustrations aplaties, non intégrées au mod et non certifiées comme tilesets natifs. Les 40 PNG du mod déjà livré sont séparés dans `renders/metano_expeditions_actuel/`. Les exigences natives ci-dessous continuent de concerner les extensions Métano et les livraisons réellement destinées à l’import moteur.

L’utilisateur a explicitement approuvé la méthode des deux zones guidées et demandé de la conserver (12 septembre 2026).

Pour les zones de terrain Métano :

- Utiliser le générateur d’images avec les références canoniques pour proposer la **composition**, puis reconstruire avec de véritables tuiles natives de 8 px. Ne pas présenter les pixels générés comme des tuiles canoniques.
- Conserver les silhouettes organiques et les variantes d’ombre guidées par les propositions. Ne pas remplacer cette méthode par des murs rectilignes procéduraux ou une simple mosaïque de tuiles choisies indépendamment.
- Ne pas recolorer, tourner, retourner, agrandir ou repeindre les tuiles natives. Les transformations du guide servent uniquement à la sélection des tuiles.
- Préserver les propositions et compositions déjà approuvées. Une demande d’export en calques n’est pas une demande de régénération de leur géométrie.
- Fournir des calques transparents séparés comme pour la guilde : sol, parois, bordures, berges, surface de rivière, cascades. Fournir aussi les versions sèches sans eau ni chemins et quatre phases natives de l’eau.
- Conserver la provenance des tuiles, vérifier les exports et présenter un résultat visible. Ne pas confondre fidélité des pixels avec validation des raccords artistiques, collisions ou intégration PMDO.

Références de travail : `source/build_zones_guidees.py`, `source/build_zones_multicalques.py`, `sprites/zones_guidees/README.md`, `sprites/zones_guidees/README_multicalques.md`.
Les règles propres aux salles de la guilde restent dans `kit.json` et `source/regles_acces.json` ; cet ajout ne les modifie pas.

## Retour en jeu : réserve importante après l’approbation visuelle

L’utilisateur signale ensuite une qualité désastreuse à l’import et des falaises perçues comme trop petites. L’audit `audits/metano_import/RAPPORT.md` confirme que l’assemblage par fragments de 8 px et colonnes d’ombre répétées ne préserve pas les volumes natifs ; une réduction effective dans son import reste à vérifier. L’approbation des aperçus ne vaut donc pas validation du rendu moteur.

Conserver les propositions générées, mais privilégier pour une prochaine correction des **modules natifs complets** (sommet, face, pied, retours) étalonnés à Métano. Ne pas considérer les seuls tests « 0 différence de pixel » comme une validation artistique ou d’échelle. Ne pas agrandir arbitrairement tous les PNG. Valider un échantillon au zoom natif puis dans le jeu avant de généraliser la correction.

## Contrat d’import confirmé par l’utilisateur

L’utilisateur importe les **PNG dans l’éditeur PMDO Dev via PNG to Tileset**. Les prochains PNG de jeu doivent être natifs, nets et structurellement cohérents avec Métano, pas des illustrations générées simplement agrandies. Les prototypes du générateur restent des guides uniquement.

Le lot `sprites/metano_import_png/` inaugure les blocs natifs complets et les noms `METANO_V3_*` uniques : l’importeur nomme les tilesets par basename et peut écraser deux fichiers homonymes venant de dossiers différents. Documenter explicitement la taille d’import **8 px**. Vérifier dimensions divisibles, rectangles complets, absence de resampling et recomposition. Ne pas appeler ce lot sec de calibration un remplacement complet des grandes zones, ni déclarer un test moteur non effectué.

## Vrais layouts utilisateur retrouvés sur la branche distante

Le commit utilisateur `3bc185bec2d5aa295f32825927db9d25bb936f75` était sur `arena/01a095e8-guilde-treehouse-pmd`, PAS sur main. Toujours vérifier la branche distante de la session, pas seulement origin/main, pour les nouveaux uploads utilisateur.
Les fichiers `IMG_4888.jpeg`, `IMG_4889.png`, `IMG_4890.png`, `IMG_4892.png` représentent deux lieux côtiers (bureau de Bekipan ; terrasse de campement avec grotte), avec plusieurs ambiances/références du premier. Pour « les layouts que j’ai commit », utiliser ces fichiers, pas les anciens cirques de calibration. Les deux générations diurnes sont dans `source/layouts_commit_3bc185b/`, explicitement non certifiées comme tuiles canoniques.

## Correction demandée : vraie variante Métano nuit d’Abyss to Ascension

La référence existe dans `meromoonmeri/new-era-abyss-to-ascension-V4`, commit
`55860b9a5eb48697a3cea3a8bdfce5f0529d6141` : `Metano_Town_Base_Night.tile`,
`Metano_Town_Cliffs_Night.tile`, `Metano_Town_Fringe_Night.tile`.
Copies et preuves : `source/cote_v4_abyss/`. Utiliser leurs pixels nocturnes
existants, pas la formule Guilde/Sharpedo pour le terrain. Cette dernière
reste la référence des fonds. L’utilisateur demande toute la roche dans le
style Métano, sans fragments réinterprétés par le générateur. Le pack V3
conservait encore lisière et ombres générées : ne pas le considérer corrigé.
Le nouvel échantillon natif est une calibration de matière, pas une validation
des retours, des raccords ni des volumes, et pas un remplacement des 20 Ground.

## Filtre Abyss demandé explicitement — correction complète livrée

La dernière consigne autorise et demande le filtre nocturne exact d’Abyss.
`source/cote_v4_abyss/night.py` reprend `tools/tile_night.py` (blob
`438383f479e2d80a6a0b3be4cced4087470d9835`), vérifié contre le script original
sur 1421 couleurs et contre les trois feuilles nocturnes complètes. Cette
transformation de nuit est explicitement voulue ; les pixels de JOUR restent
natifs sans recoloration. Ne pas ajouter le filtre Guilde/Sharpedo par-dessus.
La correction complète est maintenant `cotes_metano_abyss_0812_pmdo.zip`,
20 Ground `v40812_*`, aperçu `apercu_cotes_metano_abyss.html`. Elle remplace
l’échantillon comme livraison courante, mais tous les anciens lots sont conservés.
Les masques V3 guident la géométrie, pas les couleurs. Herbe, faces, retours,
couronnes et pieds viennent de modules natifs. Aucun ancien RGB généré ni
ombre générée. Panneaux 64x48 prolongés pour les grandes hauteurs, retours aux
bords. Tests de provenance, alpha, filtre, binaires et installateur PASS ;
ceci ne signifie ni raccords artistiques parfaits ni ouverture moteur testée.

## Métano Expéditions — sept falaises et trois entrées livrées

Livraison courante : `mod_metano_expeditions_pmdo_0812.zip`, projet
`metano_expeditions`. 20 nouveaux Ground `v50812_*` et 20 précédents `v40812_*`,
soit 40 Ground / 20 lieux en jour-nuit. Aperçu `apercu_metano_expeditions.html`.
Les références Crooked Cavern / Brine Cave / Drenched Bluff sont utilisées
uniquement pour la composition et la construction : aucune de leurs textures
n’est peinte dans nos nouvelles cartes. Deux grottes partagent un encadrement
Métano natif, le troisième accès est un défilé ouvert. Ne pas affirmer trois
sprites de porte différents. Les nouveaux contours sont définis dans layouts.py,
pas copiés pixel à pixel depuis le guide généré non conforme.
Les nouvelles collisions bloquent hors-herbe et les éléments d’accès. Trois
chemins avec dégagement 16x16 de l’arrivée au seuil sont contrôlés. Les vingt
anciennes cartes restent byte-à-byte identiques, collisions libres incluses.
Marqueurs `donjon_seuil` fournis mais aucune destination de donjon liée :
`RACCORDEMENT_DONJONS.json` est une fiche non exécutée, pas un téléporteur.
40 chargements par le vrai PMDO 0.8.12 PASS (dimensions, grille, calques,
marqueurs), sans GPU. L’éditeur graphique reste en échec ; ne pas confondre
ce résultat avec un test de rendu, de collisions en mouvement ou de gameplay.
Le manuel exhaustif est `MANUEL_METHODE_PMDO.md`, complété par la notice du lot.


## V6 — demande de repassage des zones et calques forêt/grotte

L’utilisateur demande de repasser les zones assemblées manuellement dans le générateur pour en corriger les défauts sans perdre les compositions. Ne pas écraser les natifs. Dix propositions produites dans `renders/retouches_zones_v6/` ; 01/04/10 à reprendre. Deux kits provisoires dans `renders/entrees_calques_v6/` sont découpés depuis des images antérieures : ne pas les présenter comme les nouveaux atlas générés. La limite réelle de dix générations a empêché ces atlas et les trois reprises. Voir la liste priorisée dans `source/retouches_v6/README.md`. Références TSR Murky Forest/Armaldo et Halcyon Apricorn Grove réellement inspectées. Les nouvelles entrées restent libres en textures PMD ; les retouches Métano gardent ses références de matière.
