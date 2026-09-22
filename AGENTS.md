# Méthode de production approuvée — zones Métano

## IA3 — arène de glace, layout généré : bordure immersive, chemin sud, aurore générée design canonique 20 frames à la taille du ciel, montagnes lointaines (22 septembre 2026)

[Arène PNG](renders/arene_glace_boreale_v3/IA3_arene.png) · [Animée WebP](renders/arene_glace_boreale_v3/IA3_arene_animee.webp) · [Planche des 7 calques](renders/arene_glace_boreale_v3/IA3_calques.png) · [20 frames d'aurore](renders/arene_glace_boreale_v3/IA3_aurore_20_frames.png) · packs `IA3_arene_glace_boreale_calques.zip` / `IA3_arene_glace_boreale_PMDO.zip`. Glace/montagnes/sol générés d'après la référence et quantifiés ; aurore = 20 frames générées au design canonique (17 cellules continues + retour 3), étoiles natives 1×. Détails et limites : `source/arene_glace_boreale_v3/README.md`. IA2 (glace native) reste disponible.

## IA2 — arène de glace canonique + aurore boréale canonique verticale (22 septembre 2026)

[Arène PNG](renders/arene_glace_boreale_v1/IA2_arene.png) · [Animée WebP](renders/arene_glace_boreale_v1/IA2_arene_animee.webp) · [Planche des calques](renders/arene_glace_boreale_v1/IA2_calques.png) · [12 frames d'aurore](renders/arene_glace_boreale_v1/IA2_aurore_12_frames.png) · packs `IA2_arene_glace_boreale_calques.zip` et Ground `IA2_arene_glace_boreale_PMDO.zip`. Glace `pmdskyicearena.png` 1× (arrière / sol continu / avant), rubans d'`aurorepmdsky.png` 1× en onde verticale 12×6 ticks boucle exacte sur calque propre, étoiles natives, ciel reconstitué. Cadence/onde = nos choix, cycle officiel non retrouvé. Détails : `source/arene_glace_boreale_v1/README.md`.

## FD1 — forêt secrète, Mont Discipline, plaines brûlées : 22/22 cartes (22 septembre 2026)

[Forêt secrète duo](renders/final_duos_v1/FD1_secrete_duo.png) · [Mont Discipline duo](renders/final_duos_v1/FD1_discipline_duo.png) · [Plaines brûlées duo](renders/final_duos_v1/FD1_brulees_duo.png) · [Feux natifs animés](renders/final_duos_v1/FD1_brulees_duo_anime.webp) · packs calques `FD1_<lieu>_duo_calques.zip` et Ground PMDO `FD1_<lieu>_PMDO.zip` dans `renders/final_duos_v1/`. Méthode, provenance par matériau et limites : `source/final_duos_v1/README.md`. Six cartes, 4–6 groupes, sol continu, natifs 1× (souche, ciel/collines, feux BPA 10×3, flammèches 9×4), plans générés quantifiés dans la palette du lieu. Tests images + sérialisation Ground + installeur ; PMDO non exécuté, pas d'approbation artistique.

IB1 : Searing Crucible glacial livré, source Halcyon working-copy1522c7a8. Géométrie504×504/72cases conservée ; pics14/20cases,4tracés,2tours actifs/1pause. Viewport320×240, pas de resize. Source/pack : `source/ice_boss_v1/restore.py`. Boss Halcyon opt-in, Tile à enregistrer ; Lua simulé testé, PMDO non exécuté. Préserver les16cartes/variantes des plaines déjà converties par viewport_pmdo_v1.

WP1 livré : plaines,5calques,18phases natives ;16cartes publiées. MD1 montré mais non poussé, absent du checkout restauré : à récupérer. Suite : forêt secrète, plaines brûlées. Lanceur source/plaines_pmd_v1/restore.py.

## Mise à jour — finale LF1 et mobilier FC1

LE1 approuvée, LF1/FC1 livrés : [bilan et limites](source/suite_foret_cafe_v1/README.md). Préserver entrée, natifs et salles. Mobilier13/36,23+fenêtres à poursuivre ; tailles visées au générateur puis normalisation des créations seulement. Tests≠validationPMDO/artistique.


## Entrée en lisière — six groupes et lumière PMD (21 septembre 2026)

**[PNG de la carte](renders/lisiere_pmd_v1/LE1_lisiere.png)** · **[WebP animé direct](https://raw.githubusercontent.com/meromoonmeri/guilde-treehouse-pmd/7253a42e93d8cc24358e4477e6e9c2056d118845/renders/lisiere_pmd_v1/LE1_lisiere_animee.webp)** · **[Pack PNG multicalque](https://raw.githubusercontent.com/meromoonmeri/guilde-treehouse-pmd/7253a42e93d8cc24358e4477e6e9c2056d118845/renders/lisiere_pmd_v1/LE1_lisiere_calques_et_effets.zip)** · [Cascades de lave animées](renders/lisiere_pmd_v1/LE1_cascades_animees.webp).

Dernière demande ciblée exécutée : **une entrée dans une lisière**, identité Forêt envahie H07P03, disposition d’obstacles inspirée de Mystifying Forest lorsque cohérente. Cinq véritables plans générés séparément : fond forestier / sol continu / rochers / arbres-racines / végétation basse. Sixième groupe : lumière PMD, rayons et particules sur deux pistes natives indépendantes. Aucun fond/sol cuit dans le calque d’arbres retenu ; la première tentative incorrecte est archivée, pas utilisée. Le sol est rempli sous le décor. Passage central sud→nord64px libre, dégagement conservateur8px vérifié, pas une validation de collisions/warps moteur.

Rayons H07P04W32×8ticks, particules14×7ticks, toutes448combinaisons recomposées exactement. Lumière native réemployée explicitement : ne pas prétendre qu’H07P03 possédait cette animation à l’origine. Six modules de cascades/colonnes H26P01,8×3ticks, pieds/halos conservés à1× ; livrés à part, pas placés en forêt. WebP forêt = extrait4,27s, lecture unique, pas boucle composite intégrale209s ; WebP cascades = boucle complète400ms. PNG d’import sans perte, WebP de présentation compressés. Six groupes sémantiques, pas six fichiers arbitraires.

Une seule entrée livrée ici : la finale et les autres cartes restent à produire/reprendre. Ni validation PMDO ni accord artistique prétendu. Huit bruts archivés losslessly au commit100e6878. Gros ZIP et grand WebP conservés dans Git au commit7253a42e avec liens directs ci-dessus, SHA/index `source/lisiere_pmd_v1/release.json`, lecteur/restaurateur et serveur8012 ; ils ne sont pas supprimés. Native_sources.zip V1 dédupliqué avec son membre byte-identique déjà inclus dans l’ancien pack, lecteurs adaptés/testés. Anciens rendus/ZIP et Beach inchangés. Scripts `source/lisiere_pmd_v1/`, détails et limites dans `renders/lisiere_pmd_v1/README.md`.

## Précision en cours — une autre zone du même lieu, 4–6 calques

Dernière consigne : les cartes doivent sembler appartenir **au même lieu que leur référence**, pas seulement au même biome. Garder textures, gamme de couleurs, formes caractéristiques et perspective ; ciel/arrière-plan seulement lorsqu’il existe dans la référence. Viser4–6groupes sémantiques (sol continu, reliefs/rochers, végétation/bordures, accès/architecture, fond/ciel éventuel, fluides/effets), avec vraies pistes d’animation séparées. Ne pas atteindre le quota par un simple découpage de surfaces visibles. Revoir les occlusions et la continuité du sol, pas seulement les noms de calques.

**[Cadrage et revue des références](source/dungeon_biomes_v2/CONTINUITE.md).** Mont Discipline doit garder ses dalles claires et son cadre végétal, pas devenir une montagne brune ; forêt secrète : bleus/cyan et toiles ; plaines : horizon et ciel de la référence. Conserver aussi les vrais calques de cascades/colonnes de lave et les lumières/particules de forêt, avec leurs cadences natives. Les références de chaque lieu priment sur son nom.

État après interruption :10compositions d’étude, **aucun lot2 livré/validé**, finales forêt secrète et plaines brûlées non générées (limite10atteinte). Les études montagne brune et entrée brûlée noire quadrillée sont écartées ; les autres à requalifier, pas approuvées. Bruts préservés losslessly au commitf1bde98c, index `source/dungeon_biomes_v2/drafts/archive.json`, lecteur `draft_archive.py`. Les versions déjà livrées et Beach restent intactes. La satisfaction générale exprimée par l’utilisateur ne valide pas ces nouvelles études. Reprendre avec ce cadrage avant de compléter les images manquantes ; portée22cartes par lots, aperçusPNG/WebP et push toujours requis.

## Donjons réinventés — lot 1 / cinq duos (21 septembre 2026)

**[Planche PNG des dix cartes](renders/dungeon_biomes_v1/apercus/DB1_collection.png)** · **[Pack multicalque](renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip)** · [Méthode et limites](renders/dungeon_biomes_v1/README.md).

WebP animés directs : [forêt](renders/dungeon_biomes_v1/apercus/DB1_foret_duo.webp), [île](renders/dungeon_biomes_v1/apercus/DB1_ile_duo.webp), [volcan](renders/dungeon_biomes_v1/apercus/DB1_volcan_duo.webp), [désert](renders/dungeon_biomes_v1/apercus/DB1_desert_duo.webp), [courant marin](renders/dungeon_biomes_v1/apercus/DB1_marin_duo.webp). Deux cartes par fichier, extraits2,13s échantillonnés, lecture unique, pas de fausse boucle composite courte. Aperçus compressés ; PNG d’import sans perte.

Périmètre confirmé : **11 duos entrée+fin =22cartes**, livrés par lots. Premier lot livré :10compositions complètes réellement générées,42calques PNG de surfaces visibles,616états d’animation/référence indépendants, canevas Ground8px/basenames uniques, aucun Pokémon. **Les surfaces cachées derrière arbres/parois ne sont pas reconstruites** : ces calques ne sont pas des objets mobiles complets. `assemble.py` dans le ZIP recompose les10PNG transparents et leurs démonstrations à un tick choisi, sans dupliquer les fichiers lourds.

Audit des11références dans `source/dungeon_biomes_v1/audit.json`. Port épinglé cd07abc4, pret89c65d9c :207blobs H identiques. **Tout n’est pas BPA** : forêt H07P04W BPA+BPL ; île ciel H29P04 BPL ; volcan H26P01 BPL + particules W04 BPA ; désert W05 BPL+scroll et cycles terrain d’origine conservés en référence ; courant H02P02W BPL. Natifs1× distincts des créations. La lave est un nouvel arrangement de textures sources sans interpolation/recoloration/flip, avec provenance de chaque pixel. Cadences indépendantes conservées ; banque forêt448combinaisons BPA/BPL, pas448frames à lire dans l’ordre. Sources et preuves incluses ; aucune validation PMDO/GBA/PC-port exécuté ni approbation artistique revendiquée.

Reste à produire : jungle, forêt envahie, mont de discipline, plaines sauvages, forêt secrète, plaines brûlées — six duos. Ce lot ne termine pas le mobilier/fenêtres V8. Beach, anciennes maps et anciens ZIP inchangés. Dix nouveaux bruts archivés losslessly au commit93ec3994 ; cinq anciens bruts Casino/étude Arcanin supplémentaires conservés à l’identique dans Git via le lecteur d’archive existant pour respecter le budget. Tests de provenance/recomposition, assembleur autonome et Casino passés. Serveur8011 : PNG direct, aucun HTML nécessaire ; serveur Spinda8010 conservé et rechargé pour les anciennes URL d’archives.

## Banderoles, tapis rouges et estrade Spinda / Mime Jr — 21 septembre 2026

**[PNG de la collection](renders/spinda_decor_v1/apercus/SpindaDecor_collection.png)** · [Mise en scène PNG](renders/spinda_decor_v1/apercus/SpindaDecor_cafe_demonstration.png) · [Pack de calques](renders/spinda_decor_v1/Spinda_banderoles_tapis_estrade.zip).

Demande : push GitHub, banderoles canoniques réadaptées au layout sur leur calque, tapis rouges Spinda, estrade avec deux rideaux Spinda/Mime Jr. Livré :5calques muraux jour/nuit conformés aux pans, sans couvrir fenêtres/accès ;3tapis rouges indépendants ;estrade,rideau gauche,rideau droit en3calques alignés208×184. Canevas Ground8px, variantes nuit, référence SpindaCafe2 native inchangée. Les adaptations sont générées/non natives, pas des pixels canoniques prétendus inchangés.10sorties préservées dans Git,2frontales rejetées ;front redressé depuis la diagonale retenue. Fragment de salle intempestif retiré de l’image du rideau droit. Exports statiques PNG/WebP directement visibles, sans HTML ; placement de la scène/tapis uniquement pour démonstration. Autres meubles/fenêtres V8 encore en attente.

Scripts `source/spinda_decor_v1/`, serveur8010 (racine = PNG direct), vérifications de pixels, calques, fenêtres/accès, ZIP et provenance. Pas de validation PMDO/approbation artistique. Trois anciens bruts Casino (estrade,rideaux,terrain initial supplanté) archivés à l’identique dans Git via `source/casino_network_v1/archive.json`, lecteurs/tests/serveurs adaptés ; leurs anciennes livraisons et Beach restent inchangés. Au démarrage de ce tour, le checkout restauré était revenu au commit de base : la même branche a été mise à jour en fast-forward depuis le push d73e6ac2 ; les anciens fichiers Beach locaux ont été conservés dans un stash, pas écrasés ni réappliqués sur les versions plus récentes.

## Torches murales animées — huit orientations (21 septembre 2026)

**Affichage direct demandé : le HTML ne s’affiche pas chez l’utilisateur.** Livrer prioritairement le [WebP animé des8vues](renders/spinda_torches_v1/apercus_directs/Torches_8_angles_animees.webp) et le [PNG](renders/spinda_torches_v1/apercus_directs/Torches_8_angles.png),832×448,16frames100ms en boucle. Ces aperçus ne nécessitent aucun HTML. Fond et8bandes lumière précédents conservés à l’identique dans le ZIP ; serveur8009 maintient leurs URL.

**[Atelier torches](apercu_spinda_torches.html)** · [Pack PNG autonome](renders/spinda_torches_v1/Spinda_torches_8angles_animees.zip) · [Planche des huit vues](renders/spinda_torches_v1/Torches_8_orientations.jpg).

Dernière demande : torches murales sous tous les angles, lumière animée par palette cycling multiframe, calques séparés. Livraison additive :8supports générés (N/NE/E/SE/S/SO/O/NO),4vraies poses natives Halcyon/Ledian inchangées à1×,16frames de lumière par orientation (100ms, boucle1600ms). Cartes d’indices et alpha fixes ; vraies rotations des palettes,128PNG indexés dans le ZIP et8bandes RGBA. Trois calques séparés : support / flamme / lumière. Aperçu et exports600×448, placements de démonstration amovibles ; aucun objet cuit dans les maps. Atelier8009 ; scripts `source/spinda_torches_v1/`.9originaux générés conservés losslessly dans Git (première face N rejetée, remplacée). Les maps V8/V7 et Beach restent inchangées ; ce pack ne termine pas les meubles/rubans/fenêtres encore en attente. Pas de validation PMDO ou approbation artistique revendiquée.

## Spinda V8 — lot 1 partiel et nuit tamisée (21 septembre 2026)

**[Atelier V8](apercu_cafe_spinda_revisite_v8.html)** · [Jour / nuit](renders/cafe_spinda_revisite_v8/SpindaV8_jour_nuit.jpg) · [Premier lot de mobilier](renders/cafe_spinda_revisite_v8/SpindaV8_mobilier_lot1.jpg) · [Pack autonome](renders/cafe_spinda_revisite_v8/SpindaV8_atelier_lot1.zip).

Demande actuelle : repasser tout le mobilier Halcyon ciblé au générateur, tapis compris ; étendre aux intérieurs pertinents ; une collection commune miel/sauge/crème-rose. Rubans muraux et nouvelles petites fenêtres sur leurs propres calques, mode nuit doux. **Livraison non achevée : limite de10générations atteinte sur ce tour. 9objets retenus ; table vide rejetée (vue du dessous).** Plan36objets :23de V7 +12compléments +1applique nouvelle. **27objets à générer/reprendre, plus rubans et fenêtres.** Ne pas prétendre que les natifs ou recolorations remplacent les générations demandées.

Mode nuit des cinq salles livré :57PNG jour+nuit dans le ZIP, architecture de jour RGBA identique à V7 ; teinte nocturne adaptée, motifs de sol atténués et calque indépendant de lumière diffuse statique. Ni mobilier ni fausses flammes préplacés. Fenêtres V7 héritées provisoirement, pas de nouveau ruban livré.9meubles réellement générés,2tilesheets jour/nuit d’une même collection, inventaire de progression. Pas de validation PMDO ou approbation artistique revendiquée.

Sources : `source/cafe_spinda_revisite_v8/plan.json`, `expanded_sources.json`, `raws/archive.json` (10originaux générés et5banques Halcyon conservés sans perte dans commit7445f0f6). Build/verify/serve dans ce dossier ; serveur8008 lié à0.0.0.0. Les12originaux V4 sont désormais archivés dans Git, lecteurs/restauration vérifiés ; anciens rendus/ZIP et Beach inchangés. Garder l’historique Git complet. Lire [la méthode et les limites](renders/cafe_spinda_revisite_v8/README.md) avant de continuer.

## Historique — Spinda V7 : petites fenêtres, montées occultées, mobilier audité

Dernière demande : fenêtres beaucoup plus petites ; ne plus montrer le palier/étage au-delà des marches montantes ; corriger leurs bordures ; auditer les tailles EoSO/Halcyon ; fournir les vrais comptoirs Spinda/Qulbutoké et des créations Kirlia/Charmilly.

Livraison `renders/cafe_spinda_revisite_v7/`, atelier `apercu_cafe_spinda_revisite_v7.html`. Fenêtre propre au café en32×32, diamètre28 au lieu de64 ; centres préservés. Rectangles N accueil/casino[200,0,400,184] corrigés par génération référencée : marches dans l’ombre sous le mur, joues basses sans volutes, aucun étage supérieur visible. Architecture hors rectangle bit-identique, S/E/O et graphe conservés. Module de raccord contient aussi mur/sol ; pas un escalier natif autonome.

Audit de8banques : EoSO SpindaCafe1/2, Halcyon objets/Over Café Metano, auberge, réfectoire. **30 objets/modules natifs**, **4 créations** (comptoirs frontaux Kirlia/Charmilly, banquette, desserte), **4 tilesheets** : PNG séparés +index de rectangles8px. Tables Spinda43×43 (canevas48×48), comptoirs natifs120×96 de canevas (120×88 visibles). Comptoirs = détourage manuel du Ground ; pixels RGBA visibles identiques à la référence, pas de reconstruction IA des parties cachées par les rubans. Natifs jamais redimensionnés/recolorés/retournés. Les créations sont explicitement non natives, normalisées avec aspect conservé. Aucune fenêtre Guilde réutilisée. Rien de ce mobilier n’est préposé sur les maps.

Deux ZIP : objets/tilesheets et pack complet autonome avec26PNG de salles +catalogue +atelier. Le dépôt lit les calques V6 avec deltas explicites ; le ZIP matérialise tous les calques. Tests d’images/pixels, archives, atlas et DOM simulé. Pas de navigateur graphique/PMDO, aucune approbation artistique des nouvelles images revendiquée.

Sources complètes préservées sans perte dans Git : **les4bruts V6 et7générations V7** (y compris2premières perspectives de comptoir non retenues), index `source/cafe_spinda_revisite_v7/raws/archive.json`, lecteur/restaurateur `archive.py`. Les ZIP/rendus V6 restent bit-identiques ; ancien build adapté au lecteur d’archive et testé. Le serveur sert aussi les anciennes URL de bruts depuis Git. Serveur V7 : `python source/cafe_spinda_revisite_v7/serve.py --port 8007`, 0.0.0.0. Préserver l’historique complet pour reconstruire les sources archivées. Beach trois ambiances inchangé.

Les rubans natifs sont des modules de bibliothèque, pas un ajustement automatique sur les nouveaux murs. Pas de nouvelle collection de tapis rouges annoncée. Collisions, warps et validation moteur restent à faire.

## Historique — générations N/S V6 et ciels Beach trois ambiances

Après approbation de l’audit (« Parfait, passe à la génération »), trois nouvelles salles sont livrées dans `renders/cafe_spinda_revisite_v6/` : accueil N↑/S↓, casino N↑/E plat, café S↓/E plat. Deux salons V4 conservés. Atelier `apercu_cafe_spinda_revisite_v6.html`, 26 calques PNG contenus dans le ZIP et lus directement par l’atelier (pas de doublons). Quatre bruts complets archivés WebP lossless : 3 salles + nouvel oculus café. **Escaliers redessinés par le générateur d’après la référence : pas identité pixel de l’audit V5.** Repères recalés N[304,88]/arrivée[304,200], S[304,384]/arrivée[304,280] ; graphe réciproque testé, aucune installation moteur.

Fenêtre café générée avec cadre miel et vitrage doux, 72×72 séparée, sans utiliser le sprite Guild_Heros_Room_Objects. Deux instances café, trois salon haut. Le plan N/S est approuvé, **ces nouvelles images ne sont pas encore approuvées artistiquement**. Pas de nouvelle sortie extérieure. Mobilier/rubans/tapis assortis encore à produire ; le catalogue et les flammes sont hérités de V4, pas de nouveaux meubles revendiqués.

Portée ciel confirmée par l’utilisateur : **réseau Beach dix cartes + plage de référence uniquement**. `renders/beach_sky_gradient_v3/`, atelier `apercu_plages_ciels_v3.html`. Jour/nuit : lignes natives 8px issues des banques EoSO, sans changement de couleur/échelle ; nuit comparée au GIF fourni (70 lignes identiques). Crépuscule violet-corail reconstitué d’après `IMG_4888.jpeg` : **pas un sprite natif certifié**. Sans lune, étoiles fixes et petits nuages séparés ; wrap64s. Terrains et animations antérieurs inchangés (réseau32×100ms, référence64×50ms). Au crépuscule, terrain de jour conservé sans filtre. 39 sélections/modes/layouts testés en DOM simulé. Aucun navigateur graphique testé : téléchargement Chromium refusé par TLS. Aucun runtime PMDO.

Pour la limite de stockage, sept études V4 supplantées sont conservées bit-identiques dans l’historique Git via `bruts/archived_studies.json` ; cinq bruts actifs, anciens calques/rendus et ZIP inchangés. Vérificateur adapté, restauration `python source/cafe_spinda_reseau_v4/archive_studies.py --restore`. Ne pas supprimer d’autres livraisons arbitrairement. Scripts de build/tests dans les deux nouveaux dossiers source ; serveur commun `python source/cafe_spinda_revisite_v6/serve.py`, port8006, lié à0.0.0.0.

## Historique approuvé — audit des quatre escaliers N/S

Dernière correction utilisateur : conserver l’escalier de référence et le placer au NORD ou au SUD selon l’étage, pas le redessiner en version latérale. Le choix initial E/O est remplacé. **Accueil0 : N monte vers café+1, S descend vers casino−1. Casino−1 : N monte vers accueil0. Café+1 : S descend vers accueil0.** Retours opposés N↔S ; passages E/O entre salons sans changement de niveau.

Audit livré dans `renders/cafe_spinda_revisite_v5/audit/` : image annotée, `AUDIT.md`, `plan_escaliers.json`, `verification.json`. Script `source/cafe_spinda_revisite_v5/audit_escaliers.py`. Bases générées V4 conservées, marches de l’entrée choisie réutilisées exactement à l’échelle V4, sans rotation/étirement. Nord : module232,56 +palier/cheeks ; café sud :232,324 ; accueil sud intact. Ancien trou sous les marches nord corrigé (coupe jusqu’à128, pas136). Quatre accès/2liens réciproques, pixels source exacts, contacts au sol et bandes40px opaques, empreintes16px, deux contre-tests PASS. **PAS une validation collision, warp ou runtime PMDO.**

Prototypes latéraux et anciens guides explicitement obsolètes, conservés comme historiques. Les nouvelles générations N/S d’essai ne sont pas utilisées : retouches locales sur la V4 pour garder le vrai dessin choisi. PNG d’audit régénérables dans `audit/exports/`, ignorés pour éviter les doublons. Les deux sorties de l’accueil sont internes : accès extérieur non défini, ne pas ajouter une troisième sortie sans accord. Mobilier/rubans/tapis V5 restent à produire ; l’audit n’est pas une livraison de tout le kit.


## Historique — premier prototype Spinda V5, avant la correction N/S

L’utilisateur demande désormais des fenêtres, escaliers et meubles **générés pour correspondre aux maps**, les références natives servant de modèles ; rubans ajustés aux murs, tapis rouges modulaires et décorations séparées. Il choisit deux sorties LATÉRALES à l’accueil (montée + descente), supprimant la sortie sud ; retour montant en sous-sol, descendant à l’étage.

Il insiste ensuite, image à l’appui, pour reprendre **le petit escalier de l’ancienne entrée sud de l’accueil** : marches gris-brun peu profondes, rebords rocheux recourbés, lumière dorée qui décroît vers l’extérieur. Pas de bois massif, rampe blanche, spirale, porte massive ou hautes marches latérales ressemblant à une barrière. Voir `source/cafe_spinda_revisite_v5/WORKFLOW.md` avant de continuer.

V5 est EN COURS, pas livré : un prototype généré de descente vers l’ouest128×72 et une fenêtre générée56×64 dans `renders/cafe_spinda_revisite_v5/prototypes/`, non approuvés/non placés. Les six essais de salles ne sont pas retenus. Intermédiaires de recherche V5 en.cache, non livrés ; empreintes enregistrées. Référence du seuil conservée, ainsi que les PNG normalisés. Aucun mobilier/ruban/tapis V5 encore produit, aucun pack ou atelier V5 terminé. V4 et toutes les anciennes livraisons restent intactes. Branche de session inchangée.


## Correction prioritaire — Spinda V4 généré, cinq pièces et trois niveaux

L’utilisateur a corrigé explicitement la méthode : **génération avec références canoniques, bordures immersives, zones séparées, réseau à plusieurs étages, fenêtres circulaires à croisillons** ; puis « voilà regarde café spinda reprend ce design là ». Ne PAS reprendre les bandes Métano comme solution à cette demande. L’accueil `accueil_spinda_fidele` option1 a été choisi ; quatre déclinaisons séparées ont suivi. Café et salon haut ont été régénérés une seconde fois pour retirer façade avant et faux ovales muraux. Bruts retenus indiqués dans le manifeste ; douze bruts/études conservés losslessly avec empreintes. Les autres salles n’ont pas encore d’approbation artistique utilisateur.

Livraison : `renders/cafe_spinda_reseau_v4/`, `apercu_cafe_spinda_reseau_v4.html`, scripts et workflow dans `source/cafe_spinda_reseau_v4/`. AccueilRDC ; casino+salonbas−1 ; café+salonhaut+1. Générations1200×896→600×448 NN, uniquement sur le généré. 25calques : sol, lumières statiques, parois, bordures, fenêtres si étage, escaliers de proposition optionnels/désactivés. Pas de meuble, feu ou NPC dans la scène. Terrain généré référencé ≠ natif. Petit avis mural de l’accueil retiré localement avec bois voisin et raccord adouci ; brut choisi intact.

Vraie fenêtre HeroObjects64² crop176,56–240,120 ; deux au café, trois au salonhaut. Escalier spiralé SecondFloorObjects96×72 crop208,128–304,200. Banques Halcyon au pin da6c2130d641507447e6386a5e47a296e8cb4c71 ; pixels natifs sans resampling/recoloration. Feu = quatre vraies poses Ledian6ticks, pas une animation de la lumière du sol. Deux feuilles Spinda natives et kiosque arrière/avant, fourneau généré et support natif dans le catalogue, non placés.

Quatre liens réciproques de conception ; **pas de warps/ground/collisions installés**. Portes E casino/café et W salonhaut versy232, porte W salonbas plus basse. Cartes distinctes, PAS seamless. Le relevé de passage vise le sol clair, pas la face verticale du mur au-dessus. `plan.json`/`guides512²` historiques, coordonnées finales dans le manifeste600×448. Escaliers sur calques facultatifs : suggestions de placement, pas jeu testé.

Pixels, archives, recomposition et banques natives vérifiés ; DOM dépôt/ZIP et redirection racine vérifiés ; pas navigateur graphique ni PMDO. Dépôt : calques WebP lossless ; ZIP :25PNG exacts +catalogue +viewer. Noms d’import uniques, grille8px. Les guides ne sont pas imprimés dans les exports.

Budget : les sept bruts terrain BeachNetwork ont été archivés WebP après comparaison RGBA exacte et traceSHA des PNG d’origine ; loader accepte les anciens cheminsPNG via l’archive vérifiée. Le viewer BeachV1 réutilise ses138PNG existants ; le packaging réembarque les données pour les futurs ZIP. **Rendus et ZIP Beach antérieurs inchangés.** Tests d’images ancienZIP/dépôt/futurviewer portable et DOM, ainsi que loader/provenance des neuf sources BeachNetwork. Voir les scripts dédiés, ne pas prétendre avoir refait une vérification graphique ou moteur.

Préserver les anciens cafés, casino, plages, études et stashes. Session sur `arena/01a0bf18-guilde-treehouse-pmd` exclusivement. Voir WORKFLOW et README V4 avant toute reprise.


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


## Beach Network V1 — ciel corrigé et réseau Ledian adapté à la plage

Correction utilisateur prioritaire : **régénérer le ciel de référence adapté à la plage SANS LUNE**, nuages PLUS PETITS en **wrap overlay loop parfait** ; puis plusieurs carrefours/maps « aglomératives » comme Ledian. Ne pas réutiliser le crop lunaire rejeté. Nouveau chantier `source/beach_network_v1/`, `renders/beach_network_v1/`, `apercu_reseau_plage_v1.html`. Anciennes V2/V3 absentes de ce checkout ; ne pas annoncer leur restauration.

Six générations terrain512² normalisées depuis1024², deux carrefours T/croix, 15ports96px et septliens en3×2. SourcesDSVFS+guides,03corrigée retenue ; pas pixels natifs certifiés. Patch de sable source296,168–392,216, profondeur48, noyau16px opaque identique sous toutes orientations, rotations/transpositions assumées hors méthode Métano stricte. Connexité centre→quinze accès validée avec distance≥8. Contours rocheux complets aux jointures et collisions moteur NON certifiés.

Ciel généré sans lune/halo ; nuages3groupes centraux complets,≤96×28, strip512×112 transparent, marges24 ;8px/s,512pas×125ms=64s. Ciel partagé, pas répété entre modules. Eau/écume32×100ms ; correctif important : helper V1 seul laissait l’écume01statique. `contact_foam` ajoute un liseré périodique≤3px reprenant les couleurs côtières, exclut feuillage et laisse rochers immobiles. Toutes les pistes ont désormais plusieurs frames distinctes. Plage de référence : terrain V1inchangé,64×50ms+nouveau liseré, ciel remplacé. Ne pas confondre cette réalisation avec la récupération deV2/V3.

13tests assets PASS, DOM simulé PASS, packCRC/identité PASS ; aucun navigateur graphique ni PMDO validé. Jour/nuitAbyss exact pour terrain/frames ; ciel/nuages nocturnes déjà colorés, pas doublefiltre. ZIP autonome exports/viewer, sans bruts ni sources de rebuild ; sesliens selfZIP supprimés pour ne pas pointer vers une archive absente. Sources/build complet au dépôt. Budget cumulatif~125,6Mo proche128Mo : remesurer avant d’ajouter des animations ou copies lourdes.


## Beach Extension V2 — quatre modules supplémentaires, réseau de dix

À la nouvelle demande de continuer les carrefours/plages agglomératives comme Ledian : **ajouter**, ne pas remplacer les sixV1. `source/beach_extension_v2/`, `renders/beach_extension_v2/`, `apercu_extension_plage_v2.html`. 07T(NES),08T(WES),09croix(NESW),10baie(NW) ; positions(1,2),(2,2),(1,3),(2,3). Nouvelle liaison05S↔07N ; ensemble10cartes/12liens/27ports, troisextensions08E/09W/09S. Seul le manifestecombiné change la destination05S ; fichiersV1, ciel/nuages et ZIPV1 inchangés par hashes.

Cinq générations : première07fermée par meràE, corrigée réellement via générateur, correction retenue. Bruts archivés enWebPlossless, égalitéRGBA avecPNGsource vérifiée avant substitution ; provenance/hashes dansbruts/provenance.json. Pas derégénération de ciel. 80PNGcalques512² +16atlaslossless(512frames), Abyss exact, écumecontact≤3px héritée du nouveau helperV1. ZIPV2 autonomequatrepièces, sansV1/bruts/compositesredondants ; exporteurportable reconstruit8compositions+512framesPNG, testéexact. Previewréseau768×1024 à50% explicitement ; assetsnatifs512².

13tests assetsPASS, DOMsimulé viewerscombiné/ZIP PASS (ycompris ports externes/réservés, zonesvides, messagespersistants, erreurs exportfile-origin), CRC/identitéZIP PASS ; HTTP263URLsPASS. Aucun navigateurgraphique niPMDO validé. Raccords96×16 testés sur27accès ; contoursrocheux complets noncertifiés et collisions/warps àfaire.

**Gestion budget** : duplication V1 framesPNG(768),ORA(12),compositions(12) exclue duGit, mais792exports originaux restent dansZIPV1 inchangé. `source/beach_network_v1/restore_exports.py` extrait cesfichiers byte-identiques s’ilsmanquent ; appeléparbuild/verifyV2 etverify/packageV1. Ne pas supprimer l’archiveV1 sans réintégrer cesexports. Testtemporaire de restaurationPASS. Budgetactuel~125Mo : éviter reduplications lourdes.

ServeurV2 : `python source/beach_extension_v2/serve.py --port 8002` sert`renders/`etredirigeversindexV2 ; nécessaire pourlesréférences partagées `../beach_network_v1/`. Servir uniquement le sous-dossierV2 casserait lesanciensassets. LeZIPportable n’en dépendpas. LesPNGexportés facultatifs `renders/beach_extension_v2/export_png/` sont ignorés, régénérablesdepuislesatlas.


## Casino Ledian — nouvelle portée : réseau avec décoration multicalque

L’utilisateur a renvoyé visuellement la première salle choisie et demande maintenant un **réseau casino** sur terrainLedian, tapisrouges/estrades/rideaux et mobilier/kiosques indépendants, en prenant les objets Métano comme référence, particulièrement Murkrow. **Cette demande remplace le « sans déco » initial pour les overlays** ; conserver une basevide, nepas cuire les accessoires danslesol. Borduresrocheuses doivent suivrelesentrées réellementouvertes.

Recherche Halcyon via `gh`, commit épinglé `da6c2130d641507447e6386a5e47a296e8cb4c71` (master consulté) : KrowBank confirmé par init.lua Bank_Owner=Murkrow et metano_town_ch_2.lua460–466. Toiture noire/becdoré dansObjects ; guichet/coffresdansObjects_Over. Deuxextraits natifs alignés104×96 et leurrecomposition dans `source/ledian_casino_v1/references/`, fenêtre976,928–1080,1024 ; toiturelimitéeaux48premièreslignes. Aucunresampling/recoloration. BanquesvérifiéesparGitblob. Script `inspect_krow_bank.py`, provenanceJSONetREADME de conception.

Blocageimportant : imageattachée visible danschat, annoncée `/home/user/uploads/image-1.png`, maisfichier absent pourbash/read_file, recherches/home/user,/tmp,/mnt négatives. Ne pasaffirmer chargement/détourage/correctiondel’image choisie etnepas laremplacerparleguide512initial. Réseau4salles etcalquesaménagement décritscomme **plan de travail seulement** ; àcestade seulesl’étude etlesréférencesobjetssontproduites. Aucunevalidationmoteur.


## Casino Network V1 — génération indépendante autorisée, décor et vraies flammes

Dernière demande : générer directement un réseau indépendant de l’image choisie, mêmes matièresLedian mais réaménagementcasino ; décor assorti, torches/fourneaux avec framescanoniques Halcyon. **Ne plus bloquer sur l’upload absent.** Réalisation `source/casino_network_v1/`, `renders/casino_network_v1/`, `apercu_casino_reseau_v1.html`. Une composition terrain1024² continue (4secteurs512²), pas4copiesdepièce. Terraininitialpanoramique écarté ; correctioncarrée retenue. Cinqnouveauxobjetsgénérés : estrade,rideaux,kiosque,table,fourneau ; seul lecorpscentral complet des3fourneaux dessinés parlemodèle estutilisé. SeptbrutsWebPlossless conservés.

38instances :5terrain,4tapis,estrade+rideaux,3kiosques(dontKrowBanknatif),4tables,2corpsfourneau,8supportsbrasero,10flammes. Motifdetapisnatif LedianObjects crop176,136–232,176 répété enpatches8px ; masqueuniquetexturé avantpartitionsectorielle, pasdoublebordureauxjonctions. Pasderecoloration/étirementdetapisnatif. Terrain etmeublesgénérés ≠ assetsnatifs ; basesolintactsousmobilier.

**Feucanonique réellement extrait** : GroundLedian, layer1ObjectsUnder, instancecellules14,11–18,19 ; banqueLedian_Dojo_Animated.tile,4poses,FrameLength6ticks.32×64chaquebrasero ; rows0:40flamme32×40,rows40:64supportinvariant. PNGbytes exactspourles4poses, aucunresampling/recoloration. Viewer100ms/pose(60Hz),400ms. Corpsdesfourneauxgénérésnoncanoniques, flammeLedian inchangée ajoutée séparément ; hôtemasqué→feumasqué, déplacementhôte→feusuiveur.

13testsassetsPASS, DOMsimulénormal/ZIP PASS,154PNGalignés(ensemble+4secteurs) pixelsvérifiés. Cheminprincipaldes tapisconnectéavec8pxdégagement après empreintesmeublespardéfaut ; **pas collisionsnatives/warps/hauteurs testées enmoteur**. AperçuWebPanimé exact enalphaetRGBvisibles ; RGBsousalpha0 peuventdifférerduPNG. Cadencevérifiéedanssourcepasinventée. AucunruntimePMDO/navigateurgraphiquevalidé.

Préserverbudget : seulescopiesintermédiaires terrain_vide.webp etexport_png sontignorées/reconstructibles. Ancienrenders/beach_layers_v1/index.html(duplication7Mo) redirigemaintenantvers../../apercu_beach_calques_v1.html, dontlecontenuautonomeestinchangé ; imagesetZIPBeachV1inchangés, testDOMV1repassé. Cloneavaitété réinitialiséau3d4ea6f0 : reprise parfetch+mergeff-onlyvers a91c3bd6 surlamêmebranche ; ancienétatlocalpréservédansstash«Preserve restored workspace…», nepaslepopautomatiquementsurlanouvellelivraison.


## Consigne permanente — fond magenta et places de PNJ libres

Dernier rappel utilisateur : **toutes les zones générées doivent être sur fond magenta**, et pensées pour des **kiosques vides où des Pokémon pourront être placés ensuite dans l’éditeur**. Fond de génération/référence `#FF00FF` ; les calques PNG d’import restent transparents. Ne pas intégrer de PNJ ou de silhouette-placeholder dans les images, ne pas cuire les structures dans le sol ; préserver un poste libre derrière le comptoir et l’accès client.

Casino : `source/casino_network_v1/editor_setup.py` produit deux plans arrière/avant par type de kiosque et `renders/casino_network_v1/editeur/placements_pnj.json` avec3emplacements liés aux hôtes existants. Recomposition exacte des anciens sprites, aucun Pokémon ajouté. Ordre d’intégration : fond → PNJ ajouté dans l’éditeur → devant/comptoir. Le viewer actuel conserve ses38instances fusionnées ; remplacer le kiosque fusionné par les deux plans lors de l’intégration, ne pas les superposer au sprite complet. Repères visuels et collisions suggérées uniquement, pas d’entités ou de Ground PMDO créés. Repères à ajuster au gabarit/pivot du Pokémon.

`Casino_terrain_magenta.webp` et `Casino_reseau_magenta.webp` sont des exports opaques surmagenta pur, distincts des calques transparents. `export_png.py --magenta` exporte aussi la composition du secteur choisi surmagenta, sans modifier l’alpha des calques. Le kit PNJ est inclus dans le ZIP ; grosses vuesmagenta conservées dans le dépôt, régénérables par script.


## Historique — café Halcyon agrandi (avant la correction Spinda)

Après la demande de biome bois et l’exemple de kiosque Arcanin, l’utilisateur demande explicitement : **« J’aimerais une zone café pour notre PMDO, reprends celui de Halcyon et agrandis-le »**. Cette étape est conservée, mais remplacée pour la demande actuelle par Spinda V4. Conserver sa consigne de mobilier/structures/flammes sur feuilles distinctes : il place ses décorations et Pokémon dans l’éditeur. Le magenta reste obligatoire pour la référence, l’alpha pour l’import.

`source/cafe_halcyon_agrandi_v1/`, `renders/cafe_halcyon_agrandi_v1/`, `apercu_cafe_halcyon_agrandi_v1.html` : véritable Base de `metano_cafe.rsground`, sources Halcyon déjà épinglées dans `source/cafe_multietage_v1/references/`.456×320 →840×576, pas de génération de matière et pas de resampling. Bandes natives64px répétées, coins intacts, portail natif complet repositionné ; ancien portail recouvert d’une bordure native et lacune alpha du seuil comblée par une tuile de plancher adjacente. **Entrée =56px de sol (60avec encadrement), x456:512, centre484 ; pas24px.** Petites poussières extérieures déconnectées retirées après détourage du fond brun.

5calques transparents alignés ; toutes les couleurs visibles correspondent aux vrais pixels source. Les rubans architecturaux intégrés à la Base sont conservés : ne pas prétendre qu’ils sont détachables ou que les murs derrière eux sont reconstruits. Quatre feuilles d’objets originales séparées, support natif et corps de fourneau généré/non natif facultatif, quatre poses réelles Ledian sous forme de8PNG et2atlas. Zéro meuble, feu ou NPC placé sur le terrain ; guides de service et salle facultatifs, non imprimés dans les exports.

11tests assets PASS, banques réellement redécodées ; viewer normal et ZIP extrait testés en DOM simulé. Pas de navigateur graphique ou de PMDO validé, pas de `.rsground` produit, collisions/warps/interactions à configurer. Les couches de terrain sont des surfaces visibles, pas des murs mobiles complets. Ne pas écraser les anciens cafés multietages ni le casino.

Étude bois précédente mise en attente : aucun terrain retenu/sauvé par le comparateur. Sources bois consultées et brut du kiosque Arcanin conservés dans `source/casino_bois_v1/` et `renders/casino_bois_v1/bruts/` ; ce kiosque est un prototype généré non natif/non approuvé, **pas inclus dans le pack café**. Référence miniature en ligne, original de pièce jointe absent du filesystem : ne pas prétendre une extraction pixel-exacte de l’upload. Au début de cette reprise le clone était à3d4ea6f0 ; état restauré conservé en stash avant ff vers954c705e, ne pas pop automatiquement.
