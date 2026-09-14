# Côte cendrée V2 — passage sud → nord, lave visqueuse et colonnes de flammes

Cette variante répond à la correction de `cote_cendres_lave` : ce n’est plus une côte horizontale avec une grotte en cul-de-sac. Le chemin gris traverse toute la scène du bord sud au bord nord, avec de la lave sur ses deux côtés et huit évents de flammes répartis sans symétrie. L’ancienne version reste intacte.

## Livrables
- `cote_cendres_passage/COMPOSITION.png`, 648×504, phase zéro.
- `ANIMATION_COMPLETE.webp` et 64 compositions PNG, 120 ms par phase, boucle de 7,68 secondes.
- `cote_cendres_passage.ora` : 14 calques à la phase zéro.
- PNG indépendants : lave (64), lueur de rive (64), chacune des huit colonnes (64 par colonne), et quatre calques statiques.
- `colonne_pose_00.png` à `03.png` : poses détourées des sprites de flammes, avec leurs étincelles.
- Galerie autonome à la racine : `apercu_cote_cendres_passage_v2.html`. Composition animée, inspection des groupes/calques, pause et sélection des 64 phases.
- ZIP `CENDRES_PASSAGE_V2_calques.zip` : scène, séquences et documentation, sans les bruts ni la galerie embarquée.

## Calques, dans l’ordre bas → haut
1. Lave visqueuse : surface opaque sous tout le terrain.
2. Lueur au contact des rives.
3. Sol du chemin.
4. Rebords rocheux.
5. Reliefs sombres.
6. Évents volcaniques fixés au sol.
7–14. Huit colonnes de flammes, chacune indépendante, ordonnées par profondeur.

Les trois partitions du terrain sont des surfaces visibles complémentaires, **pas des rochers complets et déplaçables avec un sol caché reconstitué**. L’ORA n’anime pas les séquences : utiliser les PNG fournis pour chaque groupe, tous sur le même canevas.

## Création et animation
La composition précédente sert de référence de matériau. Nouveau chemin généré sur magenta puis détouré, réduit nearest-neighbor, désaturé en gris cendré et réparti en calques. La première génération faisait encore un coude vers l’est : elle est archivée dans `bruts/chemin_magenta.png` et n’est pas utilisée. La correction utilisée est `chemin_magenta_corrige.png`, ouverte au nord et au sud.

Les anciens rubans de vagues recolorés en rouge sont entièrement supprimés. La nouvelle lave utilise un champ de bruit multi-échelle, déformé par des déplacements locaux périodiques : masses épaisses et lentes, remous irréguliers, poches chaudes et plaques sombres. Palette discrète et grille de 2 px, sans vagues parallèles. C’est une évocation visuelle procédurale de viscosité, pas une simulation physique ni un cycle natif PMD récupéré.

Quatre poses de flammes générées sur magenta sont détourées. Les huit colonnes ont des positions, tailles, déphasages et enveloppes de hauteur distincts : elles montent, faiblissent et se tordent sans battre toutes ensemble. Leurs bases restent attachées aux évents. Les positions et offsets sont dans `manifest.json`.

## Vérification et limites
`source/cote_cendres_passage_v2/build.py` reconstruit les assets avec Pillow, numpy et scipy. Recomposition ORA exacte, 64 compositions opaques ; les 64 compositions sauvegardées ont aussi été recomposées depuis les PNG des 14 calques et comparées pixel à pixel. Un intérieur de chemin connecté du nord au sud, à au moins 12 px des bords, a été vérifié géométriquement. La transition dernière → première phase de lave a une variation moyenne comparable aux transitions ordinaires (valeurs dans le manifeste).

Pas de validation dans PMDO, de test GPU, de collisions, de définition de dégâts ou de déclenchement des pièges. Le masque de passage est un contrôle géométrique du terrain, pas une carte de collisions validée. Les flammes sont pour l’instant des effets visuels. Les nouveaux sprites/générations ne sont pas des ressources officielles nouvellement extraites.
