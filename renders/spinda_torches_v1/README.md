# Torches murales Spinda — 8 orientations / 3 calques / palette cycling

## Contenu
- **8 supports réellement générés**, orientations du mur N, NE, E, SE, S, SO, O, NO. Les lettres des fichiers suivent N/NE/E/SE/S/SW/W/NW. Face, profils, trois-quarts et retours de premier plan. Aucune rotation ou symétrie automatique de l’image principale. Généré ≠ natif.
- 9 sorties du générateur archivées sans perte ; le premier essai N était trop tourné et a été remplacé par `N_front`.
- **Flamme : 4 vraies poses Halcyon/Ledian**, 32×40, 100ms/pose, période400ms, identiques aux PNG natifs déjà audités. Ni recoloration, ni resampling, ni miroir ; la flamme reste verticale dans toutes les orientations.
- **Lumière : 16 frames à100ms**, boucle1600ms, 8 distributions spatiales orientées. Création procédurale de lumière, pas animation native. La carte d’indices ne bouge jamais : les 15 anneaux de 16 couleurs tournent réellement dans la palette. Pas un simple halo déplacé ni une image fixe présentée comme animée. Alpha fixe ≤30/255 ; luminosité ambrée subtile.

## Calques et ancrages
Ordre conseillé : pièce → `lumiere` → `support` → `flamme`. Les supports sont des PNG64×88 avec variantes jour/nuit. L’ancrage de la coupelle est [32,44]. La flamme32×40 a pour ancrage [16,40]. Le halo96×96 a pour ancrage [48,48]. Pour un point d’installation [x,y], placer chaque calque en [x−ancreX,y−ancreY].

Toutes les dimensions et cellules des strips sont divisibles par8 : Ground PMDO. Les cadres transparents sont volontairement plus grands que le dessin. Le support seul mesure au plus40×32 visibles. Les supports sont normalisés nearest, proportions conservées ; aucun pixel natif de flamme transformé.

`manifest.json` fournit chemins, orientations, ancrages, timing et ordre des calques. `palette_cycles.json` contient la palette RGBA de base et les cycles permettant de reconstruire les16palettes. `indices/` contient les cartes d’indices L8 ; `lumiere/` **dans le ZIP** contient les véritables PNG indexés animés (même matrice, palettes différentes). `tilesheets/` contient les bandes **RGBA** pour les importeurs sans palette dynamique. Une bande de lumière =16cellules96×96 ; support =8cellules64×88 ; flamme =4cellules32×40. Lire de gauche à droite.

## Atelier et exports
Ouvrir `index.html` par HTTP. Pause, frame suivante, curseur16frames, trois calques indépendants, intensité du halo, huit orientations et placement sur grille8px. Quatre installations initiales sont des **exemples amovibles**. Les trois boutons PNG exportent séparément les supports, les flammes de la frame courante et la lumière de cette frame, en600×448 transparent. Le JSON exporte les positions et phases ; les frames individuelles et bandes sont toutes dans le ZIP.

Le halo des exports de pièce est borné à la silhouette du café. Les sprites de bibliothèque restent libres pour l’éditeur. L’éclairage est une superposition alpha ambrée, pas un moteur de raytracing ni une ombre dynamique avec obstacles. Aucun corps/flamme/lumière cuit dans la map. Le fond de démonstration est dérivé de la nuit V8 **sans son halo ambiant statique**. Les maps V8 et leurs exports ne sont pas réécrits.

Les palettes cycliques concernent la **lumière**, pas les pixels natifs de flamme. Cette séparation permet la fidélité des quatre poses tout en répondant au cycle lumineux multiframe. L’image JPG est une planche de consultation, pas une animation ; l’atelier joue les vraies frames.

## Provenance et limites
Flammes : `Palikadude/Halcyon`, commit`da6c2130d641507447e6386a5e47a296e8cb4c71`, banque `Ledian_Dojo_Animated.tile` ; provenance complète et SHA256 dans `flammes_provenance.json`/manifest. Sources originales générées : `source/spinda_torches_v1/raws/archive.json`, lecteur/restauration Git dans `archive.py`. Garder l’historique complet.

Scripts : `.venv/bin/python source/spinda_torches_v1/build.py`, `verify.py`, `python source/spinda_torches_v1/serve.py --port 8009`. Vérifications de palette/index/frames, natifs et exports ; **pas de validation PMDO ou d’approbation artistique utilisateur**. Les meubles, rubans et nouvelles fenêtres en attente de V8 restent en attente : cette livraison traite les torches demandées.

Stockage : les128 PNG indexés sont conservés dans le ZIP autonome, sans doublon sur disque dans le dépôt. L’atelier lit les bandes RGBA équivalentes. Après extraction du ZIP, les PNG indexés sont directement accessibles dans `lumiere/`. Le fond de démonstration WebP est lossless.

`Torche_N_animation.webp` : aperçu animé lossless d’une orientation,16frames à100ms en boucle. Image de consultation composite agrandie2× ; les vrais calques à1× se trouvent dans les sous-dossiers du pack.

## Affichage direct sans HTML

- [Les8orientations en WebP animé](apercus_directs/Torches_8_angles_animees.webp) :16frames lossless,100ms chacune, boucle1,6s.
- [Les8orientations en PNG](apercus_directs/Torches_8_angles.png) : même planche, première frame,832×448.

Ces vues sont agrandies2× nearest sur fond sombre pour consultation ; les calques d’import transparents restent dans le ZIP existant. Reconstruction : `direct_previews.py`. Les9ressources lourdes du précédent atelier (fond +8bandes lumière) sont désormais lues directement dans ce même ZIP, sans duplication dans le dépôt ; leurs octets sont conservés à l’identique et le serveur8009 maintient les anciennes URL. Le ZIP extrait reste autonome avec tous ses fichiers. Les nouvelles vues directes sont des fichiers séparés du pack, pas des pages HTML.
