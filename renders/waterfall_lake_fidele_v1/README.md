# Waterfall Lake — édition fidèle en calques, jour/nuit

## Correction de méthode
La première génération étendue a été **écartée à la demande de l’utilisateur** : elle modifiait trop la zone. Elle n’entre dans aucun rendu de ce paquet.

La base est le PNG GBA original fourni :
`Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png`, **456 × 312**. Le lac, ses anneaux de profondeur, les arbres, les herbes et les rochers restent à leur échelle et dans leurs positions originales. Pas de réinterprétation par le générateur, de recoloration diurne globale ou d’agrandissement des pixels de la zone.

## Modifications locales
- Le petit rocher central est retiré dans sa seule silhouette ; le fond d’eau caché est complété depuis les pixels aquatiques voisins. Il ne réapparaît donc pas lorsqu’on masque la plateforme.
- Le disque natif d’Altere Pond/atlas Métano est placé **dans le cercle le plus sombre**, à la place de ce rocher, sur son propre calque.
- Les trois pas japonais natifs sont indépendants. Trois copies supplémentaires prolongent l’accès vers le bord sud : six pierres en tout, dont la dernière continue hors cadre. Les nouvelles pierres restent dans l’eau ; aucune berge originale n’est effacée pour les faire passer.
- Les reflets/eau autour du disque et de chaque pas ont leurs propres calques, avec le cycle natif de huit poses, sans changer la taille des sprites.
- La cascade utilise sa **matière GBA originale**. Son masque reste fixe ; la matière descend de 2 px par pose avec une période verticale de 48 px. Le flux va bien du haut vers le bassin, pas horizontalement.
- L’écume originale est isolée. Trois états sont reconstruits avec un gonflement local de ±1 px et une zone de contact fixe, au point d’impact de la référence.

Le fichier d’origine est statique : l’animation de sa cascade et celle de son écume sont **reconstruites**, pas présentées comme des animations GBA récupérées. Le cycle de huit poses d’Altere/Métano, lui, provient bien des ressources natives déjà archivées.

## Cadrage et prolongement
Deux vues sont fournies :
- **Cadrage original 456 × 312**, pour voir l’édition sans extension.
- **Cadrage périphérique 504 × 360**, avec 24 px supplémentaires de chaque côté, 16 en haut et 32 en bas. L’original occupe exactement le rectangle (24,16)–(480,328).

Ce prolongement est volontairement limité : il utilise les pixels des bords réfléchis, sans redessiner le lac. Il peut produire des symétries locales dans les masses végétales ; ce n’est pas une nouvelle périphérie entièrement dessinée ou une extension de terrain validée dans le jeu. L’option de cadrage original reste disponible dans la galerie.

## 22 calques par ambiance
1. Fond d’eau et profondeurs originales.
2. Roche de la cascade.
3. Herbe et berges.
4. Végétation arrière.
5. Canopée avant gauche.
6. Canopée avant droite.
7. Cascade descendante.
8. Écume d’impact.
9–15. Sept calques de reflets natifs : disque et six pas.
16–22. Disque et six pierres d’accès, indépendants.

Tous les calques de scène sont alignés à **504 × 360**. La galerie permet de sélectionner chaque couche. Les terrains sont des partitions des pixels visibles ; les faces cachées des arbres/rochers ne sont pas inventées. Le fond d’eau sous ces terrains est complété pour permettre l’assemblage, sans prétendre récupérer un sol caché original.

## Jour et nuit
Le jour conserve les couleurs originales, hors sprites ajoutés et zones animées explicitement documentées. La nuit utilise le **même filtre Abyss existant que Northern**, appliqué à chaque calque et chaque phase. Ce n’est pas un asset nocturne GBA natif. Aucun ciel, lune ou étoile n’est ajouté à ce point de vue au-dessus du lac.

24 poses, 10 frames de jeu par pose, boucle de **4 secondes** : chute 24 poses ; écume 3 ; reflets 8. Le WebP arrondit les horodatages cumulés à la milliseconde sans dérive de la durée totale.

## Ouvrir
- `../../apercu_waterfall_lake_fidele_v1.html` : jour/nuit, calques, cadrage original/étendu et comparaison avec la référence.
- `jour/COMPOSITION.png`, `nuit/COMPOSITION.png` : scènes avec bordures périphériques.
- `jour/COMPOSITION_CADRE_ORIGINAL.png`, `nuit/COMPOSITION_CADRE_ORIGINAL.png` : cadrages 456 × 312.
- `jour/ANIMATION.webp`, `nuit/ANIMATION.webp` : boucles étendues.
- `jour/ANIMATION_CADRE_ORIGINAL.webp`, `nuit/ANIMATION_CADRE_ORIGINAL.webp` : boucles dans le cadrage original.
- `jour/waterfall_lake_jour.ora`, `nuit/waterfall_lake_nuit.ora` : 22 calques à la phase initiale.
- `jour/lake_jour_*.png`, `nuit/lake_nuit_*.png` : calques et compositions, noms distincts entre ambiances.
- `COMPARAISON_NATIVE.png` : référence et édition dans le même cadrage/à la même échelle.
- `MASQUE_*.png` : origine, extension et zones de modification autorisées.
- `verification.json` : contrôles de fidélité et d’animation.
- `waterfall_lake_fidele_v1.zip` : paquet avec scripts et dépendances nécessaires.

## Fidélité vérifiée et limites
Dans le cadrage original, **93,8 % des pixels sont identiques à la référence au premier état diurne**. Le masque conservateur garantit 129 065 pixels inchangés sur 142 272 dans chaque état ; les changements sont limités au remplacement central, aux nouveaux pas/reflets et à la chute/écume. Les anneaux du lac ne sont pas redessinés.

Le vérificateur contrôle les 24 états de chaque ambiance, les recompositions opaques, la fidélité hors zones autorisées, le filtre nocturne exact par calque, les cycles 3/8, le mouvement vertical descendant et son raccord de boucle, le contact chute/écume, les cadrages et les ORA. Cela ne constitue **pas** une validation PMDO, de collisions, de déplacement sur les pierres ou de gameplay.

Les ressources PMD et Halcyon réutilisées restent soumises aux droits de leurs ayants droit. L’image originale et les anciens livrables ne sont pas modifiés.

Reconstruction depuis la racine avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/waterfall_lake_fidele_v1/build.py
.venv/bin/python source/waterfall_lake_fidele_v1/verify.py
.venv/bin/python source/waterfall_lake_fidele_v1/package.py
```
