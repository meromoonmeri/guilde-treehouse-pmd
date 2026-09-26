# Reprise des maps — 20 septembre 2026

## Demande actuelle

Reprendre la création de maps avec textures canoniques. **Mise à jour du 25 septembre** : l'utilisateur a choisi une entrée de donjon sud → nord, la méthode rendu généré et les deux livrables (PNG 8 px + Ground). Premier lot : `renders/entree_vapeur_sud_nord_v1/`, biome Steam Cave choisi par l'agent et à confirmer. Les anciens travaux sont conservés. **V2** (`renders/entree_vapeur_sud_nord_v2/`) : eau façon rivière Métano, scintillements Métano, bulles de marais générées ; V1 intacte. Map suivante réalisée : **Entrée Cratère** (`renders/entree_cratere_sud_nord_v1/`, réf. Dark Crater, biome choisi par l'agent et à confirmer). Puis **Entrée Ruine** (`renders/entree_ruine_sud_nord_v1/`, réf. Sealed Ruin) et **Entrée Givre** (`renders/entree_givre_sud_nord_v1/`, réf. Frosty Forest, neige). Puis **Entrée Bristle** (`renders/entree_bristle_sud_nord_v1/`, réf. Mt. Bristle, canyon de sable et torrent). **Nouveau standard demandé (26 septembre) : maps plus vastes au format 4:3** — premier lot `renders/entree_jungle_sud_nord_v1/` en 768 × 576 (96 × 72 cases). L'utilisateur a demandé de continuer la série de maps. **Puis Entrée Cascade** (`renders/entree_cascade_sud_nord_v1/`, réf. Waterfall Cave) : l'utilisateur a interrompu le rendu généré pour demander **les textures canoniques** → lot construit en pixels natifs exacts (Waterfall Cave ledge + gem, cascade et scintillements Métano natifs), le brut généré n'étant qu'un guide de composition. Tant que l'utilisateur parle de « textures canoniques », les prochaines maps suivent cette méthode.

Reprise du 25 septembre : `.venv` absente du checkout puis recréée (Pillow 12.3, NumPy 2.4, SciPy 1.17). Les tests V16 + sud–nord V3 donnent de nouveau 18/19, avec la même erreur liée à l'objet historique `438b9288`.

Reprise du 26 septembre (session `arena/01a0dc9b`, branchée sur `0eaa002c` = Entrée Jungle V1) : lecture de `README.md`, `AGENTS.md`, `MANUEL_METHODE_PMDO.md`, de ce fichier, du `WORKFLOW.md` magenta et des sources des six entrées sud → nord. Distant vérifié avant tout travail : la branche parente `arena/01a0da3c` est bien à `0eaa002c`, aucun commit parallèle. `.venv` et `.cache` absents, `.venv` recréée (Pillow 12.3, NumPy 2.4, SciPy 1.17 ; pas d'OpenCV ni de Playwright). `build.py` de la Jungle relancé : sorties byte-identiques aux fichiers versionnés (seuls les horodatages internes de l'ORA changent, fichier restauré), Ground reconstruit dans `.cache`, **9 tests PASS**. Références PMD encore inutilisées à la racine pour la suite de la série 4:3 : `Mystifying_Forest_entrance_TDS.png`, `Underground_Lake_shore_TDS.png`, `Waterfall_Cave_ledge_TDS.png`, `Waterfall_Cave_gem_TDS.png`, `Foggy_Forest_Base_Camp_TDS.png` (campement, pas une entrée), `Sealed_Ruin_pit_TDS.png` et `Southern_Jungle_exit_2_S.png` (salles de fond, pas des entrées). Aucune nouvelle map produite dans cette reprise.

## Méthode courante des entrées sud → nord (résumé opératoire)

Pipeline reproduit par les six lots `source/entree_*_sud_nord_v1/` (V2 pour la Vapeur) ; le lot Jungle est le gabarit 4:3 à copier :

1. **Générer** trois bruts dans `bruts/` : `decor_magenta.png` (décor complet, eau/lave = magenta, prompt « WIDE LANDSCAPE 4:3, zoomed out » → 1200 × 896), `sol_complet.png` (sol seul, même cadrage, édité depuis le décor) et une planche de poses pour l'animation propre au biome (papillons, flocons, bulles, touffes…). Relancer avec un prompt plus court si le générateur ne renvoie rien.
2. **Segmenter en pleine résolution** (`classify`) par mesures colorimétriques documentées dans le code, puis **réduire par classe** (`down_class` : réduction BOX uniforme 576/896, attribution exclusive au poids maximal, jamais l'image entière avant segmentation), recadrage centré à 768 × 576, palette commune de 96 couleurs (`quantize_layers`), palettes séparées si une matière vire.
3. **Animer chaque effet sur son calque** : eau « façon rivière Métano » (`water_phases`, 4 × 10 ticks : bande, intermédiaire, frange dentelée, lèvre claire, aplat), scintillements Métano natifs (`sparkle_families`, pixels de `Metano_Town_River_Sparkles.tile` inchangés), poses générées extraites d'une planche (`extract_poses`/`butterfly_poses`, réduction uniforme, palette de 7 couleurs), boucle fermée testée (dernière → première), scène au PPCM des cadences.
4. **Collisions et accès** : `cell_grid` (case bloquée si > 25 % hors sol praticable), `entrance` sur la case 2 × 2 libre la plus proche de la médiane du bas du chemin, `donjon_seuil` sous la bouche, chemin 16 × 16 vérifié par `reachable`, aucun warp.
5. **Exports** : calques PNG `PFX_NN_nom.png`, frames `animation/<effet>/`, masques, ORA (`write_ora`), `review/` (scène t000, WebP animé, collisions), `manifest.json` (hashes des bruts, normalisation, origine de chaque matière, `art_approved: false`, `runtime_tested: false`).
6. **Ground PMDO 0.8.12** (`ground_project`) : gabarit `v50812_01_crete_sillage_jour.rsground` du mod Expéditions, une banque `.tile` par calque via `TileBank`, calque Top vide `Layer=4`, `index.idx`, `Mod.xml`, `INSTALLER.py` ; staging dans `.cache/<lot>/`.
7. **Tests puis paquet** : `test_build.py` (hashes, tailles/alpha/pas de magenta, couverture, structure et boucle de l'eau, scintillements natifs, boucle des poses, ORA = scène, accès, aller-retour Ground/`.tile`/index), puis `package.py` (ZIP projet, ZIP calques 8 px, aperçu autonome `apercu_<lot>.html`). Documenter dans `README.md` du lot, `README.md` racine, `AGENTS.md` et ce fichier ; **commit + push sur la branche de session après vérification du distant**.

Ce qui reste toujours vrai : terrain et poses **générés** (pas de tuiles natives certifiées, sauf les scintillements), eau **façon** Métano (pixels recalculés, couleurs Métano exactes seulement quand le biome le permet), biome choisi par l'agent à confirmer, pas de variante nuit, pas de test PMDO en jeu.

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
