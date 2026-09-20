# Reprise des maps — 20 septembre 2026

## Demande actuelle

### Rappel prioritaire — magenta et kiosques sans PNJ intégré

Utilisateur : push + toutes les zones générées sur fond magenta, kiosques vides permettant le placement ultérieur de Pokémon dans l’éditeur. Consigne inscrite dansAGENTS. Ajout Casino : exports terrain/réseau surmagenta pur ; deux plansarrière/avant par type de kiosque, troisrepèresPNJ avecpointclient (`editeur/placements_pnj.json`), sans aucuneentitéPokemon ajoutée. Recomposition des sprites existants exacte. Le kit remplace les sprites fusionnés lors de l’intégration, ne pas les empiler ; pas d’intégration PMDO revendiquée. `editor_setup.py` appelé parbuild, kitinclusdansZIP, exportPNGoption`--magenta`.


### Livraison actuelle — Casino Network V1

L’utilisateur autorise désormais de **générer directement un réseau casino indépendant** de l’imagejointe, réaménagé surlesmatièresLedian. Ancienblocageuploadlevépourcechantier. Il demande aussi décorassorti, torches/fourneaux et vraiesframesde flammeHalcyon.

- `source/casino_network_v1/`, `renders/casino_network_v1/`, `apercu_casino_reseau_v1.html`.
- Terrain1024² crééenunecompositioncontinue ;4secteurs512² (scène,salon,accueil,jeux),4liaisons etentréeS. Ne revendique pas permutationarbitrairementseamless des secteurs.
- 38instancesdecalques ; tapisnatifscontinus, estrade/rideaux/kiosques/tables générés séparément, KrowBanknatif,8braseros,2corpsfourneau générés. Mobilierdéplaçabledansviewer ; terrainviderecomposableexactement.
- 4poses deLedian_Dojo_Animated.tile reconstruites depuisGroundlayer1, rectanglecellules14,11–18,19,FrameLength6ticks. Brasero32×64 = flamme32×40+supportconstant. Pixels/cadencevérifiés ;100ms/poseà60Hz,400msloop. Aucun cycle de feu inventé.
- 13testsassetsPASS ; DOMsimuléviewer/ZIP PASS ;154PNGexportés depuiskit etcomparésauxpixelsattendus. Pas denavigateurgraphique niPMDOvalidé. Footprintsrectangulairesindicatifs, cheminprincipaltapisdégagement8pxpassant ; pascollisions/hauteursmoteur.
- SeptbrutsarchivésWebPlossless ; premierterrainpanoramique écarté, correction1024²retenue ; fourneaugénérécomportait3corps, seulmilieucompletutilisé.
- Pourbudget : copieembarquée7Mo deBeachV1`renders/beach_layers_v1/index.html` remplacéeparredirectionversviewerracineoriginalinchangé. ImagesetZIPanciensinchangés,testDOMV1PASS. Cloneinitialementreset3d4ea6f0,puisrestauréparffdepuisbranchepoussée ; stashancienétatconservé,nepaspopautomatiquement.


### Dernière évolution — casino Ledian, étude des objets Métano

L’utilisateur demande désormais **un réseaucasino avec tapisrouges, estrades, rideaux et structures/kiosques PMD sur leurs propres calques**, plus une baseLedianvide. Il a montré la première salle choisie. L’interdictiondedéco précédente est remplacée pour les overlays, pas pour la base.

Étude réalisée : KrowBank=Murkrow confirmé dans les scripts Halcyon ; toitureObjects, guichet/coffresObjects_Over. Extraits104×96 sans resampling dans `source/ledian_casino_v1/references/`, identitéGit des troisbanques vérifiée au commitda6c2130. VoirREADME et `inspect_krow_bank.py`. Réseauproposé4salles : accueil/change, jeux, scène, salon — **pas encore produit**.

La piècejointe est visible danschat mais le chemin annoncé`/home/user/uploads/image-1.png` est absent duworkspace desoutils. Impossible de corrigerfidèlement l’imagechoisie sansrécupérationfichier. Ne pasprétendre avoir livré les maps/tapis/estrades/rideaux. Dernier travailpoussé : étude et références, non réseaufinal.


Dernières demandes : **régénérer le ciel de référence adapté à la plage, sans lune, nuages plus petits en wrap overlay et boucle parfaite**, puis **plusieurs carrefours/maps agglomératives comme Ledian souterrain**. Le lot Beach Network V1 est réalisé séparément, sans écraser la plage et les anciens lots.

### Livraison actuelle — extension sud V2

Nouvelle demande « Continue … plusieurs carrefour et map aglomérative … comme Ledian ». Ajout de quatre maps indépendantes, sans remplacer les six premières : 07 T(NES),08 T(WES),09 croix(NESW),10 baie(NW), en(1,2),(2,2),(1,3),(2,3). Liaison nouvelle05S↔07N ; dixcartes, douzeliens,27ports, sorties08E/09W/09S réservées. Ciel sans lune, nuages64s et terrainV1 conservés.

- Sources `source/beach_extension_v2/`, sorties `renders/beach_extension_v2/`, viewer `apercu_extension_plage_v2.html`. Aperçu serveur : `python source/beach_extension_v2/serve.py --port 8002`, lié à0.0.0.0 ; servir les deux lots sous le même origin, pas seulement le sous-dossierV2.
- Cinq générations archivées WebP lossless, égalitéRGBA testée avec les PNG initiaux. Première07avait de l’eau sur son accèsE ; **07corrigée retenue**, E désormais sable. Bruts/provenance conservés, pas de nouvelle génération du ciel.
- 80calquesPNG512² jour/nuit,16atlas contenant512frames (32×100ms eau/écume), liserécontact≤3px. ExportPNGportable testé :8compositions+512frames exactes. Compositions du dépôtWebPlossless ; aperçu réseau explicitement à50%, exports natifs inchangés.
- 13tests assetsPASS ; viewers combiné et ZIP en DOMsimuléPASS ; archive autonome104fichiers/3 217 901octets, SHA256 `11a416c9e0fe79a31d9d68e0ee3f45dd2d02ce0680602cf0f86a25ebc5ad7131`. HTTP200pour263URLs, redirection racineversV2fonctionnelle. Pas navigateur graphique ni runtimePMDO.
- Déduplication sans altérer les livrablesV1 :768framesPNG+12ORA+12compositionsV1 ignorées parGit mais **byte-identiques dans le ZIPV1 existant**. `restore_exports.py` restaure792fichiers au besoin ; appelé par build/verifyV2, verify/packageV1. Test de restauration isoléePASS. Les fichiers restent présents dans le workspace courant.
- Budget cumulatif≈125Mo après déduplication, proche du plafond : remesurer avant toute grosse copie. ZIPV2 n’embarque ni V1ni bruts ; viewerportable limitéaux4nouvellescartes, lien07N→05 explicite/externe. Le viewer du dépôt montre les10.

### Étape précédente — Beach Network V1

- Viewer `apercu_reseau_plage_v1.html`, assets/pack `renders/beach_network_v1/`, scripts `source/beach_network_v1/`.
- Six modules 512² en réseau3×2 ; carrefours T/croix, 15ports96px, septliens et extension05S. Connexité et bandes96×16 identiques contrôlées jour/nuit.
- Neuf bruts conservés, dont03corrigée. Ciel généré sans lune ; nuages512×112, trois groupes≤96×28, déplacement1px/125ms, wrap64s. Pas d’ancien ciel lunaire recollé.
- Eau/écume32×100ms par nouveau module ; liseré côtier nouveau≤3px, y compris aux rochers. Le terrain de la plage de référence reste V1, avec64×50ms et ce nouveau liseré ; **anciennes V2/V3 absentes, non restaurées**.
- 13tests pixels/codec/topologie PASS, interactions DOM simulé PASS, pack971fichiers/28 652 023octets, SHA256 `911bb5f07ace894556b3ad5330e269f9f016830486cce382f2c078d46c045f5d`. Aucun navigateur graphique ni PMDO validé.
- Revue visuelle effectuée : ensemble jour, plage/ciel nuit, strip de nuages, module06 à la crête de l’écume. Qualité artistique à faire approuver ; quelques aplats bruns en03, contours rocheux aux jonctions non certifiés seamless. Calques = surfaces visibles, pas objets natifs complets ni collisions.
- Budget cumulatif : environ125,6Mo/1292fichiers modifiés ou nouveaux à ce stade, **proche du plafond128Mo**. Ne pas ajouter de grosses duplications ni une nouvelle archive des bruts sans remesurer.

Le repérage ci-dessous décrit la reprise initiale, avant cette livraison.

## Repérage effectué

- 141 fichiers README recensés ; parcours de leurs présentations et statuts, lecture approfondie des méthodes et lots pertinents pour les maps.
- Instructions dans `AGENTS.md`, historique de `README.md`, manuel `MANUEL_METHODE_PMDO.md`, audit `audits/metano_import/RAPPORT.md` et méthode `source/layouts_magenta_v1/WORKFLOW.md` consultés.
- 353 scripts Python recensés et analysés syntaxiquement : aucune erreur de syntaxe. Ce n’est pas une exécution de tous les scripts.
- 74 fichiers `.tile` présents sous `source/` ; ce nombre inclut des références de différents lots, pas nécessairement 74 textures distinctes.
- Inspection visuelle du témoin canonique Métano, de la forêt sud–nord V3 et de la composition d’arène V16.

## Contrat à préserver

Deux méthodes historiques coexistent :

1. **Rendu généré référencé PMD** : composition complète avec références canoniques, terrain sur magenta, détourage, plans de profondeur, fonds et effets séparés. La correction explicite de l’arène rejette une mosaïque de bouts de maps. Ne pas revenir silencieusement à cette méthode rejetée.
2. **Pixels natifs exacts** : prélèvements documentés, modules complets cohérents, pas de rotation/miroir/redimensionnement/recoloration des textures de jour. C’est notamment la route d’import native Métano. Un dessin généré même remis dans la palette source n’est pas une extraction canonique.

La demande actuelle insiste sur les textures canoniques : annoncer clairement l’origine de chaque matériau et ne pas certifier une génération comme pixel-exacte. Choisir la méthode en fonction de la map demandée, sans réimposer les contraintes spécifiques de Métano à tous les biomes.

Dans les deux cas : conserver la DA, l’échelle, les raccords, les volumes et les accès lisibles ; éviter les falaises fragmentées en cellules indépendantes. Préserver les compositions approuvées. Pour les entrées concernées par la correction historique : arrivée sud, progression vers l’entrée au nord.

## Points d’entrée utiles

| Besoin | Sources / outils |
|---|---|
| Composition générée, magenta, calques | `source/layouts_magenta_v1/WORKFLOW.md`, `palette.py`, `build.py` |
| Modules natifs Métano | `source/cote_v4_abyss/natifs/`, `prepare.py`, `sample.py` |
| Nuit Abyss exacte | `source/cote_v4_abyss/night.py` ; ne pas cumuler les filtres |
| Eau native Métano | `source/eau_metano/natifs/`, `source/build_water_metano.py`, `source/verify_water_metano.py` |
| Entrées sud–nord, provenance par pixel | `source/zones_south_north_v3/`, `exports/zones_south_north_v3/manifest.json` |
| Sky Peak, terrain original | `renders/sky_peak_canonique_v1/README.md`, `source/sky_peak_v1/build_canonique.py` |
| Donjons/autotiles natifs | `renders/donjons_dtef_v2/README.md`, `source/donjons_dtef_v2/` |
| Dernière arène générée | `source/arene_halcyon_v16/`, `renders/arene_halcyon_v16/` |
| Export Ground, ressources, index | `source/pmdo_cote/`, `source/cote_v5_expeditions/`, manuel PMDO |
| Procédure de restauration du runtime | `source/pmdo_runtime/README.md` |

Attention : certains anciens builders écrivent leurs exports dès l’import Python. Lire le code avant de les importer ou de les relancer.

## Livraison et contrôle attendus

- PNG transparents alignés, noms uniques, manifeste des positions et ordre des couches ; ORA éditable lorsque le pipeline le prévoit.
- Sol, chemin, parois/relief, entrée, végétation, premier plan, ciel et effets séparés selon les besoins. Des plans visibles découpés ne constituent pas automatiquement des objets complets avec faces cachées.
- Animations sur leurs propres calques : taille constante, cadence documentée, vérification de toutes les transitions, y compris dernière → première. Ne pas appeler une animation créée un cycle officiel récupéré.
- Prévisualisation à 1× et zoom entier, contrôle de recomposition et de provenance ; test moteur séparé.
- **Ground/PNG to Tileset : généralement 8 px pour nos packs. DTEF : sources à 24 px, feuilles 432×192, 47 configurations utiles par bloc. Ne pas confondre les routes d’import.**
- Collisions, occlusion, warps et gameplay ne sont jamais déduits des seuls contrôles d’images.

## État technique vérifié dans cette session

Environnement `.venv` recréé avec Pillow, NumPy et SciPy ; ignoré par Git. OpenCV et Playwright non installés lors de ce repérage. Node et GitHub CLI disponibles ; Aseprite/Tiled/PMDC non trouvés dans PATH. Le cache runtime décrit par les anciens README est absent ici.

Commande réellement exécutée :

```sh
.venv/bin/python -m unittest source.arene_halcyon_v16.test_build source.zones_south_north_v3.test_build -v
```

**19 tests : 18 réussis, 1 en erreur.** L’erreur est `test_original_sources_unchanged`, qui appelle `git show 438b9288:...` : cet objet historique est absent du checkout. Vérification séparée des SHA-256 des cinq sources contre le manifeste : **5/5 conformes**. Cela ne remplace pas la comparaison historique manquante. Aucun test n’a été affaibli ou modifié.

Réserves relevées dans V16 :

- La dénomination « boucle parfaite » repose sur un seuil de différence des masques, pas sur une preuve de continuité du mouvement. Une revue animée reste nécessaire.
- Des commentaires/champs générés du builder parlent encore de 8 frames/planche 2×4, alors que le code et les exports testés en utilisent 10/2×5. À corriger dans une intervention dédiée, sans reconstruire aveuglément les anciens exports.
- L’alignement sur 8 px et le nommage Halcyon ne prouvent pas un import moteur.

Les succès de chargement PMDO cités dans les anciens rapports restent historiques ; aucun lancement PMDO, rendu GPU ou test de gameplay n’a été effectué dans cette reprise.
