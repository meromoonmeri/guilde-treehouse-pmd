# V6 — repassage des zones au générateur et prototypes de calques

## Demande du 13 septembre 2026
Repasser les zones assemblées manuellement au générateur pour améliorer leurs défauts en conservant ce qui a été fait ; étudier Spriters Resource et Halcyon pour créer des entrées forêt/grotte avec sol, chemin et décor séparés.

## Réalisé
- Dix rendus V5 pris individuellement comme références par le générateur. Consignes : garder silhouettes, niveaux, ouvertures, cadrage, mer/ciel, palette Métano ; réduire la répétition mécanique des faces et les raccords ; rendre les deux grottes lisibles sans déplacer leurs accès ; conserver le défilé ouvert. Originaux natifs inchangés.
- Dix sorties générées et dix variantes avec le filtre existant `source/cote_v4_abyss/night.py`. Ce ne sont pas des pixels Métano canoniques, ni de nouveaux Ground. La fidélité géométrique pixel à pixel n’est pas garantie ; collisions non transférées.
- Référence **Murky Forest & Armaldo House**, Spriters Resource, asset 59171, planche signée Haalfpack / Noctowl2000 : examinée visuellement, notamment les feuillages séparés du sol. La feuille a été récupérée par la recherche d’images après échec TLS de l’accès HTTP direct. Aucun personnage, maison ou texte de cette feuille collé dans les livraisons.
- **Halcyon / apricorn_grove_entrance** : vrai Ground téléchargé avec ses deux banques, composé à sa grille native de 8 px, 43 × 38 cellules, deux couches, aperçu 344 × 304. Référence de chemin central bordé de végétation. Pins dans `references.json` ; ressources brutes de travail en cache. Les droits des sources restent ceux de leurs auteurs.
- Deux prototypes de quatre calques tirés des propositions déjà générées `04_foret_racines` et `01_antre_encaisse`. Aucune nouvelle génération n’a produit ces calques : détourage par masques explicites, complétion du sol caché par répétition d’un échantillon source. Huit PNG par entrée (quatre jour / quatre nuit), composition, version sans chemin, masques et projet OpenRaster.
- Galerie autonome avec avant/après, ambiance, visibilité des calques et liens PNG complets.

## Limite atteinte — travail non terminé
Le générateur a refusé les appels suivants après dix générations. Les tentatives suivantes n’ont donc produit aucun fichier :
1. **01 Crête du Sillage** : roche devenue trop lisse. Reprendre depuis le rendu natif, en utilisant la matière plus détaillée de la retouche 05 uniquement comme référence de texture.
2. **04 Lagune d’Occident** : relief simplifié ; préserver le haut mur arrière, la rive basse et la haute face sous le plateau avant. Ne pas fermer la lagune ni ajouter de chemin.
3. **10 Défilé de Brume** : roche devenue trop grossière, avec trop gros blocs/contours. Reprendre une stratification plus fine et conserver le passage nord ouvert.
4. **Nouvel atlas forêt**, quatre quadrants alignés : sol seul, chemin isolé, forêt/arrière avec ouverture, buissons de premier plan. Guide disponible `foret_guide.png` ; références Halcyon et TSR ci-jointes. Fond magenta uniforme pour les trois plans détourés, sans texte ni bordures.
5. **Nouvel atlas grotte**, même structure et guide `grotte_guide.png`, roche moussue et véritable bouche sombre ; pas de Métano obligatoire pour cette nouvelle entrée indépendante.

**Priorité au prochain passage : les deux nouveaux atlas en calques, puis les trois reprises.** Les sept autres retouches sont à valider visuellement, pas déclarées parfaites. Les calques actuels sont des prototypes de scène, pas des objets indépendants ou des tilesets finalisés : leurs masques et les surfaces cachées demandent encore une passe artistique. Ne pas prétendre que les générations refusées ont eu lieu.

## Reconstruction et contrôle
- `python source/retouches_v6/layers.py` : PNG, masques, compositions, planche et OpenRaster depuis les deux PNG générés déjà versionnés. Dépendances Pillow, numpy et scipy.
- `python source/retouches_v6/gallery.py` : galerie autonome, aperçus réduits nearest-neighbor encodés WebP sans perte ; les PNG complets restent inchangés.
- `node source/retouches_v6/test_gallery.cjs` : comportement des sélections et calques dans un DOM simulé, pas dans un navigateur réel.
- `prepare.py` : audit visuel Halcyon et guides d’atlas, requiert les trois ressources en cache indiquées dans `references.json` ; construit aussi la planche avant/après.
- `verification.json` : décodage des 50 PNG, recomposition exacte des deux projets ORA et des calques, huit calques nocturnes comparés au filtre, dix références natives et ZIP du mod inchangés.

## Conservation
Le mod Expéditions et ses 40 Ground restent inchangés. Aucun test GPU, import PMDO ou nouvelle collision revendiqué. Les images générées retouchent les apparences et peuvent décaler des détails : l’avant/après est proposé pour validation, pas substitué silencieusement au mod.
