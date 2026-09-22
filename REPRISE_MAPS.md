# Reprise des maps — 20 septembre 2026
## CANON1 — quatre maps en cellules natives 24 px, aucune pixel inventé (22 septembre 2026)

**[PNG collection 4 cartes × jour/nuit](renders/canon_dtef_v1/apercus/CANON1_collection_1x.png)** · [entrée jungle](renders/canon_dtef_v1/apercus/CANON1_JC1_entree_jour_1x.png) · [finale jungle](renders/canon_dtef_v1/apercus/CANON1_JC1_finale_jour_1x.png) · [entrée forêt](renders/canon_dtef_v1/apercus/CANON1_TC1_entree_jour_1x.png) · [finale forêt](renders/canon_dtef_v1/apercus/CANON1_TC1_finale_jour_1x.png) · [cycle animé WebP](renders/canon_dtef_v1/apercus/CANON1_JC1_entree_cycle.webp) · [pack ZIP](renders/canon_dtef_v1/Canonia_DTEF_v1.zip). Sixteen direct previews `CANON1_<carte>_<mode>_1x.png` (648×504 à 1×) plus huit bandes de controle 3x ; aucun livrable ne dépend du HTML.

Demande : poursuite des maps **en textures canoniques**, en spriter. Route retenue et appliquée intégralement : chaque case exportée est une cellule native 24 px prélevée dans les banques DTEF épinglées (`Content/Tile/{SouthernJungle,TreeshroudForest1}.tile`, SHA‑256 contrôlé), placée par la sémantique autotile du moteur (`AutoTileAdjacent.cs` : bits Dir4 = Bas/Gauche/Haut/Droite, quadra seulement si les deux cardinaux et la diagonale suivent, 47 masques, sélection de variante par zéros de poids faible). Ni bombing de variantes, ni agrandissement, ni miroir, ni recoloration, ni repeintage. `renders/donjons_generes_dtef_v3`, `source/designs_dtef_v4` et `source/donjons_10_biomes_v1` restent non canoniques et sont gardés tels quels.

Livré : deux duos entrée/finale (jungle des donjons PMDO, forêt claire), canevas 27×21 cases = 648×504 px (dimension exacte de l’entrée de Brine Cave auditée), 4 groupes sémantiques réels par carte (`01` sol continu, `02` murs/relief, `03` secondaire statique, `04` secondaire animé — cadence native : 1 groupe de 16 frames @19 ticks pour les 47 masques secondaires de la jungle, 2 groupes de 12 frames @18 et @6 ticks en forêt, PNG + `.ora` + composition, nuit = filtre Abyss existant appliqué une seule fois aux mêmes tuiles, zoom de contrôle sur le passage nord. Export DTEF 432×192 avec bandes de frames et durées en ticks, Ground 8 px `TexSize=1` (tuile native = 9 cellules, aucune interpolation), `Mod.xml` + `index.idx` fusionnable via l’`INSTALLER.py` partagé, ZIP autonome 7,8 Mo / 220 membres, `sha256` et contrôle CRC consignés dans `renders/canon_dtef_v1/pack_verification.json`.

Vérification : `source/canon_dtef_v1/verify.py` recalcule le placement depuis les plans `layouts/*.txt` et les règles du moteur, puis compare octet à octet (12 contrôles, niveaux A–D du manuel plus aperçus, tous PASS) : banques = provenance épinglée, 47 masques = `FieldDtefMapping`, chaque cellule = cellule native, aucun RGBA de jour hors des tuiles de la banque, sol continu sous tout, nuit non cumulable et alpha intact, composition en t = composition en t + cycle, frames animées = nombre et durée natifs, feuilles DTEF = extraction pure avec écart chiffré face au « bombing » V2, Ground relu = banques natives, obstacles alignés 8 px, banque étrangère préservée à la fusion d’index. **Aucun rendu PMDO, aucun test moteur, aucune session de jeu, aucune approbation artistique** : niveau E non exécuté, dit comme tel.

Matière et limites annoncées : la banque d’autotile d’un donjon ne contient que Wall/Secondary/Floor (905 cellules SouthernJungle, 1 234 TreeshroudForest1, zéro tuile d’objet/escalier/coffre vérifiée) — donc pas de props canoniques à poser ; les futures structures (pieu, escaliers, PNJ, scripts) restent des zones `R` vides et documentées dans `manifests/<carte>/geometrie.json`. Le sol uni est natif (seul le masque 0xFF varie, 3 variantes, distribution du moteur) : masses ≥3×3 et obstacles rectangulaires pour que les raccords pleins apparaissent ; une poche de 1–2 cases rend mal et a été supprimée, pas repeinte. Zones `R` non construites, warps non branchés, collisions dérivées du layout (mur et secondaire bloquants) et à contrôler dans l’éditeur. Scripts `source/canon_dtef_v1/` (autotile, native, layouts, build, verify, package, serve, pmdo_ground), méthode et limites dans `source/canon_dtef_v1/README.md`, import dans `renders/canon_dtef_v1/README_import.md`, serveur `8013` (racine = dépôt, PNG directs).

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


## Demande actuelle

### Historique — café Halcyon agrandi (remplacé par la direction Spinda)

Utilisateur : reprendre directement le café d’Halcyon et l’agrandir pour PMDO. Livraison `renders/cafe_halcyon_agrandi_v1/`, viewer `apercu_cafe_halcyon_agrandi_v1.html`, scripts dans `source/cafe_halcyon_agrandi_v1/`.

Terrain840×576 au lieu de456×320 (canevas×3,32), entièrement en vrais pixels natifs sans resampling, cinq calques, magenta +alpha. Bandes entières64px, coins conservés, portail sud complet56px de sol ; pas de seconde ouverture ni de trait alpha sur son seuil. Quatre planches meubles natives et deuxatlas feu/fourposes, huitPNG individuels, support et fourneau facultatif non natif séparés. Zéro mobilier/feu/PNJ posé. Rubans fixes muraux du café source conservés, pas présentés comme des objets détachables.

11contrôles assets PASS, viewer/ZIP en DOM simulé PASS, pas de navigateur graphique ni de validation PMDO. Collisions/transitions/NPCs non configurés. Sources déjà présentes dans `source/cafe_multietage_v1/references/`. Anciens cafés/casino inchangés. Brouillon casino bois mis en attente, pas de terrain choisi ; prototype Arcanin archivé sans perte, non natif/non validé/non inclus dans le café.


### Rappel prioritaire — magenta et kiosques sans PNJ intégré

Utilisateur : push + toutes les zones générées sur fond magenta, kiosques vides permettant le placement ultérieur de Pokémon dans l’éditeur. Consigne inscrite dansAGENTS. Ajout Casino : exports terrain/réseau surmagenta pur ; deux plansarrière/avant par type de kiosque, troisrepèresPNJ avecpointclient (`editeur/placements_pnj.json`), sans aucuneentitéPokemon ajoutée. Recomposition des sprites existants exacte. Le kit remplace les sprites fusionnés lors de l’intégration, ne pas les empiler ; pas d’intégration PMDO revendiquée. `editor_setup.py` appelé parbuild, kitinclusdansZIP, exportPNGoption`--magenta`.


### Livraison précédente — Casino Network V1

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
