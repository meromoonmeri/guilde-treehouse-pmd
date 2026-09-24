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

## Cap canonique face mer v1 — nouvelle map 100% strict (septembre 2026)
Reprise projet en mode spriter pro : l'utilisateur demande des maps avec les
textures canoniques. Livraison `renders/falaise_mer_canonique_v1/` :
1024×512 (128×64, 8px), paroi Metano plein cadre en dalles 64×48 completes,
bouche d'eau dans couronne/pied, canal + cascade 64px en eau native 4 phases
(FrameLength=10). 6 calques PNG + ORA + WebP + galerie
`apercu_falaise_mer_canonique_v1.html` + ZIP. Scripts
`source/falaise_mer_canonique_v1/{build,verify,gallery,package}.py`, PASS
(0 difference, 1760 cellules eau comparees). Aucun pixel genere.
Lecons : rangees cascade 15-16 transparentes en source (chute mappee sur
0..14) ; retours arrondis en bord de cadre rendus comme des arches
abandonnes au profit de faces plein cadre ; bouche obligatoire sous peine de
barre verte (notch) ou brune (pied) sur l'eau. Repetition des faces assumee,
a varier en V2 apres validation en jeu. Nuit Abyss non incluse.

## Sommet Sky Peak de nuit — vista 960x600 (septembre 2026)
Demande : layout Sky Peak via generateur, textures canoniques, vue depuis le
sommet, fleurs sur calque propre (traitement canonique), foret + montagnes,
nuit, etoiles scintillantes, nuages wrap seamless, calques separes PMDO.
Correction utilisateur : prairie en textures CANONIQUES, ZERO entite.
Livraison `renders/sommet_sky_nuit_v1/` : prairie/reliefs natifs du GIF Sky
(bande y328..504, miroir 504->960 coutures x228/732, fleurs retirees puis
reanimees), nuit Abyss (pipeline canonique v1), 10 sprites floraux natifs
(4 phases @200ms, 34 sites, 2 groupes, variantes native+nuit), etoiles ref_v2
64 phases reutilisees a l'octet, ciel degrade echantillonne, panorama et
nuages generes SANS entites (brut entites jete et regenere), split
montagnes/foret par treeline, 2 wraps a marges >=32px + brume miroir.
Galerie `apercu_sommet_sky_nuit_v1.html` (tout anime live), ORA 13 calques,
WebP 8f, ZIP. Verify PASS. Brut `sommet.png` genere non utilise (remplace
par prairie native). Prochaine etape possible : variantes aube/jour.

## Texture prairie Sky 512 + audit de mes generations (septembre 2026)
Demande : auditer mes propres bruts, livrer une surface texture prairie.
`renders/texture_prairie_sky_v1/` : surface 512 jour/nuit quiltee 100% tuiles
GIF natives (442 motifs, 4096 cellules, 0 difference), 8 touffes natives,
0 galet (aucun isole dans le GIF). `AUDIT_MES_GENERATIONS.md` : pano v1
rejete (entites), sommet genere non utilise (remplace natif), guide_prairie
REFUSE en texture (vert lime (128,229,38) vs (135,247,119), rochers gris vs
bleu-ardoise, plaques marron intruses, traits trop gros). Verify PASS.

## Paroi + prairie Sky layer unique 1008x176 (septembre 2026)
Demande : paroi rocheuse + prairie en layer unique, texture canonique.
`renders/paroi_prairie_sky_v1/` : bande GIF y328..504 carrelee [F][M(F)],
fleurs retirees (infill 4 frames), joint unique x504 continu, jour + nuit
Abyss. Premier essai [A][M(A)][B][M(B)] rejete : joint central non continu
(blocs differents). Verify PASS 0 difference.
