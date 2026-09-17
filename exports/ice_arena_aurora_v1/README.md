# Arène glacée et aurores — scène animée proposée

**Dessin canonique, mouvement nouveau. Ce n’est PAS un cycle animé canonique retrouvé.**

Arène512×720, arrivée au sud vers la zone de combat au centre/nord. Panorama nocturne derrière la bordure de glace ; pas de sol de marche dans le BG. La scène ne comporte pas de grotte ajoutée : c’est l’exemple d’arène avec décor animé demandé après les entrées sud–nord.

## Animation et fichiers

-64étapes de6ticks, boucle6,4secondes.
-`aurora_frames/` :64PNG264×216, déplacement vertical entier par colonne, jusqu’à6px par rapport au dessin d’origine ; pas de RGB interpolé ou recoloré. Un pixel au plus entre deux phases successives, raccord final inclus.
-`star_frames/` :64PNG264×216, formes/couleurs natives, opacité178..255 animée séparément.
-Deux atlas8×8 de2112×1728. Chaque case264×216 est exactement son PNG individuel.
-`static/` :8calques512×720 — ciel, brume native, glace lointaine native, sol, accès sud, bordure nord, glaces latérales/rampe, fissures. Tous restent immobiles.
-`review/scene.gif` et `background.gif` : aperçus animés complets, boucle infinie. Le GIF réduit la palette ; versionsWebP sans perte également fournies.
-`placement_recipe.json` : ordre de dessin, origine BG120,0, dimensions, durées et accès indicatif. C’est une recette d’édition, pas un faux fichier moteur.

Ne pas importer les4captures de contrôle ni les NPZ comme textures de jeu. Les PNG de calques et atlas sont les ressources de montage. Les franges cachées ne constituent pas une reconstruction exhaustive de tous les reliefs pour des déplacements arbitraires de caméra.

## Sources et traçabilité

`aurorepmdsky.png` et `pmdskyicearena.png` originaux inchangés ; hashes dans le manifeste. Décomposition de l’aurore reprise du lotV2, dont la recomposition native exacte était vérifiée. Tous les rubans animés portent leur source_xy par phase dans `provenance/aurora_source_xy.npz`. Géométrie d’arène guidée par génération, puis matériaux prélevés réellement dans les références ; aucun pixel du guide généré livré comme texture canonique.

Recherche enregistrée dans `source/ice_arena_aurora_v1/references/native_animation_search.json` : arbres Git complets inspectés pour Halcyon, DumpAsset et PMDODump. Aucun cycle correspondant à ce panorama n’y a été identifié. `Aurora_Beam_Custom` est une attaque, non un remplacement du décor. Ce résultat limité aux dépôts inspectés ne prouve pas que les phases n’existent nulle part.

Artwork originalPMD et ayants droit respectifs ; aucune licence supplémentaire ou identification officielle de scène certifiée par cette production. Les mouvements proposés sont nouveaux, les images originales ne sont pas attribuées à ce projet.

10tests dédiésPASS. Pas d’import/runtimePMDO, collision, warp ou parallax validés. Le masque de neige représente une surface visuelle, pas des collisions ; seules des vérifications locales du passage central ont été effectuées. Art et animation à examiner. Les autres zones et le programme de guilde ne sont pas déclarés terminés.
