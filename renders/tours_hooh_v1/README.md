# Tour Carillon et Tour Cendrée — deux ensembles séparés

Chaque tour possède son **entrée extérieure** et sa **salle de boss** en640×480, avec exports jour/nuit. Les salles de boss sont des adaptations libres : panorama ouvert sur des montagnes crépusculaires, grandes poutres bordeaux, parois brisées et panneaux vitrés à motifs japonais. Ne pas les présenter comme les cartes canoniques de Rosalia.

## Références Internet réellement consultées
- https://pokemon.fandom.com/wiki/Bell_Tower — aperçu HGSS du toit et de la structure.
- https://strategywiki.org/wiki/Pok%C3%A9mon_Gold_and_Silver/Burned_Tower — aperçu du plancher/piliers du1F G/S.
- https://archives.bulbagarden.net/wiki/File:Bell_Tower_HGSS.png
- https://archives.bulbagarden.net/wiki/File:Bell_Tower_Summit_HGSS.png
- https://archives.bulbagarden.net/wiki/File:Burned_Tower_1F_HGSS.png

Les pages d’archives ont été inspectées ; le téléchargement direct de leurs PNG pleine résolution a échoué en TLS. Les deux images effectivement fournies au générateur sont les aperçus de recherche conservés dans `source/tours_saisons_v1/references/`. Aucune construction Minecraft n’a servi de référence.

La Tour Carillon conserve le langage pagode, tuiles bleu-noir, bois rouge et ornements d’oiseau. La Tour Cendrée est basse et brûlée à l’entrée ; sa salle haute délabrée est une invention pour la demande, pas une affirmation sur le lieu canonique. Les vitraux à motifs floraux/géométriques japonais sont également une création.

## Calques
Entrées :9calques — sol, parvis/chemin, façade, porte/escalier, poutres, toit, végétation arrière et avant gauche/droite. Sol caché reconstruit depuis les pixels voisins ; recomposition exacte du brut final réduit.

Boss : scène séparée en ciel,3massifs lointains,3plans de nuages, plancher, murs, vitraux, toiture brisée et **4poutres, deux par côté**. Carillon possède aussi une petite extension indépendante de planches assorties au sud pour corriger une ouverture dans le dessin généré. Les découpes d’architecture sont des masques de production sur le dessin, pas un kit de charpente modulaire natif.

La géométrie et les motifs architecturaux viennent du générateur, détourés du magenta. Le ciel et les silhouettes de montagnes sont dessinés par le script, pas extraits d’un jeu. Les nuages sont des sprites générés : seuls les deux groupes détachés centraux de chaque rangée sont retenus, pour ne pas réutiliser les bords coupés du brut.

## Boucles et parallaxe
- Période commune : **64secondes /640pixels**.
-256états de250ms par WebP, sans image finale dupliquée artificiellement.
- Nuages lavande : +10px/s ; rose : −10px/s ; ambre : +20px/s.
- Les sprites passent d’un bord à l’autre par translation modulo640 : wrap horizontal exact. L’ambre accomplit deux tours pendant la période commune.
- Les PNG transparents de départ et les trois WebP indépendants sont dans `sprites/` et `nuages_animes/<jour|nuit>/`.
- `BOUCLE_64S.webp` dans chaque salle est une **boucle complète**, pas un extrait de2secondes. La galerie calcule le même mouvement à l’horloge du navigateur, en pixels entiers.
- Les boucles indépendantes sont mutualisées entre les deux tours : pas deux copies identiques dans chaque dossier.

Le ciel « jour » des salles de boss est volontairement **crépusculaire**, conformément à la demande. La variante nuit applique le filtre exact Abyss à chaque calque. Les entrées ont leur rendu diurne propre et leur nuit.

## Vérifications
`verification.json` :14compositions et14ORA (avec les forêts),1024images de boss décodées et recomposées,3072contrôles de périodicité,6boucles indépendantes vérifiées à64s, filtre nuit exact par calque. Les4poutres existent dans chaque salle ; le masque de plancher relie le bas au centre.

**Aucun test PMDO, collisions ni gameplay exécuté.** La connectivité d’un masque d’image ne certifie pas la navigation moteur. Import éventuel des PNG Ground en8px en gardant les dimensions640×480. Les noms de calques sont uniques par scène/mode. Le défilement nécessite une intégration au moteur ; les JSON/WebP ne l’installent pas automatiquement.

Scripts : `source/tours_hooh_v1/build.py`, `source/tours_saisons_v1/{common,verify,package}.py`. `optimize.py` régénère les mêmes boucles depuis les calques statiques, en compression sans perte. Le ZIP compact conserve les calques PNG, boucles de nuages et galerie calculée ; les ORA, bruts et grands WebP composés restent dans le dépôt pour éviter de dupliquer toutes les images dans l’archive.
