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


## Dernière correction — conserver la méthode Métano texturée sur magenta

L’utilisateur rejette le changement de matériau et rejette les layouts plats comme livrable. **Le générateur reprend la roche ET l’herbe Métano avec les références existantes, conserve le layout et génère la falaise texturée sur fond magenta.** Ne pas revenir aux essais V7/V8. Témoin : `renders/falaise_metano_temoin/`. Référence utilisée : `source/falaises_generees/reference_canonique.png`. Vérifier ce témoin avant une génération en série. Ne pas prétendre que les pixels générés sont canoniques ; ne pas remplacer les cartes natives. L’amélioration demandée du cycle océan est encore en attente.


## Caps / Terrasses V3 — dernières variantes face à la mer

L’utilisateur demande des calques comme Terrasse V2 et Cap V2 : falaise latérale, très proche caméra, face à la mer. Six variantes texturées via générateur sur magenta dans `renders/caps_terrasses_v3/`, avec références V2 et Métano, PNG terrain et nuit à 1640×656 sans resampling. La 04 est décalée de 256 px à gauche pour cadrage. Terrain complet séparé de ciel/nuages/océan, pas roche et herbe séparées. `apercu_caps_terrasses_v3.html` montre les calques. La demande antérieure d’océan plus fluide est maintenant réalisée **dans ces exports PNG et cet aperçu** : 64 phases à 50 ms, boucle 3,2 s, interpolation de palette à indices/alpha fixes. Elle n’est PAS intégrée au mod natif existant. Voir `source/caps_terrasses_v3/README.md` et les tests ; ne pas annoncer un nouveau test moteur.


## Dix variantes supplémentaires — Caps/Terrasses V4 audités

Demande : dix autres falaises, vérifier soi-même la roche, la jonction couronne/herbe et la colorimétrie Métano, renforcer la configuration si nécessaire. Dix générées (07–16), dans `renders/caps_terrasses_v4/bruts/`. Références : pose V3 + vrais échantillons natifs + scène canonique. Exports corrigés vers 328 couleurs natives en CIELAB ; zéro couleur hors palette, mais ce test NE PROUVE PAS le motif. Huit dessins retenus visuellement. **07 (galets/chapelet) et 11 (gros blocs/rebord lisse) refusés : prochaine priorité, les régénérer puis réauditer.** Une tentative de reprise 07 a échoué sur la limite de dix générations ; ne pas prétendre qu’elle a été faite. Voir `source/caps_terrasses_v4/README.md`, audits JSON et planche de bordures. Les originaux, six variantes V3 et mod sont conservés. Océan V3 réutilisé inchangé.

## Entrées de donjon — règle permanente des calques (septembre2026)
L’utilisateur rappelle que **toute entrée doit être livrée en plusieurs calques**, pas seulement comme génération aplatie : sol/chemin, végétation basse, arbres ou massif, ombres, profondeur du passage. Fournir aussi une feuille de sprites d’arbres quand demandée. Une image validée ne doit pas voir son layout régénéré pour la découpe.
La première entrée Sakura `renders/entrees_six_donjons_v1/bruts/sakura_printemps_A.png` est explicitement validée. Son pack `sakura_validee/` conserve une recomposition exacte, propose un sol reconstitué sous les éléments, deux arbres isolés détourés, une feuille8px et un OpenRaster multicouche. Les arbres occultés de la lisière ne sont pas prétendus complets. Les ombres peintes restent liées au sol/placement de cette scène. Ne pas attribuer les générations à un artiste humain ni les appeler sprites canoniques récupérés. Les autres bruts du lot restent des propositions, sans validation.

## Dernière correction — layouts de référence, changements subtils seulement
Pour les références ajoutées au commit `8eb46bc`, l’utilisateur demande finalement des layouts « valeur sûre » : reproduire les compositions de référence en plusieurs calques, et limiter les modifications à des changements subtils. Les20 propositions de biomes/layouts générés sont mises de côté, pas approuvées. Ne pas poursuivre les mélanges de zones ou nouvelles géométries pour ce lot sans nouvelle demande.
Livraison : `renders/references_fideles_v1/`,14 zones de référence + le fond nocturne, dimensions et pixels conservés, six micro-variations lumineuses optionnelles, phases GIF natives6/12/30 préservées. Ce sont des partitions de surfaces visibles ; les zones cachées et les objets complets ne sont pas reconstruits. Les autres ressources approuvées restent inchangées. Ne pas annoncer20 nouveaux layouts :14 références +6 micro-variations font20 rendus, pas20 biomes distincts.

## Variantes magenta — dernière demande et ajouts
L’utilisateur autorise à nouveau des layouts **légèrement** différents, avec palettes harmonisées, via référence → générateur sur magenta → détourage → calques → assemblage. Conserver les accès et limiter les modifications locales. Toute eau doit avoir plusieurs phases cohérentes avec la référence ; ne pas livrer un simple fond d’eau statique en prétendant avoir conservé l’animation.
Lot `renders/layouts_magenta_v1/` : quatre layouts/deux palettes (huit bases), puis cinq variantes demandées : deux forêts avec bordures de feuilles, sable avec siphons d’eau, cristal irisé bleu–rose–blanc, côte cendrée avec lave. Les feuillages et effets sont indépendants. RGB des irisations fixe, seule l’opacité varie. Les siphons d’eau et la lave sont des adaptations des cycles sources6/30 phases, pas des animations natives récupérées. Référence cristalline12 phases + reflet24 phases à période identique. « Couleur centre » a été interprété comme gris cendré, à corriger si l’utilisateur précise autrement.
Les anciennes références fidèles, Sakura validée et autres lots restent inchangés. Les sols cachés sont reconstitués pour ces nouveaux layouts, mais pas toutes les faces occultées des massifs. Pas de validation PMDO/GPU ni ajout de collisions/dégâts de lave. Galerie `apercu_variantes_magenta_v1.html` et manifestes décrivent les calques, origines, durées et limites.

## Clarification : canopée immersive et eau intégrale
Les petits rameaux étaient une mauvaise interprétation : demander un cadre continu de grandes masses de feuillage au premier plan comme dans les références Sky. Le sable doit être remplacé **partout** par l’eau, pas seulement dans les siphons ; rochers gris assortis, calques et animations distincts. Correction non destructive dans `renders/corrections_eau_canopy_v1/` : deux forêts avec silhouettes de Southern Jungle fournies au commit46e93da (extraction directe, deux calques latéraux), eau intégrale avec rochers gris, surface12phases et siphons6phases adaptés. Galerie `apercu_corrections_eau_canopy_v1.html`. Anciennes versions conservées, mais elles ne satisfont pas cette clarification. Pas de test PMDO/GPU.

## Côte cendrée — passage et comportement de lave corrigés
L’utilisateur demande que `cote_cendres_lave` devienne un chemin sud → nord, avec lave visqueuse et désordonnée, et colonnes de flammes qui s’élèvent à des emplacements irréguliers sur le passage. Variante non destructive `renders/cote_cendres_passage_v2/` : chemin gris traversant généré sur magenta (deuxième brut corrigé utilisé), nouvelle lave procédurale sans réutilisation des vagues natives, huit colonnes indépendantes à rythmes décalés, 64 phases120ms, 14calques. Galerie `apercu_cote_cendres_passage_v2.html`. Terrain partitionné en surfaces visibles, pas objets complets. Aucun dégât/collision PMDO implémenté ni test runtime/GPU.

## Eau et siphons — courant rapide, palette cycling et chemin
L’utilisateur demande pour `eau_integrale_rochers_gris` une aspiration fulgurante vers les spirales, palette cycling, rochers harmonisés avec l’eau et bordure d’eau animée, ainsi qu’un chemin logique où les Pokémon pourront marcher jusqu’au siphon. Correction non destructive `renders/eau_siphons_rapides_v2/` : chaussée générée sur magenta depuis le sud au palier du grand siphon ; rochers ardoise bleutés, courants convergents, spirales accélérées, vraie rotation de LUT bleu–cyan, écume de rive et reflets indépendants. 48phases40ms, 11calques, ORA, PNG et galerie `apercu_eau_siphons_rapides_v2.html`. Contrôle géométrique avec marge12px et intérieur sec sur toutes les phases ; pas de collisions PMDO ni aspiration des personnages implémentées. Les six poses de cuvettes sont adaptées du sable d’origine, pas des phases natives d’eau retrouvées.

## Correction prioritaire — destination grotte et causalité des éruptions
Pour `cote_cendres_passage`, l’utilisateur précise que le chemin venant du sud doit **mener à la grotte**, pas sortir au nord. Les flammes doivent jaillir **de la lave sur les côtés, jamais du chemin**, et seulement après gonflement puis éclatement d’une bulle. Générer les images clés du magma et des éruptions, puis assembler le layout en plusieurs frames et calques cohérents. V3 non destructive : `renders/cendres_grotte_eruptions_v3/`, quatre images clés de magma générées (planche affinée guidée par Dark_Crater_Pit_TDS), huit poses bulle→rupture→jet→retombée, six sites latéraux décalés,64frames100ms et12calques. Intercalaires par flot optique/quantification, pas l’ancienne animation procédurale V2 ni des vagues recolorées. Aucune éruption ne recouvre le terrain dans aucune phase ; corridor32px jusqu’à la grotte vérifié, pas de runtime/collisions PMDO. Galerie `apercu_cendres_grotte_eruptions_v3.html`. La première planche magma grossière est archivée, non utilisée. Conserver les anciennes versions sans les présenter comme satisfaisant cette clarification.

## V4 — raccord côte/grotte et palette cycling thermique
L’utilisateur signale un mauvais raccord du magma près de la grotte et demande magma/bulles/flammes assortis, avec des frames en palette cycling cohérent physiquement. `renders/cendres_palette_raccord_v4/` ajoute seulement2904pixels de roche au décroché vertical artificiel à gauche de l’approche (ROI107,198–189,294), sans modifier les anciens pixels rocheux. Petit raccord généré sur magenta, comparaison avant/après incluse. Remplacement du morphing V3 par un plan d’indices fixe (16classes thermiques×16phases),64palettes/PNG réellement indexés ; classes froides0–3 RGB fixes, progression de luminosité dans les veines. Magma, bulles et jets partagent16couleurs chaudes, chauffe locale liée à l’événement, grain du magma sur les bulles.64frames100ms,14calques. Galerie `apercu_cendres_palette_raccord_v4.html`. Aucune prétention à une simulation physique : palette cycling = logique visuelle d’incandescence/refroidissement, pas thermodynamique réelle ni écoulement simulé. Aucun test PMDO/GPU/collision. Préserver les versions antérieures, la destination grotte et l’interdiction des flammes sur le chemin.

## V5 — fissures et continuité réelle de matière des éruptions
L’utilisateur demande des fissures de magma dans la roche avec leur propre calque animé, et des bulles/colonnes retravaillées pour sembler faites de la même texture que le magma, pas seulement de couleurs assorties. `renders/cendres_fissures_matiere_v5/` conserve V4 : creux fixes et fissures ramifiées animées dans parois/rebords, corridor central protégé. Nouvelle génération8poses ; rendu par projection de la texture du magma de chaque frame (chauffe locale comprise) sur les silhouettes, étirement/relief borné et égalité des pixels au pied. Extraction de la planche dans son vrai espace inter-rangées à38% pour éviter une pointe de jet parasite sous une bulle. Magma indexé V4 conservé octet pour octet ; 64phases100ms,16calques, ORA/PNG/ZIP et galerie `apercu_cendres_fissures_matiere_v5.html`. Fissures/éruptions contrôlées séparément, aucun jet sur le terrain, ordre causal et corridor inchangés. Pas de PMDO/GPU, collisions ou dégâts. Ne pas présenter cette projection et le palette cycling comme une simulation physique.

## Entrée Apple Woods + reprise des siphons — dernière livraison
L’utilisateur a salué V5 (« bon travail »), puis demandé deux travaux. Il a choisi **la forêt en premier** : layout légèrement différent de `Apple_Woods_entrance_TDS.png` (référence46e93da), herbe style Sky Peak, chemin assorti, arbres indépendants et entrée dans un gros tronc. `renders/applewoods_skygrass_v1/` : sol/chemin générés séparément,20pommiers sur20calques, grand arbre en profondeur/tronc/canopée, ombres et bases feuillues séparées ;26placements floraux issus des4phases natives Sky Peak200ms, pixels conservés et décalages de phase.552×408,30calques, PNG/ORA/ZIP. Galerie `apercu_applewoods_skygrass_v1.html`. La scène est une nouvelle proposition, pas une entrée déjà approuvée ; le contrôle de corridor ne valide pas l’entrée/collision en jeu.
Le deuxième travail est également livré : `renders/siphons_ecoulement_v3/`, nouvelle matière d’eau générée, **neuf** centres de siphons (y compris le petit voisin du principal), chaussée conservée. Champ2D stationnaire par volumes finis/projection de pression, rotation et absorptions, frontières ouvertes, rochers/chaussée imperméables ; conservation de débit et flux solide nul contrôlés. Rendu par advection arrière à deux phases et traceurs, nouvelles ombres de cuvettes, pas les anciennes6poses de sable. Rives bleutées discrètes, opacité des reflets≤28/255.128phases50ms,9calques, PNG/ORA/ZIP. Galerie `apercu_siphons_ecoulement_v3.html` avec animation complète et curseur32échantillons ;128PNG dans le pack. Ce n’est pas une simulation3D de surface libre ni une validation PMDO/GPU. Intérieurs secs et alpha des rochers inchangés.
Aperçu commun : `apercu_pommier_et_siphons.html`. Scripts de reconstruction/vérification dans les deux dossiers source, `package_both.py` pour les ZIP et l’aperçu commun. Les anciennes ressources, variantes et entrées approuvées restent intactes.

## Portraits d’émotion et sprites Pokémon — profil demandé le 16 septembre 2026

Pour tout nouveau portrait/personnage Pokémon, lire `source/pmd_character_pipeline/README.md` et `contract.json` avant génération. Ce profil résulte des deux guides Emmuffin/TawnySoup fournis par l’utilisateur, de SpriteCollab/SpriteBot et de l’organisation Halcyon effectivement inspectée. Il configure le workflow du projet, pas le modèle d’image lui-même.

- Portrait : 40×40, ≤15 couleurs par émotion fond compris, case remplie entièrement opaque ; planche 5×4, vues inversées dans les 4 rangées suivantes si asymétrie. Les contours adoucis sont des pixels opaques choisis dans la palette, pas de l’alpha partiel.
- Sprite : ≤15 couleurs visibles pour toutes les animations ensemble, alpha 0/255 ; PNG Anim/Offsets/Shadow séparés, XML cohérent, 1 ou 8 directions, durées en ticks 1/60s. Les multiples de 8 sont conseillés pour les cellules, pas une obligation universelle de SpriteCollab.
- Génération = référence de dessin. Retouche pixel par pixel et inspection à 1× obligatoires ; une réduction/quantification automatique ne prouve pas la qualité artistique. Valider identité et poses avant de multiplier les émotions/animations. Ne pas appliquer le pipeline des décors (halos alpha, énormes feuilles, etc.) aux portraits/sprites.
- Conserver sources, provenance, crédits et bases verrouillées. Destination initiale : custom du mod, pas soumission publique garantie. L’éligibilité IA au dépôt public n’est pas établie par les documents consultés ; demander confirmation des mainteneurs avant soumission.
- Halcyon emploie `Content/Portrait/<IndexNum>.portrait`, `Content/Chara/<IndexNum>.chara`, données de forme et sélection species/form/skin/gender dans les scripts. Ces archives/index sont produits par le moteur : ne jamais renommer des PNG ou écrire de faux binaires. Exemple vérifié : Sandile 551, forme 1 Scarfed Sandile.
- Exécuter le précontrôle `validate.py` et les tests ; distinguer systématiquement conformité technique, revue artistique, approbation SpriteCollab et test PMDO. Le Pokémon et le mod cible ne sont pas encore choisis dans cette demande de préparation.

Fonds utilisateur ajoutés au commit `bee49f0` : `template.png` (200×320) prioritaire et `Extra_Backgrounds.png` (280×240) pour variantes explicitement mappées. Préserver les originaux. Ce sont des fonds/motifs, pas des portraits finis : quatre cellules Special du template ont de la transparence et Special2 compte 17 couleurs ; composer un fond opaque et vérifier ≤15 couleurs sur le portrait final. Audit dans `source/pmd_character_pipeline/references/user_backgrounds.json`.

## Reprise caractères / Méga — ressources désormais sauvegardées

Suite à la perte de l'ancien Carapagos non poussé, nouvelle source magenta et exports **partiels** dans `source/pokemon_custom/tirtouga_v2/` et `exports/pokemon_custom/tirtouga_v2/`. Idle/Walk uniquement, trois émotions adaptées du Normal crédité, précontrôles minimum PASS mais donjon/complet FAIL attendus. Ne pas annoncer un personnage fini. L'audit actualisé `source/sprite_audit_v2/` recense 46 bases sans sprite, aucune sans Normal, sur SpriteCollab3609a86.

Méga : `source/mega_evolution_v1/`, `renders/mega_evolution_v1/`, galerie `apercu_mega_et_carapagos.html`. 144 phases/4,8s, six atlas RGBA, démo native Dracaufeu→MégaX huit directions, switch opaque, fragments de coque avec décroissance. Emblème flamme/S redessiné depuis une référence secondaire, pas extraction officielle. Tests d'image PASS, **aucun test runtime PMDO**, aucune couverture exhaustive des tailles X/Y/Z-A. Ces atlas ne sont pas des tilesets ; raccord moteur encore absent. Continuer à faire des checkpoints commit/push sur la branche de session, sans prétendre que les 46 Pokémon ou la Méga jouable sont terminés.

## Correction — Méga entièrement reprise au générateur, GIF et Carapagos V1 préféré

L'utilisateur veut reprendre **tous les composants visuels Méga au générateur**, avec cycling fluide, plusieurs phases et layouts multidirectionnels ; GIF pour chaque animation, portraits aux fonds canoniques. Il préfère le **premier sprite Carapagos (V1)**, pas V2. Ne pas étendre aveuglément V2 ni annoncer une régénération comme une récupération.

Reprise : `source/mega_evolution_v2/`, `renders/mega_evolution_v2/`, galerie autonome `apercu_mega_generee_v2.html`. Quatre planches8clés utilisées,5e essai de fracture rejeté conservé ; cycles48phases au flot optique, rupture43phases, séquence192phases/6,4s, six calques,15GIF incluant8directions et2archives CarapagosV2. Layout8directions×12instants. Personnages natifs Dracaufeu/X, masques avant/arrière approximatifs, aucune validation PMDO ni toutes-tailles. Ne pas appeler les inbetweens des dessins manuels ou le cycling des images un format natif LUT PMDO.

Portraits `tirtouga_portraits_v3` : cinq sources générées séparément Happy/Angry/Sad/Shouting/Surprised, palette choisie (bouche rose explicitement réservée), retouches sourcils,40²opaques,13–15couleurs ; fonds `template.png` **inchangés pixel pour pixel là où visibles**, Normal original byte-identical. MinimumPASS,10émotions obligatoires encore absentes ; pas d'approbation artistique.

Récupération V1 : recherche /home/user, stash (y compris untracked), historique des dossiers, git fsck full sans objets orphelins ; aucun fichier V1 retrouvé. Rapport `source/mega_evolution_v2/recovery_carapagos.md`. L'utilisateur doit fournir une copie de l'image de l'ancien échange pour reprendre exactement son dessin préféré. Les GIF V2 sont marqués archives, pas V1 récupérée.

## Carapagos — choix de base confirmé et premier lot complet à poursuivre

L'utilisateur a choisi **reconstruction depuis les portraits validés** (et non V1 à attendre ou V2 à prolonger), et a confirmé « Toute les animations ». Il valide les cinq portraitsV3 ; ils sont déjà sur les fonds canoniques et leurs hashes sont dans `source/pokemon_custom/tirtouga_portraits_v3/approval.json`. Ne pas les régénérer ni modifier leurs fonds.

`source/pokemon_custom/tirtouga_v4/`, `exports/pokemon_custom/tirtouga_v4/`, galerie `apercu_carapagos_v4_animations.html` : premier lot **22/32actions du profil complet**, dixdonjon en8directions, douzescènes en1vue. Sourcecorpsofficiel+portraitsvalidés, caméranativeTorkoal ;15couleursglobales,cellules64²,XML/triplets/GIF,ZIPplat. Minimum/donjonPASS,completFAIL attendu ;les nouveaux sprites ne sont PAS approuvés artistiquement et aucun testPMDO.

Limite10générations atteinte ; deuxplanches refusées, à produire au prochain tour : Scenes_C(Pose,Pull,Pain,Float,Sit,Sink) et Scenes_D(Laying,LeapForth,Head,Cringe). Pas de fausseactionIdle pour les remplir. `next_batch.json` / `production_plan.json` suivent ce mandat ; ne pas redemander s'il faut les faire. Priorité aussi à la revue/retouche des proportions entreactions et desmarqueurs en roulade ; certainsdessins sources de scène avaient dérivé en illustration. Les erreurs dedirection sont explicitement écartées, plusieursposes réutilisées sont déclarées (Double=deuxfrappesAttack,Rotate=huitvues,Hop=deuxphasesenl'airpartagentledessin). Portraits approuvés ≠ spriteV4 approuvé.

Le GIF MégaDracaufeu demandé est `renders/mega_evolution_v2/gifs/mega_0.gif`, ouvert directement avant le travail, également intégré à la galerieV4. Conserver cet effetV2 sans nouvelle modification non demandée.

## Correction bloquante — identité de Terapagos Stellaire

Le17septembre2026, l'utilisateur rejette `source/pokemon_custom/next_species/generation/terapagos_stellar_idle_views.png` : cette forme ne ressemble pas au vrai Stellaire. **Ne pas exporter/animer cette planche.** L'art officiel correct était déjà fourni au générateur et dans le dépôt ; le résultat a été présenté sans rejeter ses erreurs. Références désormais vérifiées : PokeAPI/sprites `official-artwork/10277.png` (identique au commit9d7c667...), SpriteCollab `portrait/1024/0002/Normal.png` et `Normal^.png` (3609a86...). README/audit dans `next_species/references/terapagos_stellar/`. Présentation officielle sur fond sombre, pas image régénérée. Globe sombre multicolore facetté, vraie couronne/ornement cristallin, tête/nageoires/queue conformes ; pas boule cyan et étoile inventée. Refaire une vue fidèle avant multidirectionnel ; préserver asymétrie des joyaux. Pas de sprite0002 dans la révision vérifiée, ne pas substituer Terastal0001.

Travail Carapagos interrompu mais sauvegardé : V5sprites32actions, portraitsV4 seizeémotions, complets techniquesPASS ; galerie/regroupement final V5 et revue artistique encore à faire. Anciens portraits approuvés inchangés. Zarude : premier brut disponible, non exporté/non approuvé, case ouest mal orientée à corriger. Le mandat reste Carapagos à finaliser puis Zarude/Stellaire et autres manquants, sans prétendre ces autres Pokémon terminés.

## Ajouts demandés ensuite — Méga-Raichu X/Y et transformations

Le17septembre2026, l'utilisateur ajoute **Méga-Raichu X et Méga-Raichu Y**, ainsi que les animations de transformation **Dynamax, Gigamax et Téracristallisation**. Ce sont des travaux à suivre, pas des livrables déjà réalisés. Ordre conservé : finalisation/revue/galerie Carapagos, Zarude, reprise fidèle de Terapagos Stellaire, puis ces ajouts. Plan durable : `source/pmd_character_pipeline/production_roadmap.json`.

Vérifier les références exactes et les ressources existantes pour chaque Méga-Raichu ; ne pas inventer une forme depuis Raichu normal/Alola ni faire une simple recoloration X→Y. Dynamax : transition de taille et retour, sans confondre agrandissement visuel et intégration moteur. Gigamax : véritable forme spécifique de l'espèce, pas seulement sprite géant ; espèce de démonstration encore à choisir. Téracristallisation : cristallisation et couronne du type pertinent ; annoncer les types effectivement couverts, pas un système universel fictif. Ne pas confondre cet effet générique avec l'anatomie de Terapagos Stellaire.

Même méthode demandée : images clés au générateur contrôlées contre les références, PMD pixel art, phases fluides/cycles pertinents, calques indépendants, ancrage/enveloppes avant-après et revue huit directions, GIF par séquence. Palettes/alpha des personnages séparés des VFX. Pas de revendication de test PMDO, d'approbation artistique ou de ressources complètes avant vérification réelle.

## Priorité actuelle — transformations et accessoires anatomiques (17 septembre 2026)

La demande détaillée ultérieure de Dynamax/Gigamax/Téra a pris priorité sur la file précédente. Correction explicite : **couronnes sans tête/visage intégré**, adaptées individuellement à la tête de chaque sprite existant, pas un placement universel. La promesse de retirer aussi les yeux du joyau a été appliquée ; ne pas appeler ces variantes des copies canoniques pixel-exactes.

Prochain livrable visuel désormais assemblé : `apercu_transformations_v1.html`, `exports/transformations_v1/README.md`, build/verify dans `source/transformations_v1/`. Dracaufeu : 24 transformations GIF (Dynamax, vrai Gigamax 0006/0003, Téra Feu ×8directions) et 24 boucles d'état, chacune240phases/8s ; sept calques pour D uniquement. 168masquages opaques,1920reflets sans débordement,24raccords périodiques,48duréesGIF et hashes natifs vérifiés. Composants générés + interpolation + chorégraphie calculée ≠240dessins manuels. Gmax natif a une pose Idle statique/direction.

**Pas de test PMDO réel, pas toutes espèces, pas tous types, pas toutes occultations anatomiques.** Six profils locaux seulement dans `crown_attachment/` ; poses ambiguës bloquées. Feu/Eau accessoires statiques provisoires, Feu seul animé dans le nouveau pilote. Autres17couronnes statiques absentes. Continuer l'adaptation et les gates runtime sans effacer la file Carapagos/Zarude/Stellaire/Méga-Raichu X/Y, les originaux ou les portraits approuvés.

## Dernière demande — Téra V2 et périmètre de la file confirmé

L'utilisateur demande la correction des couronnes **via génération**, les types manquants, des reflets de verre prismatique animés pour tous les sprites SpriteCollab et les ressources manquantes. Il a choisi explicitement **la liste du projet** pour les portraits/sprites, pas tous les absents mondiaux.

Lot `source/tera_v2/`, `exports/tera_v2/`, `apercu_tera_v2.html` : dix générations réussies de couronnes, propositions pour19types. Feu4cardinals/Eau8vuesprovisoires/autres17frontuniquement. Vol compte de ballons incorrect ; Stellaire refusé (statuette non fidèle, dans review/rejected_models). Aucun porteur intégré, bijoux frontaux sans yeux ; motifs inhérents crâne/œil/masque/fantôme distincts. Ne pas annoncer19couronnes canoniques achevées ou les plaquer universellement.

Nouveau verre :59plancheslocales×24phases +12planchesdistantes×24, alpha/RGBtransparent/XMLnatifs conservés ;11testsunitairesPASS. Toute source du catalogue peut être chargée à la demande par `catalogue_surface.py`, mais **55953planches indexées ≠ toutes rendues ou intégrées**. Inventaire complet984racines/3337XML,55941planchesdistantes non rendues ; aucunshaderPMDOinstallé/testé. Revue Feu+verre16placementsproposés, pas toutesanatomies.

Deux tentatives supplémentaires Zarudeouest/Stellairecorps bloquées par limite10générations : aucunnouveausprite/portrait de la file dans ce tour. Carapagos32actions/16portraits regroupés sans compter d'art nouveau ;6originauxpréservés. Méga-RaichuX/Y **retrouvés** dans0026/0002 et0003 : Normal natif existant avec crédits, à préserver ;15émotions requises manquantes chacun, corps officiel complet à vérifier. Stellaire15émotionsmanquantes, Zarude0sur16, tousspritesàproduire/corriger. `project_queue.json` garde aussi46espècesbase sanssprites. Ne pas remplacer les portraits déjà présents ou faire passer l'inventaire pour une production terminée.

## Dernière correction de périmètre — totalité de SpriteCollab

L’utilisateur précise explicitement : « la totalité des créations absentes de SpriteCollab, faudra tous les faire ». Cela **annule le précédent choix limité à la liste du projet**. La priorité est désormais le catalogue complet, sans abandonner Carapagos/Zarude/Stellaire/Méga-Raichu. `exports/spritecollab_global/` inventorie les 5 640 slots de la révision3609a86 (HEAD upstream revérifié), y compris variantes et entrées non requises. `source/sprite_audit_v2/global_backlog.py` distingue absences complètes, incomplets upstream, émotions du contrat et états/pending. Les 32actions du projet ne sont PAS automatiquement les exigences de chaque entrée SpriteCollab. Ne pas annoncer tous les Pokémon faits à partir d’un audit ni d’images brutes. Préserver crédits, originaux et propositions en attente ; pas de flips automatiques des asymétries.

## Règle portrait la plus récente — Normal anatomiquement fixe

L’utilisateur rejette les expressions générées de Terapagos Stellaire : **ne pas poursuivre cette planche** (`terapagos_stellar_emotions_v1.png`), conserver Normal/Normal^. Pas d’annulation déduite du travail de sprite entier. Méga-Raichu X/Y et, par règle générale, les futures expressions doivent conserver les traits et l’anatomie exacte du portrait Normal : proportions/silhouette du visage, museau/nez, joues, implantation/design des yeux, oreilles/marquages. Faire jouer naturellement paupières, sourcils et bouche, pas redessiner le faciès. Une expression test avant une planche.

Contrat et make_prompt mis à jour avec référence Normal obligatoire et blocage portrait1024/0002. Deux études Happy contraintes ont été produites pour X/Y ; comparaison `exports/pokemon_custom/portrait_identity_v1/comparison.png`. Tous les pixels hors masques yeux/bouche restent ceux du Normal, palette native ; **pas d’approbation artistique ni de pack d’expressions final**. Le fond Normal est conservé pour étude, pas présenté comme fond Happy final.

## Expressions animales, Carapagos et vrais fonds canoniques

L’utilisateur interdit à Raichu les expressions humaines (mordillement de lèvre, dents visibles). Pas de lèvres, dents, grimaces ou plis humains inventés ; petites expressions de museau animal, douleur via paupières. La même méthode d’anatomie Normal fixe doit s’appliquer à Carapagos, **sur fonds canoniques**, sans remplacer ses six portraits approuvés. Les Pain Raichu V2 autorisant des dents dans le prompt sont écartés au profit de Pain_animal_v3.

Lot `canonical_expressions_v1` : fonds exacts de chaque émotion de template.png, sujet natif conservé hors régions yeux/bouche, bec/narine de Carapagos entièrement intacts. 12propositions,10passent40²/15couleurs/alpha ; Angry/Surprised MégaY à16couleurs bloqués hors exports individuels, pas de quantification silencieuse des traits fixes. Galerie `apercu_expressions_canoniques_v1.html`. Les passages techniques ne valent toujours pas approbation artistique ni validation PMDO.

## Carapagos — expressions de face complétées avec la méthode Normal fixe

Dernier lot : `apercu_expressions_canoniques_v2.html`, `exports/pokemon_custom/canonical_expressions_v2/`. Huit nouvelles expressions individuelles ont porté Carapagos à16émotions de face :6originaux approuvés conservés +10propositions anatomiquement bornées depuis Normal. Œil seul modifiable, bec/narine et contour du visage intacts ; fonds canoniques par case. Contrôle technique completPASS, pas de doublons exacts parmi les nouveaux sujets avant fond. **Pas de nouvelle approbation artistique, pas de vues inverses ni testPMDO.** Méga-Raichu repris sans nouveau contenu dans ce lot, deux portraitsY16couleurs toujours bloqués. Ne pas reprendre Terapagos Stellaire portraits.

## Priorité la plus récente — les neuf membres de guilde de la quête PMDO

Prioriser désormais Gardevoir, Farfetch’d, Pancham, Bagon, Shroomish, Happiny, Pachirisu, Weavile, Politoed. Le chantier global reste en file, pas annulé. Audit `exports/guild_members_audit/README.md` et `audit.json` : tracker3609a86 HEAD revérifié, vrais listings/XML/CopyOf et triplesIdle contrôlés, crédits natifs préservés. Aucun testPMDO ni création dans cet audit.

Seul Politoed manque d’émotions parmi16 :12à produire, conserver Normal/Inspired/Shouting/Surprised. Tous les neuf ont donjon10. Bagon/Happiny/Pachirisu base ont32actions du profil ; les six autres manquent chacun22actions de scène du profil projet (132au total dans les bases), pas forcément toutes utilisées par la quête. Gardevoir Cutscene possède notamment Pose/StandingUp/Jump/Special0–3 ; Weavile Cutscene possèdeSpecial0–1 : examiner avant régénération. Pachirisu femelle n’a pas les mêmes scènes que sa base. Pas de forme/gender/Galar/Méga substituée sans indication.

Correction Carapagos réaffirmée : ses portraits approuvés **à bouche ouverte étaient bons**, car référencés canoniquement sans dents visibles. Les préserver. La règle n’est pas « bec toujours fermé » ; une ouverture anatomiquement naturelle du bec est autorisée lorsque l’émotion et la référence la justifient. Adapter le masque à cette articulation, ne pas bloquer tout mouvement à cause d’un masque conçu pour une expression fermée.

## Suite ordonnée par l’utilisateur après les manques de guilde

Produire les manques audités des neuf membres, **puis seulement quand ils sont terminés** : (1) animations spéciales de diva pour la Team Dazzling composée ici de **Lopunny/Lockpin, Mawile/Mysdibule, Tsareena/Sucreine** — ne pas substituer une autre composition canonique ; (2) animation de lancement de combat fondée sur la **véritable transition canonique PMDO**, à inspecter avant toute reconstruction et à distinguer du test moteur ; (3) retour aux créations de maps avec textures canoniques et méthode précédente. Les anciens autres manquants restent en file, non annulés. Aucune des trois nouvelles étapes n’est déjà produite ou une tâche lancée en arrière-plan.

## Workflow portrait impératif — magenta puis fonds canoniques

L’utilisateur précise que le **générateur doit produire les portraits sur fond magenta**, avec des expressions naturelles animales compatibles avec l’anatomie ; détourer ensuite et placer sur le vrai fond canonique de l’émotion. Ne plus demander au générateur de peindre ou conserver le fond canonique. `make_prompt.py`/contrat sont corrigés pour distinguer source magenta et composite final opaque40²/15couleurs. Préserver les vraies joues/marquages roses lors du détourage.

Tarpaud : `source/pokemon_custom/politoed_portraits_v1/generation/Happy.png` est rejeté (ancien fond et deuxième sourire humain sur la mâchoire jaune). Nouveau lot `*_magenta.png` :10sources reçues, Sigh/Stunned bloqués par la limite10générations. Nettoyage : alpha depuis le magenta, seules régions de l’œil/larmes prélevées sur Normal ; bouche naturelle à la jonction vert/jaune conservée, aucun sourire supplémentaire. Fond de chaque émotion extrait pixel-exact de template.png. Galerie `apercu_tarpaud_portraits_v1.html`, exports14portraits =4natifs byte-preserved +10propositions. Aucun art approuvé ni testPMDO ; 2émotions et les scènes des membres restent à faire avant Team Dazzling/transition/maps.

## Dernière préférence Tarpaud et premier lot de scènes

L’utilisateur préfère **le lot V1 poussé en ac15d0fa** aux essais V2 de visages entiers. Préserver V1 ; ne pas utiliser V2 Sigh/Stunned pour combler les trous. Exception ciblée : **Dizzy avec véritable spirale continue** (étourdi façon KO), et **Special0 applaudissant, yeux fermés, bouche ouverte** naturellement à la jonction vert/jaune. V3 conserve 13 portraits V1 byte-identiques, remplace Dizzy et ajoute Special0 ; fond optionnel explicitement choisi dans Extra_Backgrounds.png rectangle40,0,80,40. Générateur puis détourage/nettoyage ; la spirale finale est une retouche pixel manuelle explicite, pas des anneaux concentriques générés acceptés tels quels. Ajouts proposés, pas art-approuvés. Sigh/Stunned restent absents.

Priorité actuelle : animations manquantes de guilde. `exports/guild_scene_animations_v1/` conserve toutes les animations de base de Gardevoir/Dimoret et ajoute les ressources Cutscene authentiques (7actions Gardevoir, 2Dimoret), crédits séparés et triples natifs inchangés. **Special1 Gardevoir doit matérialiser l’Appeal Cutscene, différent de l’Appeal de base** ; ne pas garder un alias qui sélectionnerait le mauvais dessin. Un seul manque du profil générique est couvert par cette réutilisation : Pose. Special0/1 Dimoret ne sont pas artificiellement renommés Nod/Pose.

Nod Gardevoir : candidat **de face uniquement**, 3dessins sur5étapes, têtes générées de la première ligne puis palette native et corps/repères immobiles. Les sept autres vues générées sont incohérentes et rejetées ; pas de faux Nod8directions. Les deux packs passent le précontrôle donjon local, pas d’import/runtimePMDO ni d’approbation artistique. GIFs et galerie `apercu_guilde_scenes_v1.html`. Continuer les manques avant Team Dazzling/transition/maps ; ni132lacunes ni catalogue entier ne sont achevés.

## Animation manquante ≠ geste générique — morphologie, DA, identité

Dernière précision explicite : **les animations manquantes des membres doivent être adaptées à la morphologie, à la DA et à l’identité de chaque Pokémon**, exemple **Gardevoir mange avec un geste raffiné**. Cela concerne toute la gestuelle, pas seulement une palette propre à l’espèce. Ne pas remplacer la production Eat/Nod/Sit/etc. par la collecte de Specials sans rapport ; ne pas appliquer le même rebond/mouvement de bras à tous. Articulations/appendices réels, proportions et DA PMD natives, intention et retour au repos propres au personnage. Balignon ne reçoit aucun bras ; Canarticho utilise ses ailes ; Tarpaud conserve des mouvements de grenouille. Préserver les ressources complètes de Draby/Ptiravi/Pachirisu.

Premier exemple V2 : `apercu_gardevoir_eat_v2.html`, Eat Gardevoir de face en8étapes. Génération avec défauts (4×2 au lieu de3×2, première main inversée, visage trop humain) : extraire/nettoyer uniquement bras/baie, corriger continuité de main, conserver visage/robe natifs et animer le repère de main rouge. Candidat techniquement contrôlé ; sept directions manquantes, art et PMDO non approuvés. Le lot V1 reste intact, les autres membres ne sont pas annoncés terminés.

## Récupération effective — V5 poussée, nourriture séparée

Les anciens commits locaux871541fb/05997d93/8dc0508b n’étaient pas récupérables dans le checkout restauré ni dans le dépôt distant. L’utilisateur a demandé de reconstruire. **Nouveau lot V5**, pas une restauration byte-identique : Gardevoir Eat/Nod et Balignon Eat,16étapes ×8vues,27GIFs, sans nourriture intégrée. Premier push confirmé **adb28898** sur la branche de session. Dossiers `source/guild_scene_recovery_v5/`, `exports/guild_scene_recovery_v5/`, galerie `apercu_guilde_reconstruction_v5.html`.

Reconstruction explicitement au pixel sur les8anatomies natives, inspirée des études V1/V2 encore conservées ; pas de nouvelle génération revendiquée. Visages/robes/directions natifs, bras articulé de Gardevoir, corps incliné de Balignon sans bras, ombres et pieds fixes. Art/runtime toujours non approuvés. Les autres manques ne sont pas terminés :128actions du profil32 encore sans cycle local.

Références Halcyon récupérées à nouveau et vérifiées : vrai Eat48 des .chara286/408/531 (première séquence4frames), script de dîner Eat141–152, émote eating154–165, objets Food_*168–180. **Ne pas dessiner la nourriture dans le personnage** ; conserver des entités de scène distinctes. Références/archives hors packs. GFXParams commence par None0, donc Eat48, pas47 ou l’Index interne XML. Pas d’audit exhaustif de tous les candidats ou de test moteur déduit de ces lectures.

## Nouvelle demande — structures PMD/Halcyon et végétation animée

L’utilisateur demande en plus plusieurs sprites de structures / QG de guilde type **treehouse**, avec textures PMD, puis explicitement des **tilesheets de végétation animée comme Halcyon**. Les questions de composition des bâtiments ont été passées : ne pas prétendre qu’un plan de QG est choisi/approuvé. Le kit environnemental est demandé en parallèle ; les manques de personnages restent ouverts.

Premier lot `source/vegetation_treehouse_v1/`, `exports/vegetation_treehouse_v1/`, galerie `apercu_vegetation_treehouse_v1.html` :8plantes originales (herbe, fougère, fleurs violettes/dorées, buissons rond/baies, branche/lierre), empreintes32×32 sur grille8px,4phases0/1/0/2,14ticks chacune.4PNG128×64, atlas512×64, TSX animé avec128sous-cases, recette de placement PMDO,32PNG individuels, poses éditables et11GIFs dont1référence Halcyon. ZIP livré à côté. Pas de faux .tile ou d’import/runtime revendiqué.

Référence réelle : Vast Steppe de Halcyon working-copy1522c7a8. Palette et cadence inspectées depuis les ressources natives déjà conservées. Générateur magenta puis détourage/échelle native/palette/ancrages fixes. Les variations erronées de branches et de fleurs dorées sont réarticulées depuis le neutre, pas acceptées comme poses valides. Pivots sol/suspension fixes ; palettes sémantiques contre les franges violettes. Contrôles locauxPASS, art et PMDO/Tiled non approuvés. **Les bâtiments/QG treehouse ne sont pas encore dessinés** ; ne pas annoncer ce kit de végétation comme le lot de structures terminé.

## Eat neuf membres — V6 et sélection du programme complet

L’utilisateur retient **toutes les propositions déjà présentées pour la guilde** : QG treehouse/bâtiments et annexes, végétation animée et programme d’animations. Cela remplace l’absence de sélection de programme, pas la validation artistique d’un plan inédit. Les bâtiments restent à produire ; aucun runtime n’est déclaré approuvé.

`exports/guild_eat_all_v6/`, `source/guild_eat_all_v6/`, `apercu_guilde_eat_tous_v6.html` : **9/9 membres disposent de Eat**. Quatre nouveaux candidats16étapes×8vues (Canarticho/Pandespiègle/Dimoret/Tarpaud), deux cycles V5 conservés byte-identiques (Gardevoir/Balignon), trois Eat natifs **une seule vue,4frames** conservés avec XML/PNG exacts (Draby/Ptiravi/Pachirisu). Pas de huit directions fictives ni de nourriture ajoutée. 57GIFs ;9précontrôles donjonPASS ;82tests de régressionPASS. Articulation native guidée par quatre études générées, cadences adaptées aux espèces, pas des feuilles générées brutes acceptées. Accessoires visibles, pieds/ombres et palettes contrôlés ; feuille de Pandespiègle naturellement occultée dans U/UL. Art nouveau non approuvé ; PMDO NOT TESTED.

Suivi actuel : `exports/guild_eat_all_v6/production_progress.json` et `PROGRESS.md` :156actions natives,1Pose Cutscene réutilisée,7cycles techniques produits, **124actions du profil32 encore sans cycle local**. Les anciens bilans128 restent historiques. Les cartes ajoutées par l’utilisateur en9ec9a081 sont inchangées.

## Structures puis audit des derniers ajouts de zones

Nouvelle priorité utilisateur : structures de guilde d’abord, puis examiner toutes les zones des derniers commits, identifier leurs BG et appliquer la méthode multi-layers en **changeant seulement les layouts, pas les textures canoniques des maps**.

Premier lot `source/guild_structures_v1/`, `exports/guild_structures_v1/`, ZIP et `apercu_structures_guilde_v1.html` :5 propositions QG treehouse/dortoir/réfectoire/infirmerie/atelier-réserve. Génération guidée par références natives puis alpha/taille/palette natives ; **les textures des structures sont générées, pas pixel-exactement extraites**. Ombres/architecture/toiture-foliage/fumée fixe séparées ; certains calques optionnels vides. Pas d’intérieur derrière toit reconstruit, ni collision/import validé. Ponts et végétation antérieurs restent réutilisables. Le reste du programme retenu reste ouvert.

`source/zones_bg_audit_v1/audit.py`, `exports/zones_bg_audit_v1/audit.json`, `AUDIT.md`, `apercu_zones_bg_audit_v1.html` : inspection visuelle des23PNG de9ec9a081 et lecture réelle des2maps de3d801c76, hashes/originaux inchangés.12terrains,2BG purs (aurore, mer nocturne),3mixtes,2intérieurs,2planches à deux panneaux,1doublon exact forêtglomy/P21P02A,1afficheUI hors terrain. Les intitulés sont descriptifs, pas une identification officielle certifiée. Les références anciennes hors ces commits ne sont pas annoncées auditées à nouveau.

Les deux .rsground ont `Background.BGAnim.AnimIndex` vide ; leur ciel utilise `00_ciel` dans les tiles. `Cloud/nuage` contient plusieurs feuilles de terrain/objets, ne pas le déclarer nuages animés à partir du nom. Ne pas modifier ces maps pendant l’audit. **Aucun relayout produit dans ce lot** : prochaine étape extraire les vrais matériaux, préparer nouveau layout et layers indépendants, puis tester entrées/collisions/occlusion. Ne pas déduire une animation de deux panneaux sans vérifier leur sens.89testsPASS (82anciens+7nouveaux), aucune validation moteur.

## Premier lot de relayouts aux pixels natifs — V1

Sur « lance toi ! », deux candidats produits dans `source/zones_relayout_v1/`, `exports/zones_relayout_v1/`, galerie `apercu_zones_relayout_v1.html`. Forêt/grotte blanche768×360 (7layers) et couloir rocheux bleu768×360 (4layers). Guides générés puis **aucun pixel généré dans les exports** : NPZsource_xy pour chaque layer, égalité exacteRGBA source vérifiée, pas de recoloration/mirror/rotation/échelle. Sol homogène par patches natifs avec coutures sans fondu ; falaises entières, pas de fragments8px aléatoires.

Forêt : falaise complète source288,0,600,216 déplacée à456,0 ; traces de terre en courbe, masses d’arbres/buissons et pierres repositionnées. Pied de falaise d’origine masqué : couverture végétale conservée et raccordée par bandes natives80px chevauchées, pas de faux pied inventé. Passage bleu : paroi240px répétée, crête avant reculée72px ; reste **droit**, coude du guide non implémenté faute de retours natifs. Une différence native au bord623,160 dans la répétition240px, original non « corrigé ».

96testsPASS, dont7nouveaux. TSX8px descriptifs, PNG et ZIP ; aucune collision/import/runtime validée. Parcours orange indicatif seulement. Le rapport d’audit précédent «0relayout» reste historique ; suivi actuel `exports/zones_relayout_v1/production_progress.json` :2candidats, doublonforêt couvert par même source, autres zones/BG purs toujours à produire. Aucun achèvement global de la guilde déduit.

## Lot02 — arène de glace, nuit, aurore

Nouvelle relance « lance toi ! » : `source/zones_relayout_v2/`, `exports/zones_relayout_v2/`, ZIP et `apercu_zones_relayout_v2.html`. **1nouveau terrain (arène768×480,6layers),1BG réagencé (nuit456×240,8layers),1BG préparé sans relayout (aurore264×216,5layers).** Ne pas annoncer trois maps jouables ou une animation.

Arène : modules natifs192px à hauteur d’origine, crête avant reculée72px, vraie neige unie source100,248 ; fissures déplacées. Aiguilles lointaines connectées à leur vraie teinte111,159,231, pas extraction de tous les pixels bleus des parois. Relief caché non reconstruit : plans arrière liés.

Nuit : nuages hauts déplacés+16,-8 et+64,+8 ; lune/halo/reflet/récif fixes. Déplacer le récif révélait une zone native non fournie : tentative abandonnée. Ciel découvert derrière les nuages reconstitué depuis les lignes dégagées du halo natif selon rayon ; RGB réellement prélevés, mais **pas pixels cachés authentifiés**. Pas de fausse animation. Aurore : recomposition EXACTE de l’original,5calques ; pointes masquées contre référence, pas de brume cachée derrière elles.

19PNG de calques,19NPZsource_xy,19TSX8px descriptifs. Originaux9ec9a081 byte-intacts ;104testsPASS (96anciens+8nouveaux). Galerie/ZIP, mais PMDO/Tiled non testés, art non approuvé. Suivi actuel `exports/zones_relayout_v2/production_progress.json` :3terrains candidats cumulés,1BG réagencé,aurore seulement préparée et toujours en attente de layout. Les autres zones/BG et programme guilde restent ouverts.

## Correction explicite — pas un élargissement horizontal : sud vers nord, grotte et layers

L’utilisateur exige de terminer le programme et corrige les références forêt/passages : **arrivée SUD, chemin vers grotte au NORD**, avec plusieurs calques de sol/chemin/arbres/parois/entrée et matériaux canoniques. Les deux V1 horizontales ne sont pas conformes ; ne plus les compter comme répondant à cette direction. Conserver l’historique mais utiliser le suivi V3.

`source/zones_south_north_v3/`, `exports/zones_south_north_v3/`, `apercu_entrees_sud_nord_v3.html` :2propositions corrigées — forêt512×640,9layers ; passage bleu512×408,8layers. Forêt : terre continue, falaise blanche et grotte de la référence, complément natif Vast Steppe pour de vrais arbres entiers (troncs/canopées séparés). Bleu : la référence horizontale n’a PAS de grotte ; portail ouvert et retours natifs du panneau droit undergroundpmd, clairement signalés, chemin/masses nord de rockroadpmd. Ne pas présenter un portail maçonné comme une bouche naturelle extraite de rockroadpmd.

Pixels multi-sources exacts avec NPZsource_sxy ; aucune recoloration, rotation, miroir ou échelle. Modulation de sol par chevauchements natifs, parois/arbres par modules. Masque de chemin connecté sud→entrée et dégagement8px vérifiés ; cela ne prouve pas les collisions/warps/occlusion moteur.11nouveaux testsPASS, art et runtime non validés. Registre `FULL_PROGRAMME_STATUS.json` : toutes23références,2corrigées,1BG candidat,18layouts encore ouverts/revoir,1doublon,1UI. Aurore seulement préparée ; direction de l’arène à revoir. Donneur natif≠son relayout produit. Programme guilde complet toujours ouvert.

## Demande suivante — zones animées, arène glaciaire et aurore

Après « Parfait » sur les entrées sud–nord, l’utilisateur demande des zones avec animations, exemple arène de glace avec aurores canoniques animées en BG et décor. Premier exemple livré dans `source/ice_arena_aurora_v1/`, `exports/ice_arena_aurora_v1/`, ZIP, galerie `apercu_arene_glace_aurores_animees_v1.html`.

Arène512×720, approche sud vers zone centrale/nord,8calques statiques. Aurore et étoiles séparées :64étapes6ticks=6,4s,128PNG264×216,2atlas8×8,2GIFs et2WebP sans perte. Terrain immobile. Rubans : décalages verticaux par colonne, jusqu’à6px, RGBsources exacts/NPZparphase ; étoiles : formes/RGB natifs, alpha178..255. Pas de neige/inventaire de fausses phases natives.

**Distinction impérative : dessin canonique, animation NOUVELLE proposée.** Arbres complets Halcyon/DumpAsset/PMDODump inspectés, pas de cycle correspondant identifié ; `Aurora_Beam_Custom` est une attaque. Recherche enregistrée avec SHAtree, pas preuve d’absence exhaustive. L’utilisateur a été averti avant génération du mouvement. Ne pas prétendre avoir extrait le cycle original du jeu.

10tests dédiésPASS : coordonnées sources, boucle fermée, pas maximal1px entre phases, alpha étoiles seulement, terrain invariant, atlas/PNG/GIF, accès central sans glace superposée. Masque neige≠collision. Pas d’import/warp/parallaxPMDO validé ; autres zones/programme guilde ouverts. Exemple arène sans grotte ajoutée, pas une entrée de donjon annoncée achevée.

## Correction de méthode — rendus générés, PAS assemblage de bouts de maps

L’utilisateur rejette la méthode appliquée à la dernière arène : « méthode que tu avais fais dans render genere, pas des bouts de map ». **Pour cette demande et les prochains rendus concernés, revenir à la composition générée complète, pas à une mosaïque de prélèvements même vérifiée pixel-exacte.** Les règles spécifiquement imposées à Métano restent distinctes ; ne pas généraliser leur contrainte de copie native à tous les rendus générés demandés.

Pipeline retrouvé : `source/layouts_magenta_v1/WORKFLOW.md` et build.py, terrain Northern magenta. Nouveau lot `source/arene_glace_generee_v2/`, `renders/arene_glace_generee_v2/`, ZIP et `apercu_arene_glace_generee_v2.html`. Deux générations complètes : terrain cohérent sur magenta et sol sous les reliefs. Normalisation512×640, alpha/nettoyage,7calques terrain +2fond, masques, ORA éditable,128PNG animés, GIF/WebP6,4s. **Terrain redessiné référencéPMD, pas pixels natifs certifiés.** Aucun morceau de map n’est utilisé pour reconstruire le terrain de ce lot.

Aurores et étoiles reprises byte-identiques du lot précédent ; dessin canonique mais mouvement original proposé, toujours PAS cycle officiel récupéré. Rendu unique reconstitué exactement par les plans ; sol caché généré, faces cachées des reliefs non complétées pour mouvements arbitraires. Les calques restent des plans éditables d’une composition, pas une banque d’objets tous indépendants.11tests dédiésPASS, JavaScript syntaxe contrôlée ; runtime/collisions non validés.

Cette arène remplace la méthode terrain de `exports/ice_arena_aurora_v1`, conservée historiquement. Ne pas continuer cette méthode rejetée sous prétexte de fidélitéRGB. Les autres zones ne sont pas déclarées terminées et les validations antérieures ne sont pas effacées implicitement.

## Correction arène large V3 — ciel séparé et aurore wrap

Dernière demande : « regenere le ciel sur un layer + aurore en wrape overlay loop parfaite et la zone doit avoir plus de largeur c'est trop étirée ». **Ne pas étirer horizontalement l'ancien portrait ni confondre ondulation locale et wrap horizontal.** Nouvelle composition entière générée en paysage, nouveau ciel et nouveau sol complet : `source/arene_glace_large_v3/`, `renders/arene_glace_large_v3/`, ZIP et `apercu_arene_glace_large_v3.html`. 768×512 au lieu de512×640 ; normalisation uniforme avec minimes marges, jamais anisotrope. Méthode rendus générés conservée, aucun assemblage de fragments de maps. Versions précédentes préservées.

Ciel opaque indépendant, étoiles extraites sur leur propre overlay statique,7plans terrain, ORA. Bande d'aurore792×240 issue du dessin canonique dans3poses déjà produites, RGB non étirés/recolorés, nouveaux placements et atténuations alpha aux bords. **Mouvement créé, toujours PAS cycle officiel récupéré.** Wrap horizontal30px/s :198pas4px/8ticks,26,4s, phase198=0 ; chaque transition y compris197→0 est exactement la même translation. Raccords spatiaux transparents adoucis, rideaux distincts plutôt qu'un ruban continu redessiné.198PNG RGBA, WebP overlay sans perte, GIF de scène, lecteur autonome avec cases calques et bouton raccord.

13tests dédiésPASS, syntaxe JavaScriptPASS. Terrain immobile, partition/recomposition exacte ; plan de sol généré caché, pas toutes les faces cachées des falaises. Pas de test navigateur interactif ni d'import/runtime/collision/warp PMDO. Dernière composition non encore approuvée par l'utilisateur, autres zones/guilde toujours ouvertes.

## Correction impérative V4 — aurores ANIMÉES, pas seulement scrollées

Utilisateur : « non faut que les boreales soit animée en plusieurs frame stp ANImée ». La V3 était insuffisante : ses198phases déplaçaient une bande immobile. Ne pas appeler cela une animation des rideaux eux-mêmes. V4 : `source/arene_boreales_v4/`, `renders/arene_boreales_v4/`, ZIP, `apercu_boreales_animees_v4.html`.

88poses internes distinctes à100ms, cycle8,8s : plis voyageurs, oscillations locales, hauteur variable, scintillement alpha. Mouvement créé sur dessin canonique, PAS animation officielle extraite. Option wrap indépendante3px/étape, cycle combiné264étapes26,4s. **Lecteur démarre sans défilement**, pour démontrer les formes animées sur place ; cases séparées animation/wrap, frame suivante, vue overlay seul. Calques terrain large768×512/ciel/étoiles V3 byte-identiques ; versions antérieures conservées.88PNG RGBA792×240, WebP transparent intrinsèque, GIF sans scroll et GIF de scène avec wrap, contact sheet poses fixes.

9tests dédiésPASS : poses distinctes, déformation non rigide/animation sans scroll, boucles, raccord, calques invariants, WebP alpha+RGB visibles exacts, GIF animé/terrain fixe. WebP peut changer les RGB invisibles sous alpha0 ; PNG exacts. SyntaxeJS contrôlée ; pas navigateur interactif/runtimePMDO. Candidat visuel non encore approuvé, programme global ouvert.

## Correction V5 — générer les dessins ET palette cycling

Utilisateur : « tu dois générer toi même les frame s'il te plaît en palette cycling aussi ». Pour les aurores V5, ne plus se contenter des déformations calculées du dessin V4. Nouveau passage générateur avec référence canonique : `renders/boreales_frames_generees_v5/bruts/aurores_8_poses.png`. Le générateur a retourné9dessins en3×3, malgré une demande de8en2×4 ; extraction de la grille réelle, brut conservé.9poses détourées/indexées +72étapes (8fondus prémultipliés par paire), boucle7,2s. **9dessins générés, pas72dessins indépendants.** Aucune géométrie d'aurore V1/V3/V4 réutilisée ou déformée. Art généré référencé, pas natif pixel-exact.

Vrai cycling de palette indexée256entrées (16groupes de teintes froides×16luminosités),72tables RGB exportées, indices et alpha séparés. Démonstration palette seule : dessin/alpha fixes, couleurs évoluent. Lecteur `apercu_boreales_generees_palette_v5.html`, mode combiné ou palette seule, wrap indépendant28,8s. Terrain/ciel V3 copiés byte-identiques.9poses,72PNG,2WebP transparents,GIF,ZIP ; sources `source/boreales_frames_generees_v5/`.11tests dédiésPASS, JS syntaxePASS ; pas de validation navigateur/runtimePMDO ni cycle officiel récupéré. Autres zones restent ouvertes.

## Correction V7 — frames subtiles du ciel boréal PMD Sky, sans wrap

Utilisateur : « non faut pas que ce soit du wrap mais que ce soit que des frame animée comme dans pmd sky ca a l'air chaotique » puis « l'image référence c'est le ciel boréal dans pmd sky c'est animée subtilement ». Rejets actés : pas de wrap/défilement (V3/V4), pas de planche de dessins nouveaux mélangés ni cycling de palette global (V5), pas de ruban inventé (essai V6 abandonné, brut non persisté). **Les frames sont l'image de référence `aurorepmdsky.png` elle-même** : 24 frames × 120 ms (2,88 s), variation proportionnelle de luminosité ±7,5 % sur les rideaux via quatre champs gaussiens cosinus à périodes entières, frame 0 = référence exacte, boucle fermée. Pics, nuages d'horizon (fondu 144→157) et étoiles intacts. Overlay transparent 528×314 (alpha extrait, voile ±11 %) posé une seule fois à position fixe (120, 0) dans la scène 768×512, ciel/terrain V3 inchangés, aucun wrap. Rythme et amplitude choisis (cycle officiel inconnu), subtils. Sources `source/boreales_pmdsky_v7/`, rendus `renders/boreales_pmdsky_v7/`, ZIP, aperçu racine `apercu_ciel_boreal_pmdsky_v7.html`. 12 tests dédiés PASS. Note maintenance : la sandbox a été réinitialisée au commit de base pendant la session ; l'historique poussé a été réintégré par ff-only (330 collisions untracked vérifiées identiques, sauvegarde `/home/user/sauvegarde_docs_stash.patch`), `.venv` reconstruite ; les fichiers Métano/ponts non commités de l'utilisateur restent en working tree sans être touchés.

## Correction V8 — aurore ondulante générée + glace latérale (méthode habituelle conservée)

Utilisateur : « Faut de la glace sur les zone grise de la map sur les côté on dirait l'arène est dans le vide / le ciel boréal doit être animée comme des ondulation génère etc et suis la méthode habituel sans la changer ». Rejets actés en plus : V5 rejetée (mélange chaotique de poses déphasées + wrap) ; le « subtil » V7 ne suffisait pas, il fallait des **ondulations générées visibles**. Méthode habituelle inchangée : planches générées fond magenta → extraction alpha → calques séparés → scène 768×512 → viewer/tests/ZIP/push.

Deux planches : `bruts/aurore_ondulations_8_haut.png` (8 poses utilisées ; cases débordantes → extraction colonne unique, fenêtre 305 px centrée sur le centroïde de chaque case, 768×256) et `bruts/glace_laterale.png` (parois gauche/droite + plaine du fond, bande magenta en haut). Aurore : 32 étapes × 125 ms (4 s), fondus prémultipliés entre poses adjacentes, frame 0 = pose 0 pure, boucle fermée, translation horizontale nulle testée. Glace : calque statique derrière le terrain, zones grises comblées. Ciel/terrain V3 byte-identiques, aucun wrap. Sources `source/boreales_ondulation_glace_v8/`, rendus `renders/boreales_ondulation_glace_v8/`, ZIP, aperçu racine `apercu_arene_ondulation_glace_v8.html`. 10 tests dédiés PASS ; GIF en granularité 120 ms (cycle réel 3,84 s) documenté. Dessins/rythme choisis, pas le cycle officiel ; non validé par l'utilisateur.

## V9 — onde boréale : 10 frames sur 10 calques, physique d'onde transversale

Utilisateur : « On va recommencer Génère 10 frame sur leurs propre layer l'animation physique et logique d'onde boréale s'il te plaît ». Nouveau dessin maître généré (fond magenta + blanc, taille réelle 1792×592, jamais supposée). Extraction corrective : fonds clairs retirés par composantes connexes ; le `fill_holes` brut remplissait deux poches blanches sous les franges (77k+68k px) en voile gris — corrigé par exclusion des fonds puis des poches ouvertes (d<60). Onde transversale pure : décalage vertical uniquement par colonne, `12·sin(2π(2x/768−t/10))+5·sin(2π(5x/768−t/10)+0,35)` sous enveloppe 48 px, phases à périodes entières → frame 10 ≡ frame 0 exactement. 10 calques indépendants `couches/OndeBorealeV9_frame_XX.png` (768×256, 160 ms, 1,6 s), contexte V3/V8 byte-identique copié dans `contexte/`, scène sans wrap. Sources `source/onde_boreale_v9/`, rendus/ZIP `renders/onde_boreale_v9*`, aperçu racine `apercu_onde_boreale_v9.html` (ghost de frame). 10 tests dédiés PASS dont physique colonne par colonne. Dessin/cadence choisis, pas le cycle officiel ; non validé par l'utilisateur.

## V10 — effet boréal canonique récupéré, sans ciel, onde en 10 calques

Utilisateur : « tu dois générer les effet onde boréal sans le ciel derrière comme tu avais fais pour les étoiles et l'effet boréal doit s'animer sur son propre layer en plusieurs frame tu dois récupérer la texture de l'onde boréal canonique ». **Plus aucun rideau redessiné** : la texture est récupérée de `aurorepmdsky.png` elle-même. Extraction type étoiles V3 : rubans lumineux par lum+sat (ciel sombre lum~21/sat~63 non retenu), étoiles exclues en deux passes (composantes peu saturées, puis points visibles sat<50 à >10 px d'un ruban sat≥70 — zéro résidu), nuages/pics (y≥144) exclus, fondu bas 134→144, ×2 nearest 528×288, RGB zéro sous alpha 0 (sinon le WebP lossless les réencode et les tests exacts échouent — déjà vu en V4/V7). Onde transversale pure `8·sin(2π(2x/528−t/10))+4·sin(2π(5x/528−t/10)+0,4)`, enveloppe 40 px, 10 calques indépendants, frame 10 ≡ frame 0, 160 ms. Pose unique (120,0) ; ciel+étoiles V3 / glace V8 / terrain V3 byte-identiques dans `contexte/`, aucun wrap. Sources `source/effet_boreale_canonique_v10/`, rendus/ZIP `renders/effet_boreale_canonique_v10*`, aperçu racine `apercu_effet_boreale_canonique_v10.html`. 9 tests dédiés PASS. Texture canonique ; découpe et cadence nos choix, cycle officiel non récupéré ; non validé par l'utilisateur.

## V11 — boréales passées au générateur : suite subtile, calque propre sur notre ciel

Utilisateur : « Passe les dans le générateur pour que les boréal et une suite d'animation subtile sur son propre layer pour le mettre sur notre ciel de notre zone ». Planche générée avec **deux références** : `aurorepmdsky.png` (rubans canoniques) + ciel V3 de la zone (harmonisation navy). 8 poses verrouillées (cœurs/shimmer subtils), extraction **géométrique obligatoire** : la distance de couleur confondait les cœurs magenta avec le fond (franges roses + fissures résiduelles, cœurs affaiblis) → fond par inondation depuis les bords (magenta-like + navy cuit), trous navy internes = voile opaque, fissures magenta internes = transparentes. 16 étapes (8 poses + 8 fondus 50 %) × 120 ms = 1,92 s, boucle exacte, positions verrouillées testées (< 18 px). Calque 768×300 posé une fois sur ciel+étoiles V3, glace V8/terrain V3 byte-identiques, sans wrap. Sources `source/boreales_suite_generee_v11/`, rendus/ZIP `renders/boreales_suite_generee_v11*`, aperçu racine `apercu_boreale_suite_generee_v11.html`. 9 tests dédiés PASS. Suite générée, pas le cycle officiel ; non validé par l'utilisateur.

## V12 — onde boréale palette cycling Halcyon, sans ciel

Utilisateur : « générer les onde boréal sans ciel et que leurs mouvement soit logique les un après les autres en palette cycling dans le style halcyon » (après « Utilise le générateur d'image... arrête de trop penser » : rester direct, générer et montrer). Planche générée 2×4 : silhouette identique, couleurs avancées d'un pas par frame. Extraction inondation magenta (V11), 8 calques 768×256, 120 ms, boucle fermée. WebP/GIF/planche/scènes + viewer `apercu_palette_cycling_v12.html`. 9 tests PASS. Sandbox réinitialisée puis réintégrée (330 collisions identiques, stash docs jeté après vérif, .venv reconstruite).

Correction V12 : la planche générée variant les silhouettes entre cases (IoU 0,51), le palette cycling authentique a été refait depuis la géométrie du ruban de la case 1 : image indexée (rampes cyan 0-3 / magenta 4-7 ordonnées le long du ruban, corps sombre 8 fixe), 8 frames = rotation de palette (+1 cyan, -1 magenta, période 4 | 8). Silhouette identique vérifiée (IoU > 0,999). Assets moteur : onde_indexee.png (P) + onde_alpha.png + palettes_8frames.json. Alignement par roll impossible (formes trop différentes, dx ±8, erreur 9-26 px) : ne pas refaire. Ne pas re-essayer l'extraction multi-cases comme base du cycling.

## V13 — rebase sur layout_guide.png : calques séparés, aurore animée indépendante

Utilisateur : « me rebase sur source/ice_arena_aurora_v1/generation/layout_guide.png, faire les plusieurs layer, aurores animées indépendantes du ciel ». Extraction par inondation depuis le haut (glace = barrière) : ciel navy / étoiles (1-40 px) / aurore (saturés, ≥40 px) / terrain. Aurore : palette cycling des vraies couleurs du guide (famille cyan/magenta × quartile de luminosité), frame 0 = origine exacte, 8 frames même masque, boucle exacte 4|8, 120 ms. Recomposition calques = guide exact testé. Sources `source/arene_guide_couches_v13/`, rendus/ZIP `renders/arene_guide_couches_v13*`, aperçu racine `apercu_arene_guide_couches_v13.html`. 8 tests PASS. Sandbox réinitialisée en cours de session (3e fois) : réintégration ff-only depuis origin, 330 collisions untracked identiques supprimées, stash docs vérifié puis jeté, .venv reconstruite (pillow numpy scipy).

## V14 — calques exacts du guide + aurore 15 frames élégantes

Utilisateur : « Les layer sont pas exactement celui de la référence / Tu dois faire 15 frame de mouvement élégant / Harmonieux changement de couleur des onde boréal dans le même design et texture à la place des boréal statique ». Corrections : (1) calques EXACTS — aurore = rubans lumineux seulement (sat>80 ET lum>55), cristaux sombres d'horizon au terrain ; recomposition 4 calques = guide exact, testée ; (2) 15 frames (120 ms, 1,8 s) : phase 1/15 de cycle par frame, interpolation linéaire circulaire entre les 4 arrêts des rampes cyan (+) et magenta (−), pas adjacent < saut/2 testé, frame 0 = couleurs d'origine, boucle exacte, même masque. Sources `source/arene_guide_couches_v14/`, rendus/ZIP `renders/arene_guide_couches_v14*`, aperçu racine `apercu_arene_guide_couches_v14.html`. 9 tests PASS. Sandbox réinitialisée une 4e fois en début de V14 : réintégration ff-only (330 collisions identiques), stash docs jeté après vérif, .venv reconstruite.

## V15 — zone canonique générée, critères Halcyon/Palika

Utilisateur : « méthode canonique de création de map avec le générateur + animations boréal en plusieurs frames d'ondulation + convertir la zone aux critères de Halcyon Palika ». Terrain généré plein cadre 928×1152 (bande magenta), alpha par inondation (pointes de pics dépassant dans la bande = terrain légitime, zéro magenta résiduel — ne pas exiger top transparent). Planche 2×4 d'ondulations générée → 8 frames AuroreV15_00..07.png strictement 768×256, 150 ms, posées à (80,24) sur grille 8 px. Calques Halcyon empilés : ciel navy uniforme / étoiles V14 / aurore / terrain, sans wrap. Sources `source/arene_halcyon_v15/`, rendus/ZIP `renders/arene_halcyon_v15*`, aperçu racine `apercu_arene_halcyon_v15.html`. 8 tests PASS. NB : np.any(mask!=mask, axis=2) plante sur tableaux 2D — comparer directement.

## V16 — sol continu + boréales référence 10 frames

Utilisateur : « La zone au centre devrait pas avoir de trou régénère + les aurores boréales soit ceux de la référence régénère les même mais avec 10 frame de loop parfaite ». Terrain régénéré sans cratère (bord sombre 5471→226 px, test <600). Planche 2×5 style référence exact → 10 frames AuroreV16_00..09.png 768×256×130 ms, boucle frame10≈frame1 (12,6 %), IoU min 0,355 (seuil 0,30 : phase opposée normale). Extraction : inondation + seuil serré global d<40 pour le magenta cuit enfermé entre deux passages de vague ; fenêtre centroïde + fill_holes IMPOSSIBLE (recrée le voile V9). Halcyon inchangé (grille 8 px, (80,24), nommage uniforme). Sources `source/arene_halcyon_v16/`, rendus/ZIP, aperçu racine `apercu_arene_halcyon_v16.html`. 7 tests PASS.

## Reprise du 20 septembre — Beach DSVFS, séparation fidèle et eau animée

Demande : plusieurs calques de l’image `DSVFS.png` et animation de l’eau Beach PMD Sky. Fichier fourni retrouvé à la racine (pas dans le chemin uploads annoncé). Lot non destructif `source/beach_layers_v1/`, `renders/beach_layers_v1/`, viewer `apercu_beach_calques_v1.html`. Aucun générateur utilisé : préserver exactement cette composition. Neuf partitions visibles 702×466, ORA ; sols/faces cachés non reconstruits. Animation mer + écume, 64 phases de 50ms (3,2s), couleurs source seulement, phase0 exacte, décor sec invariant. Progression des hauteurs de crête extraite des17poses de la planche Beach & Path to Beach (rip redblueyellow) pour guider un mouvement nouveau ; PAS les frames/cadence officielles Sky récupérées. Mer sous écume complétée par pixels bleus voisins, puis remapping entier. Contacts ancrés sur5px et amplitude croissante sur18px pour éviter les traînées de contours aux rochers ; pas d’avance sur le sable. Frames adjacentes parfois identiques : GIF/WebP fusionnent les poses, durée totale contrôlée3200ms.

Copies d’import PNG to Tileset8px : 704×472, ajout transparent droite2/bas6, aucune mise à l’échelle. Remplacer les calques fixes03/04 par les frames de même index, ne pas garder l’ancienne écume par-dessus. Dix tests assetsPASS, interactions viewer en DOM simuléPASS, ZIP CRC/identitéPASS. Chromium téléchargementTLS échoué, pas de navigateur interactif validé ; pas de runtimePMDO. Les anciennes maps et le PNG source restent intacts. Sources et référence de vagues incluses dans le ZIP pour reconstruction ; viewer embarqué autonome.

## Réseau Jardin secret V1 — style Ledian, T reporté (24 septembre 2026)

Demande : layout réseau style Ledian pour `secretgarden.png` (408×408). Lot `source/secretgarden_reseau_v1/`, `renders/secretgarden_reseau_v1/`, galerie racine `apercu_jardin_secret_reseau_v1.html`. **6 pièces 512×512 vides, 46 calques, 16 ports 64px** : couloirs NS/EW, traversante (N/S), latérale (W/S), carrefour + carrefour clairière (4 accès). Générations guidées sur magenta, détourage, partitions exactes testées, raccord d'herbe native `secretgarden.png` (190,240)-(222,272) ×2 opaque 24px. **Jonction en T reportée** : limite 10 générations atteinte (6 + 3 reprises + 1 T) ; le plein-cadre croix vérifié 4 ouvertures est devenu le carrefour, la variante en retrait (~21px, pontée par la bande et testée) est la 6e pièce. Ne pas présenter les générations comme des cartes natives ; statiques, PMDO NOT TESTED.

## Réseau Jardin secret V2 — T corrigé, bordures feuillues, couches matière, fleurs Sky Peak (24 septembre 2026)

Suite demandée : corriger le T, bordures feuillues immersives au lieu des découpes vertes nues, chaque zone en couches sol/végétation/arbres au choix, fleurs animées comme Sky Peak. Build `source/secretgarden_reseau_v1/build_v2.py`, galerie `apercu_jardin_secret_reseau_v1.html` (V2, animation pause/pas-à-pas).
**7 pièces 512×512, 82 calques, 19 ports 64px** : ajout jonction en T vérifiée (N/E/W herbe, sud mur d'arbres). 10 couches par zone (sol, fond, cimes, buissons, premier plan, troncs, rochers, fleurs, bordure, accès) + 4 phases fleurs 200ms et GIF par pièce + ORA. Bordure : cadre généré, non-carrés rembourrés magenta (jamais anisotrope), fenêtres 104×88 dégagées par script aux accès. NS = tunnel de feuillage assumé (bordure couvrante, désactivable). Coins T hors terrain/bordure = vide transparent standard. Générations et partition seuils documentés ; vérification PASS ; PMDO NOT TESTED.

## Réseau Jardin secret V3 — multicalque sol/chemin/arbres/rochers/bordure jungle (24 septembre 2026)

Demande : par zone, multicalque sol / végétation bordure feuillue style jungle PMD / roche / arbre / chemin. Build `source/secretgarden_reseau_v1/build_v3.py` (remplace les couches V2, bruts/anciens dans git). **7 pièces, 68 calques, 19 ports** : 01_sol (rives du polygone), 02_chemin (bande centrale géométrique érosion 15px), 03_arbres (cimes claires + troncs toutes profondeurs), 04_buissons (verts sombres), 05_rochers, 06_fleurs (4×200ms + GIF), 07_bordure_jungle (7 nouvelles générations style Southern Jungle, réf SHA dans manifeste, rembourrage magenta si non-carré, fenêtres 104×88 aux accès), 08_acces. V2 (fond/cimes/plan/troncs séparés, bordures jardin) archivée en git. Vérification PASS ; PMDO NOT TESTED.

## Réseau Jardin secret V4 — layouts séparés sol/chemin/fleurs/rochers, 2/7 zones (24 septembre 2026)

Demande : sol, chemin, fleurs, rochers en layouts générés séparés. `source/secretgarden_reseau_v1/build_v4.py`, `renders/.../layouts/<zone>/`. Ce tour : couloir_ns + salle_carrefour (8 générations + 2 reprises : chemin carrefour dirt→herbe, fleurs guirlandes→bouquets). Assemblage contraint (chemin⊆sol, végétation hors sol, rochers/fleurs sur sol|végétation), bordure+accès V3 inchangés, fleurs ré-animées. Manifeste v4 avec source par pièce ; 5 zones encore en V3 (ew, t, traversee, laterale, clairiere = 20 générations restantes). Vérification PASS. Sandbox réinitialisée une 5e fois : réintégration via fetch+reset sur origin (ce22a6eb), .venv reconstruite, sans perte.

## Réseau Jardin secret V5 — nues, tilesheets rochers/végétation animée (24 septembre 2026)

Demande : preview HTML + version sans verdure/rochers par zone + tilesheets rochers et végétation avec frames. `source/secretgarden_reseau_v1/build_v5.py` (zéro génération, pixels existants). Par zone : composition nue PNG+GIF (sol+chemin+fleurs+accès), GIF full (fleurs+végétation 4×200ms), tilesheet rochers + manifeste (88 sprites réseau, masquage par composante), phases végétation + spritesheet buissons ×4 frames (127 sprites, nappes connectées exclues du découpage). Galerie V5 : toggle végétation animée (remplace 03+04), bouton vue nue, liens d'exports. Empilement unifié partout. Vérification PASS. Sandbox réinitialisée 6e fois : réintégration habituelle, sans perte.
