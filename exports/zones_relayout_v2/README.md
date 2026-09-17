# Glace et panoramas — lot02

Galerie autonome : `apercu_zones_relayout_v2.html` à la racine. **Une arène réagencée, un BG redisposé, un BG préparé en calques — pas trois maps jouables.** Images fixes, aucun cycle inventé depuis les références.

## Arène de glace —768×480,6layers

Ciel, neige au sol, aiguilles lointaines visibles, paroi arrière, crête de premier plan, fissures. Modules de paroi192px conservés à leur hauteur, sans miroir ni réduction ; premier plan reculé72px. L’aplat bleu pâle de neige vient réellement du pixel100,248 de la référence, dont le sol est largement uni. Groupes de fissures natifs déplacés. Aucun boulder inventé pour remplir le guide généré.

Les aiguilles lointaines sont isolées par régions connectées à leur teinte native111,159,231 ; pas par sélection de toutes les ombres bleues des faces proches. Les parties cachées du relief ne sont pas reconstruites : les deux plans arrière restent liés tant que les occultations ne sont pas complétées. Pas de collision/warp/occlusion de personnages validés.

## Mer nocturne —456×240,8layers

Ciel avec halo natif, étoiles, lune, nuages hauts, nuages d’horizon, mer, reflet, récif. Nuage gauche déplacé+16,-8 ; nuage haut droit+64,+8. **Lune, halo, reflet et récif restent aux positions d’origine**. Diamètre de lune inchangé. Le déplacement du récif a été abandonné : l’image ne donne pas le ciel/nuage caché derrière lui.

Derrière les nuages déplacés, le ciel est reconstruit par prélèvement de pixels dans les lignes hautes dégagées du halo natif, à distance correspondante du centre lunaire. Aucun fondu, couleur générée ou interpolation ; ces pixels clonés ne sont cependant **pas une authentification des zones cachées**. Les autres zones couvertes du ciel utilisent des donneurs natifs voisins. Le reflet garde ses pixels et sa position, pas de fausse animation d’océan ou de nuage.

## Aurore —264×216,5layers

Ciel sombre, étoiles, rubans d’aurore, brume lointaine, glace au premier plan. **Composition native intégralement inchangée**, recomposition pixel-exacte vérifiée. C’est une préparation de BG, pas un relayout achevé. Masques des pointes tracés contre l’original ; la brume cachée derrière elles n’est pas reconstruite. Aucun sol praticable fourni.

## Import et provenance

Seuls les PNG `ZonesV2_*` sont les calques de montage, dans l’ordre du manifeste et avec une origine commune0,0 pour chaque asset. TSX8px descriptifs inclus, non testés dans Tiled. `*_source.npz` : tableau source_xy[y,x] donnant le pixel source de chaque pixel visible, ou[-1,-1] pour transparence. Tous les RGBA visibles correspondent exactement à leurs donneurs. Fichiers de comparaison/NPZ/rapports à garder hors ressources de terrain du moteur.

Références utilisateur du commit9ec9a081 : `pmdskyicearena.png`, `bgnightbackgroundpmdskyda.png`, `aurorepmdsky.png`. Originaux byte-identiques. Artwork d’origine PMD et ayants droit respectifs ; aucune licence supplémentaire ou identité officielle de scène certifiée ici. Le guide généré concerne seulement l’arène ; aucun de ses pixels ne figure dans les exports.

8tests dédiésPASS ;104tests de régressionPASS avec les lots précédents. **Art non approuvé, PMDO/Tiled NOT TESTED**. Les autres zones restent ouvertes ; `production_progress.json` distingue3candidats terrain cumulés,1BG réagencé et1BG seulement préparé. L’aurore reste dans la liste des layouts à faire.
