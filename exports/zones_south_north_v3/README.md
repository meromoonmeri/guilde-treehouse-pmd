# Correction de direction — sud → nord

Les deux versions horizontales V1 étaient non conformes à la demande précisée. Elles restent dans l’historique ; **ce lot les remplace pour la demande d’entrées sud–nord**, sans prétendre terminer toutes les autres zones.

- **Forêt512×640,9calques** : sol, chemin continu de terre, canopée nord, falaise blanche, grotte, troncs, canopées latérales, pierres, buissons au pied de falaise. Arrivée au bas ; grotte vers256,144 au nord. Sol/terre/falaise proviennent de la référence forestière. Pour avoir des arbres entiers latéraux sans miroir, complément canonique Vast Steppe (Halcyon), avec tronc et canopée séparés. Ce complément n’est pas présenté comme extrait de la seule image de forêt.
- **Roches512×408,8calques** : fond sombre, sol natif, chemin clair, retours ouest/est, cadre du portail, ouverture, masses rocheuses nord. Entrée ouverte vers256,176, arrivée au sud. La référence rockroadpmd est une bande horizontale SANS grotte. Les vrais retours et le portail ouvert viennent donc du panneau droit de `undergroundpmd.png`. Il s’agit d’une entrée souterraine maçonnée native, et non d’une bouche naturelle prétendument présente dans rockroadpmd. Le chemin et les masses nord gardent les matériaux de rockroadpmd.

## Calques et données

PNG `SouthNorthV3_*` avec origine commune0,0, ordre dans le manifeste. Chaque image porte un nom unique pour éviter les collisions de basenames. TSX8px descriptifs ; aucun .rsground ou collision moteur fabriqué ici. Les masques de chemin et lignes rouges sont des outils de contrôle, PAS des données moteur validées.

NPZ `source_sxy[y,x] = [source_id,x_source,y_source]`, ou[-1,-1,-1] pour transparence. Sources et SHA-256 dans `manifest.json`. Tous les pixels visibles RGBA sont prélevés dans ces sources sans recoloration, rotation, miroir ou échelle. Sols et chemins uniquement : assemblage par chevauchement de patches natifs sans mélange de couleurs. Parois et arbres : modules traduits. Les guides générés restent dans le dossier source et ne fournissent aucun pixel final.

Le masque de chemin relie effectivement le bord sud à l’entrée nord, y compris après contrôle de dégagement8px. Ce contrôle ne prouve pas la collision, le warp ou l’occlusion en jeu. Les calques d’entrée sont distincts du cadre et ne sont pas dupliqués en dessous.

## Crédits / réserves

Références utilisateur `forêtglomypmdsky.png`, `rockroadpmd.png`, `undergroundpmd.png` du commit9ec9a081 ; compléments natifs `vast_steppe_layer_3.png` et `vast_steppe_layer_4.png` provenant des références Halcyon déjà conservées (working-copy1522c7a8, provenance dans `source/amp_plains_fleurie_v1/references/`). Artwork PMD/Halcyon et droits de leurs auteurs respectifs ; pas de licence supplémentaire déduite de ce travail. Originaux vérifiés byte-identiques à438b9288.

11tests dédiésPASS. **Art à examiner ; PMDO/Tiled/collisions/warps NOT TESTED.**

Le programme entier reste non terminé. `FULL_PROGRAMME_STATUS.json` reprend les23références :2candidats corrigés sud–nord,1BG réagencé,18références sans nouveau layout répondant encore au suivi actuel,1doublon,1affiche hors map. L’aurore reste une préparation en calques ; l’arène V2 doit être revue selon la direction demandée. Utiliser une référence comme donneur ne termine pas son propre relayout. Bâtiments/annexes retenus, végétation et animations de guilde restent suivis sans déclarer leurs étapes manquantes achevées.
