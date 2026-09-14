# Grotte V5 — fissures animées et éruptions de la même matière

Ajout non destructif à V4 (`b878f8b`). Le raccord rocheux corrigé, le chemin vers la grotte et les calques de terrain sont conservés. Les bulles et jets sont remplacés par de nouvelles formes ; les anciennes versions restent disponibles.

## Fissures dans la roche

Des fissures ramifiées, à largeur et contour irréguliers, parcourent les parois et les rebords du passage. Elles partent du contact avec la lave. Le centre du chemin, avec une marge supplémentaire de 10 px autour du corridor de contrôle V4, et la profondeur de la grotte sont exclus.

Deux calques distincts :
- `08_gorges_fissures` : creux sombres fixes dans la roche ;
- **`09_magma_fissures` : magma animé dans ces fissures, 64 PNG transparents indépendants.**

`MASQUE_FISSURES.png` fixe leur géométrie ; `INDICES_FISSURES.png` encode les classes thermiques et la phase. Les phases progressent le long des branches depuis leurs racines au contact de la lave. Les fissures utilisent les mêmes tables de palette thermique que la surface, avec des bords plus sombres et un cœur plus incandescent. Aucun élargissement/clignotement arbitraire du masque.

## Bulles et colonnes : même texture, pas seulement mêmes couleurs

Une nouvelle planche de huit poses a été générée en prenant le magma V4 comme référence : soulèvement bas, gonflement, dôme tendu, rupture, jet naissant, colonne filamenteuse, retombée, résidu. Les silhouettes remplacent les anciens symboles de flammes et les bulles plus lisses.

Pour chaque frame, **la texture du magma réellement affichée à cet instant, chauffe locale comprise, est prélevée et projetée sur chaque silhouette** :
- compression sur les dômes et étirement vertical dans les jets ;
- relief visuel borné dans la même gamme de 16 couleurs ;
- coordonnées de texture sans décalage au pied : les pixels de contact correspondent exactement au magma sous-jacent ;
- pas de contour noir rapporté ni de palette de flamme étrangère au matériau.

C’est une projection de texture déformée avec relief, pas une affirmation que chaque pixel du volume surélevé reste identique à celui du plan horizontal. La base, elle, est contrôlée pixel à pixel. Les six sites et leur ordre bulle → fissuration → éclatement → jet → retombée → repos sont conservés. Ils restent exclusivement dans la lave, pas sur le chemin.

La planche générée dépasse la séparation mathématique entre ses deux rangées : l’extraction suit le véritable espace vide à 38 % de sa hauteur afin de ne pas incorporer la pointe d’un jet sous une bulle. L’échelle commune et les bases des poses sont préservées.

## Livrables

Scène : `cendres_fissures_matiere/`, 648×504, 64 phases à 100 ms, boucle 6,4 s.
- `COMPOSITION.png` et `ANIMATION_COMPLETE.webp`.
- 64 compositions complètes PNG.
- **16 calques** : 7 statiques et 9 groupes animés de 64 PNG.
- `cendres_fissures_matiere.ora`, avec la phase zéro de chaque groupe. Les séquences PNG fournissent les animations ; l’ORA ne les lit pas comme une timeline.
- `PALETTES_064.json`, indices et masques de contrôle.
- `pose_generee_00.png` à `07.png` : poses détourées de la nouvelle génération.
- `pose_matiere_00.png` à `07.png` et `SEQUENCE_MATIERE_COMMUNE.png` : exemples avec la texture commune appliquée.
- ZIP `FISSURES_MATIERE_V5_calques.zip` : scène, calques, poses, palettes, contrôles et documentation, hors brut généré et galerie.
- Galerie autonome à la racine : `apercu_cendres_fissures_matiere_v5.html`, avec sélection du magma des fissures, des éruptions et des autres calques, pause et curseur des phases.

Ordre d’assemblage : magma et chauffe locale → calques de terrain et contact V4 → creux des fissures → magma des fissures → six éruptions. Détails dans `manifest.json`. Les calques de terrain sont des surfaces visibles, pas des objets complets avec leurs faces cachées reconstituées.

## Vérifications

Reconstruction : `source/cendres_fissures_matiere_v5/build.py`, puis `verify.py`. Dépendances : Pillow, numpy, scipy ; les assets V4 sont nécessaires.

Contrôles réalisés :
- magma indexé V4 conservé octet pour octet dans ses 64 PNG ;
- calques de terrain V4 inchangés ;
- masque des fissures fixe, uniquement sur la roche et hors corridor protégé ;
- 64 images distinctes de magma dans les fissures, conformes aux tables de palette partagées ;
- pieds des éruptions raccordés aux pixels du magma de la même frame ;
- aucun pixel d’éruption sur le terrain ;
- corridor protégé inchangé dans les 64 compositions ;
- ordre causal des six séquences et transparence au repos ;
- 64 compositions opaques et distinctes, recomposition exacte depuis les PNG sauvegardés et l’ORA.

Pas de test runtime PMDO/GPU, de collisions, de dégâts ou de scripts d’éruption configurés. Les fissures sont visuelles. La chauffe et le palette cycling évoquent un comportement cohérent mais ne constituent pas une simulation physique. Les nouvelles générations et adaptations ne sont pas des sprites officiels récupérés.
