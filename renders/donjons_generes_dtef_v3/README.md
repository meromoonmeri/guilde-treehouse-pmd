# Donjons V3 — retouches générées légères, export DTEF natif

Les dix biomes de V2 sont maintenant repassés au générateur, par paires de matières. Les **5bruts** de `bruts/` contiennent chacun deux biomes : colonne gauche matière de mur, droite matière de sol. Chaque génération a reçu les gabarits composés des deux donjons natifs correspondants.

## Intégration contrôlée, comme Sakura
Les textures générées deviennent des donneurs96×96, puis des patchs24×24 à positions déterministes variables. Elles sont intégrées seulement aux intérieurs opaques des tuiles statiques : mélange maximal30% pour les murs et42% pour les sols, atténué vers les bords. Les échantillons sont dans `matieres/`.

**Conservés depuis V2 :** disposition exacte DTEF, bordure de4px de chaque cellule, alpha, cases vides, variantes disponibles, bloc Secondary complet et toutes les couches animées avec leurs durées natives. Les textures du sol varient au lieu de répéter le même échantillon à chaque cellule.

Les matières finales sont des **adaptations de ressources natives avec apport généré**, pas des sprites canoniques intacts. La variante0 reçoit aussi la retouche statique dans cette V3. Aucun remplacement par une simple image de salle ; ce sont bien des feuilles DTEF.

## Import
`RAW/TileDtef/d3_<biome>_<jour|nuit>/tileset_0.png`, variantes1/2, et `tileset_<v>_frame<couche>_<index>.<duree>.png`.

Feuilles432×192 : Wall / Secondary / Floor,6×8cases par bloc, tuiles24px. Même `FieldDtefMapping` audité pour Sakura. Les durées sont des frames de jeu, pas des millisecondes.

Sur une **copie de test** de PMDO, après extraction du ZIP :
```
./PMDO -raw "/chemin/vers/le/pack/RAW/" -convert autotile
```
Ce lot utilise l’import **DTEF24px**, pas un découpage PNG générique8px. Ne pas aplatir les dossiers ni renommer `tileset_0.png`. Les préfixes `d3_` évitent de remplacer les anciens assets.

Commande documentée depuis le code de l’importeur ; **non exécutée ici**. Collisions, génération d’étages et spawns ne sont pas configurés.

## Sources et animation
Bases : Treeshroud Forest1 (Relic Forest dans Halcyon), Southern Jungle, Murky Forest, Southern Cavern1, Crystal Cave1, Vast Ice Mountain, Dark Crater, Quicksand Cave, Sealed Ruin, Steam Cave. Pins/provenance dans V2 `source/donjons_dtef_v2/references/`.

788PNG DTEF jour/nuit, dont728feuilles de couches animées inchangées depuis V2. Nuit exacte Abyss. Les WebP de démonstration sont des **extraits répétés de2secondes**, pas des boucles complètes ; la galerie DTEF déroule les cadences intégrales.

Galerie technique : `apercu_donjons_generes_dtef_v3.html` à la racine du dépôt, `apercu_dtef.html` dans le ZIP. Galerie commune : `apercu_jungle_donjons_v3.html`.

`verification_finale.json` regroupe les contrôles du lot. **Pas de test PMDO/GPU.** La conformité structurelle ne garantit pas automatiquement tous les raccords artistiques en jeu.

Scripts : `source/donjons_generes_dtef_v3/build.py` et `source/livraison_jungle_dtef_v3/`. Reconstruction depuis le dépôt avec Pillow/NumPy/SciPy et les dépendances V2. Le ZIP compact contient les exports, galeries et scripts ; les bruts restent dans le dépôt. Les droits des ressources natives restent ceux de leurs auteurs/contributeurs et ayants droit.
