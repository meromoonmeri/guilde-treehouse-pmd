# Spring translucide & chemins Apple Woods — V2

## Contenu
- Luminous Spring : 600 × 600, 5 familles de calques, 78 phases / 6,5 s ; spectre à couleurs fixes, alpha maximal 89/255 (34,9 %). Eau et halo natifs indépendants. Le fond auparavant opaque est remplacé uniquement dans la colonne (x 275–324, y 0–200) par une reconstruction à partir du décor adjacent et du côté opposé du bassin. Ce ne sont pas des pixels cachés récupérés.
- Tour Carillon et Tour Cendrée : deux entrées distinctes de 640 × 480, 32 calques chacune. Architecture issue de tours_hooh_v1, conservée pixel pour pixel dans les masques fournis ; suppression des restes de fond dans les silhouettes. Arbres individuels, sol, chemin, feuilles et architecture séparés.
- Jour et nuit : formule Abyss exacte appliquée à chaque calque, et non approximation sur la composition aplatie.

## Provenance et adaptations
La référence locale Apple_Woods_entrance_TDS.png (552 × 408) fournit directement les échantillons 24 × 24 d’herbe et de chemin, ainsi que deux arbres extraits à leur échelle native. Les coordonnées sont dans manifest.json. Extraction des arbres par masque feuillage/tronc : ce ne sont pas des sprites détourés officiels. Recoloration du feuillage en or et orange, placement recomposé ; feuilles tombées dessinées pour cette version. Le sol et le chemin ne sont pas recolorés. Les textures natives répétées ne constituent pas un nouveau DTEF/autotile.
L’architecture est la création/adaptation précédente, pas une extraction native Apple Woods. Les salles de boss, boucles de nuages, anciennes entrées et autres livraisons ne sont pas modifiées.

## Utilisation
Ouvrir apercu_spring_applewoods_v2.html (autonome, hors ligne), choisir le lieu et le mode, puis régler les calques. L’opacité 100 % du curseur conserve l’alpha des PNG, elle ne rend pas le spectre opaque.
Chaque répertoire jour/nuit contient les PNG alignés, la composition et un OpenRaster (.ora). Spring inclut aussi son animation WebP. Les ORA de Spring montrent la phase 39 ; les autres phases sont des PNG séparés.
Échelles de travail non validées en jeu : grille habituelle du projet 8 px ; échantillons de matériau 24 px, pas des fichiers DTEF. Utiliser les noms préfixés cs2_* pour les calques ; COMPOSITION et les masques sont des fichiers de contrôle, pas des ressources à importer globalement.

## Contrôles et limites
verification_build.json et verification_independante.json : recomposition PNG/ORA, formule nuit, géométrie des arbres, échantillons natifs, préservation de l’architecture dans les masques, 78 phases de Spring et invariance hors colonne. Connexité du masque du chemin en image seulement.
Aucun test d’exécution, d’import, de collisions ou de navigation PMDO. Les décors restent à intégrer et à tester dans le moteur.

## Reproduction
Depuis la racine : .venv/bin/python source/corrections_spring_tours_v2/build.py ; puis verify.py ; puis package.py. Dépendances : Pillow, NumPy, SciPy. Les sources et anciennes livraisons sont conservées dans le dépôt.
