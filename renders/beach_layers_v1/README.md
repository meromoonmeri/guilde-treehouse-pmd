# Beach PMD — calques fidèles et eau animée

Référence : `DSVFS.png`, **702 × 466 px**, conservée sans redimensionnement, modification de palette ou changement de layout. Aucun passage au générateur ni nouvelle texture de décor.

## Voir et télécharger

- `index.html` : atelier autonome, animation, visibilité des calques, pause, phase par phase, zoom natif, comparaison avec la référence et exports PNG.
- `BeachV1_plage_animee.webp` : scène animée sans perte.
- `BeachV1_plage_animee.gif` : aperçu animé.
- `BeachV1_eau_transparente.webp` : eau et écume animées, sans le décor.
- `BeachV1_calques.ora` : document OpenRaster avec neuf calques fixes alignés, phase de référence.
- `BeachV1_pack.zip` : PNG, animations, ORA, viewer, sources de reconstruction et notice.
- À la racine du dépôt : `apercu_beach_calques_v1.html`.

## Les neuf calques

Tous les PNG dans `calques/` mesurent **702 × 466**, à placer en **(0, 0)**. L’ordre est donné par le manifeste et le document ORA.

1. `BeachV1_01_ciel.png` — ciel visible entre les falaises.
2. `BeachV1_02_sable.png` — plage et accès visibles.
3. `BeachV1_03_mer.png` — surface de la mer, sans l’écume extraite.
4. `BeachV1_04_ecume.png` — écume et liserés clairs.
5. `BeachV1_05_falaises_fond.png` — roche de l’arrière-plan.
6. `BeachV1_06_vegetation_fond.png` — palmiers et plantes du fond.
7. `BeachV1_07_vegetation_proche.png` — palmiers et plantes proches.
8. `BeachV1_08_rochers_rivage.png` — rochers des bords et du rivage.
9. `BeachV1_09_ilots.png` — petits îlots rocheux.

Les neuf couches fixes sont disjointes et leur recomposition égale **exactement** la référence. Le détourage utilise les matières, la profondeur, quelques zones de troncs et une réaffectation des petits fragments de contour : aucun RGB original n’est repeint.

**Ce sont des partitions des surfaces visibles d’une image aplatie, pas les vrais calques natifs récupérés du jeu.** Le sol caché sous les palmiers, l’arrière des rochers ou les surfaces occultées ne sont pas reconstruits. En masquant un objet, la transparence correspondante reste visible. L’ORA n’est pas une banque d’objets complets librement déplaçables.

## Animation de l’eau

**64 phases × 50 ms = 3,2 secondes**, deux pistes synchronisées :

- `animation/mer/BeachV1_mer_00.png` à `63.png` ;
- `animation/ecume/BeachV1_ecume_00.png` à `63.png`.

Pour animer, **remplacer** les calques fixes 03 et 04 par les deux PNG de même index. Ne pas laisser l’ancienne écume par-dessus l’animation et ne pas superposer toutes les phases en même temps. Tous les autres calques restent fixes.

La planche déjà présente dans le dépôt, `DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Time _ Darkness - Backgrounds - Beach & Path to Beach.png`, fournit 17 poses de référence du ressac. Les hauteurs de crête mesurées sur ces poses guident le va-et-vient. La pose dont la crête est presque dissipée est ramenée à la hauteur de repos pour ce guide. Les rectangles et mesures sont dans `manifest.json`.

**Mouvement nouveau adapté à l’image, pas cycle officiel PMD Sky retrouvé.** La cadence de 50 ms est choisie pour ce lot. Aucun pixel de la planche de vagues n’est substitué à la texture de la map. Les couleurs viennent exclusivement de `DSVFS.png` ; mouvement par déplacements entiers sans interpolation de couleurs, oscillation locale et progression du ressac guidée par la planche.

La mer sous l’écume est complétée à partir des pixels bleus visibles les plus proches pour permettre son déplacement. Cette petite surface cachée est une reconstruction, pas une extraction authentifiée. La phase 0 de la scène animée est malgré cela exactement identique à l’original.

Les cinq premiers pixels de contact à l’intérieur de la mer restent fixes ; l’amplitude augmente progressivement au large pour éviter les traînées sous les rochers. L’empreinte de l’eau est constante : **le sable n’est pas recouvert puis découvert** dans ce lot. Les bandes bleues et l’écume plus au large ondulent ; aucune roche, plante ou zone sèche ne bouge.

La fonction est périodique (phase 64 = phase 0). Certaines phases adjacentes sont identiques à cause du déplacement entier et des temps de repos. WebP/GIF peuvent fusionner ces poses en augmentant leur durée : leur durée totale reste **3 200 ms**. Les 64 PNG de chaque piste restent disponibles. Une boucle périodique n’est pas une certification artistique du mouvement.

## Import PNG to Tileset — option 8 px

Les originaux **702 × 466** ne sont pas divisibles par 8. Le dossier `import_8px/` contient donc les mêmes calques et les deux séquences avec suffixe `_PAD8`, sur canevas **704 × 472** :

- 2 colonnes transparentes ajoutées à droite ;
- 6 lignes transparentes ajoutées en bas ;
- origine toujours (0, 0), aucun déplacement, étirement ou rééchantillonnage.

Utiliser **8 px** pour cette route PNG to Tileset. Les noms distincts évitent les collisions de basenames avec les exports non rembourrés. Ne pas importer la composition avec ciel/décor comme une texture unique si l’on souhaite garder les pistes séparées.

À 60 ticks/s, 50 ms correspond à **3 ticks par phase**. L’import de PNG n’installe pas automatiquement les séquences : associer explicitement les frames de mer et d’écume et leur cadence dans le moteur. Aucun `.rsground`, collision, warp, import ou rendu PMDO n’est fourni/validé ici.

## Reconstruction et tests

Depuis la racine du dépôt, avec Pillow, NumPy et SciPy :

```sh
.venv/bin/python source/beach_layers_v1/build.py
.venv/bin/python source/beach_layers_v1/verify.py --report
node source/beach_layers_v1/test_viewer.cjs
.venv/bin/python source/beach_layers_v1/package.py
```

Les 10 tests d’assets contrôlent provenance, partition exacte, phase 0, décor invariant sur les 64 phases, dimensions/alpha, palette source, mouvement réel, périodicité, contacts fixes, WebP sans perte, durée GIF/WebP, ORA et copies d’import sans resampling. Voir `verification.json`.

Le test du viewer contrôle les interactions en DOM simulé, pas dans un vrai navigateur. Une installation de Chromium a été tentée mais son téléchargement a échoué (connexion TLS interrompue). Ne pas annoncer un contrôle interactif Chromium réussi. Les fichiers et le serveur d’aperçu sont vérifiés séparément ; **PMDO non testé**.

## Provenance et crédits

Image principale fournie par l’utilisateur : `DSVFS.png`, empreinte dans le manifeste. Planche de référence Beach & Path to Beach : rip crédité **redblueyellow** sur la planche. Les ressources Pokémon Mystery Dungeon et leurs droits restent ceux de leurs auteurs/contributeurs et ayants droit, notamment Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft. Ce travail de séparation et d’animation ne confère pas de licence supplémentaire.
