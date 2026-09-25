# Thunder Meadow V4 — sommet (texture canonique, orage en spirale)

Tous les pixels viennent de la carte de `5394.png`, sans générateur. Par rapport à la référence :
- l'arbre est retiré et son emplacement comblé avec le sol natif (même méthode qu'en V1) ;
- les gros rochers sont déplacés comme en V1.

Le chemin monte du sud vers le nord : il part de la bande claire centrale au bord bas et suit la fissure canonique jusqu'au bord haut.

Calques :
- `00_nuages` : palette flash canonique sur 6 niveaux.
- `01_spirale` : orage en spirale, 48 frames × 83 ms (4 s par tour), boucle exacte vérifiée. Il est construit à partir de la bande canonique de nuages, en indices de palette, projetée en coordonnées polaires tordues. Pixels 2×2, bord tramé. Il reçoit le même flash que les nuages. Deux versions : `spirale/*_indexe.png` (index 0-7, 255 = transparent) et RGBA.
- `02_eclairs` : frames canoniques placées dans le ciel, là où elles sont le plus visibles, près du centre de la spirale.
- `03_terrain`
- `04_details` : rochers.

La spirale est un effet construit (projection polaire), pas une animation GBA d'origine. Collisions indicatives, rien n'a été testé en jeu.
