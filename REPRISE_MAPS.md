# Reprise des maps — 20 septembre 2026

## Demande actuelle

Reprendre la création de maps avec textures canoniques. **Mise à jour du 25 septembre** : l'utilisateur a choisi une entrée de donjon sud → nord, la méthode rendu généré et les deux livrables (PNG 8 px + Ground). Premier lot : `renders/entree_vapeur_sud_nord_v1/`, biome Steam Cave choisi par l'agent et à confirmer. Les anciens travaux sont conservés. **V2** (`renders/entree_vapeur_sud_nord_v2/`) : eau façon rivière Métano, scintillements Métano, bulles de marais générées ; V1 intacte. Map suivante réalisée : **Entrée Cratère** (`renders/entree_cratere_sud_nord_v1/`, réf. Dark Crater, biome choisi par l'agent et à confirmer). Puis **Entrée Ruine** (`renders/entree_ruine_sud_nord_v1/`, réf. Sealed Ruin) et **Entrée Givre** (`renders/entree_givre_sud_nord_v1/`, réf. Frosty Forest, neige). Puis **Entrée Bristle** (`renders/entree_bristle_sud_nord_v1/`, réf. Mt. Bristle, canyon de sable et torrent). L'utilisateur a demandé de continuer la série de maps.

Reprise du 25 septembre : `.venv` absente du checkout puis recréée (Pillow 12.3, NumPy 2.4, SciPy 1.17). Les tests V16 + sud–nord V3 donnent de nouveau 18/19, avec la même erreur liée à l'objet historique `438b9288`.

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
