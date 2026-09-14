# Grotte cendrée V3 — chemin vers la grotte, bulles et éruptions dans la lave

Cette version corrige la mauvaise interprétation de `cote_cendres_passage` : **le chemin arrive du sud et mène à l’entrée de la grotte**, il ne traverse plus le bord nord. **Aucune flamme ne jaillit du chemin.** Les anciennes versions sont conservées.

## Scène et fichiers

`cendres_grotte/` — 648×504, 64 compositions PNG, 100 ms par frame, boucle de 6,4 secondes.
- `COMPOSITION.png` : phase zéro.
- `ANIMATION_COMPLETE.webp` : scène complète animée.
- `grotte_v3_scene_000.png` à `063.png` : compositions complètes.
- `cendres_grotte.ora` : 12 calques à la phase zéro.
- 4 calques statiques : sol du chemin, rebords, parois de la grotte, profondeur sombre de l’entrée.
- 8 groupes animés de 64 PNG : magma, chaleur de rive, six sites d’éruption indépendants.
- `magma_cle_00.png` à `03.png` : quatre images clés extraites de la planche générée et adaptées au canevas.
- `eruption_pose_00.png` à `07.png` : huit poses générées détourées.
- `SEQUENCE_BULLE_FLAMME.png` : planche de contrôle de l’ordre narratif.
- `masque_approche_grotte.png` : corridor géométrique de contrôle, pas une carte de collisions PMDO.
- ZIP `GROTTE_CENDREE_V3_calques.zip` : scène, calques, séquences et documentation ; bruts et galerie exclus.
- Galerie autonome à la racine : `apercu_cendres_grotte_eruptions_v3.html` (animation, groupes séparés, pause et curseur des 64 phases).

## Éruption : ordre obligatoire

Chaque site suit le même enchaînement, avec un décalage temporel différent :

| Étape | Durée |
|---|---:|
| Petite bulle basse | 400 ms |
| Gonflement | 400 ms |
| Bulle tendue et fissurée | 400 ms |
| Éclatement et projections | 200 ms |
| Jet de flammes naissant | 400 ms |
| Colonne de flammes | 600 ms |
| Retombée | 500 ms |
| Résidu incandescent qui s’efface | 600 ms |
| Repos, calque transparent | 2900 ms |

Le jet ne précède jamais la rupture de la bulle. Les six sites sont placés dans les masses de lave, avec des tailles et offsets distincts. Le rectangle de la plus grande pose est contrôlé hors du terrain solide : aucune flamme n’est simplement cachée/découpée au-dessus du chemin pour simuler un placement correct. Bases fixes, léger mouvement des poses de jet et disparition du résidu. L’aperçu commence à des étapes différentes selon les sites, car c’est une boucle continue, pas un démarrage simultané de tous les événements.

## Ce qui est généré et ce qui est assemblé

1. **Terrain généré sur magenta**, guidé par la grotte et les matériaux de la première côte cendrée, puis détouré et ajusté au canevas. Le même terrain est conservé sur toutes les frames pour éviter que le chemin ou la grotte ne changent de forme.
2. **Quatre images clés de magma générées**, avec un grain guidé par `Dark_Crater_Pit_TDS.png` fourni dans le dépôt. Planche utilisée : `bruts/magma_quatre_phases_affine.png`. La première planche, `magma_quatre_phases.png`, avait de trop grandes plaques sombres : archivée mais non utilisée.
3. Extraction des quadrants, adaptation de l’échelle et extensions miroir. Les déplacements locaux entre poses sont estimés par flot optique ; les intermédiaires sont interpolés puis ramenés à une palette commune et une grille de 2 px. **La lave ne réutilise ni les vagues recolorées ni le bruit procédural de V2.** Ce sont des poses générées et des intercalaires calculés, pas des frames natives récupérées ni 64 générations indépendantes du décor entier.
4. **Huit poses chronologiques d’éruption générées sur magenta**, détourées à échelle commune, avec la même base au sol : le gonflement n’est pas normalisé artificiellement à la hauteur de la flamme.
5. Assemblage des groupes et export des 64 frames complètes. L’ordre de composition et l’état de chaque site à chaque phase figurent dans `manifest.json`.

Les calques de terrain sont des partitions de surfaces visibles. Ils ne constituent pas des objets complets avec toutes les faces cachées reconstruites. L’ORA contient la phase zéro ; les animations sont les séquences PNG indépendantes.

## Vérifications et limites

Reconstruction : `source/cendres_grotte_eruptions_v3/build.py`, puis `verify.py`. Dépendances : Pillow, numpy, scipy et opencv-python-headless.

Contrôles réalisés :
- corridor de 32 px du bord sud jusqu’à l’entrée, entièrement sur le terrain ;
- aucun pixel d’éruption sur le terrain solide dans les 64 phases ;
- ordre bulle → rupture → jet → repos vérifié séparément pour chacun des six sites, y compris dans la boucle ;
- intérieur du chemin identique au terrain statique dans toutes les frames ;
- 64 compositions opaques et distinctes, recomposées exactement depuis les PNG sauvegardés ;
- recomposition ORA exacte ;
- transition finale → initiale du magma comparée aux transitions ordinaires (valeurs dans le manifeste).

**Pas de test PMDO/GPU, de collisions, de dégâts ou de script de zone configurés.** Le contrôle de corridor n’est pas une validation runtime. Animation visuelle, pas une simulation physique de magma. Les ressources de jeu de référence restent soumises aux droits de leurs ayants droit ; les dérivés générés ne sont pas présentés comme des nouveaux sprites officiels.
