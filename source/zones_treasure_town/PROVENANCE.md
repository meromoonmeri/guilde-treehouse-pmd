# Version courante

Voir **DA_GUILDE_CAP.md** : harmonisation au générateur, deux plans de nuages en wrap, mer de nuages séparée et un calque par cascade. Les notes ci-dessous décrivent la base de texture et le moteur de palettes, toujours utilisés.

# Plans de zones et texture Treasure Town

## Sources graphiques retenues

Les plans de terrain et de relief, les guides de layouts, une banque de végétation, une banque de cascades/rides et le matériau d’eau sont conservés dans ce dossier. Ils ont été ajoutés dans le commit `8e65ad60049108ac2de1e6c5892faaa8b4cfe749`, avec une référence de texture de Treasure Town.

Les sources ont été inspectées avant assemblage : elles emploient des strates ocres et de petits fragments pierreux, et non les grands blocs gris de l’itération rejetée. Elles sont normalisées, détourées et composées selon les positions de `layouts.json`. Les guides servent aux dispositions, pas de dessin final. La référence de Treasure Town vient du dépôt Minemaker0430/ExplorersOfSkyOrigins au commit `b8c0de576606c5a24802158462d5d1d7e561f72d` ; elle reste une référence graphique tierce, pas une création originale de ce pack.

Le commit `df4bca7de098f0b4e87a49ad2fae32878495d5d4` a ajouté la préparation et les premières cartes de cycling. La livraison courante finalise leur emploi dans les zones, sépare le fond d’eau, les rubans de cascades et l’écume, et ajoute les exports indexés ainsi que le rendu navigateur.

## Plans construits par le pipeline

`prepare_zones_tt.py` place séparément :

- les ciels et astres de la banque déjà retenue ;
- les sprites de nuages ;
- le matériau d’eau ;
- les arrière-plans rocheux/boisés générés ;
- les rubans de cascade, leurs pieds d’écume et les rides de surface ;
- les terrains avec leurs chemins ;
- les sprites de végétation, dont le pied doit se trouver sur de l’herbe.

La préparation ne repart pas d’une capture intégrale dont elle retire les bâtiments. Les références de composition servent seulement d’inspiration à de nouveaux layouts. Les deux anciennes falaises et le rêve de personnalité ne sont pas redessinés par ce pipeline.

## Palette cycling réel

`palette_cycle.py` produit une carte d’indices fixe, une palette de base et une liste de palettes :

- l’indice 0 est transparent ;
- les indices 1 à 32 sont fixes ;
- les indices 33 à 40 sont réservés au cycling.

Pour l’eau, le fond quantifié est un calque distinct. Seuls les détails lumineux désignés passent sur le plan cyclique. Pour les cascades, les indices suivent des bandes verticales et les différences de lumière de la matière générée. Pour l’écume, la sélection suit les valeurs lumineuses du sprite afin de ne pas transformer les rides en grands disques rayés. Aucune translation ne sert à simuler ces trois cycles.

Le cycling possède une palette de jour et une palette de nuit. La silhouette, les indices et les entrées fixes restent identiques à toutes les phases. Les ciels/nuages ont leurs propres comportements indépendants.

## Sorties et vérification

Le renderer d’aperçu résout les couleurs depuis la carte d’indices à chaque changement de palette. Les Aseprite 8 bits de `aseprite_indexe/` contiennent réellement des chunks de palette par frame et un cel indexé lié. Les scènes Aseprite RGBA et les atlas Tiled contiennent les phases de couleur équivalentes pour les importeurs qui ne pilotent pas une palette.

`verify_zones_tt.py` contrôle ces deux représentations, l’ordre des phases, les pixels fixes, la transparence, les entrées non animées et le rendu du navigateur. La démonstration `palette_cycling_tt.gif` montre côte à côte les indices immobiles et leurs couleurs animées.

Les fichiers sources suffisent à reconstruire la livraison sans rappeler le générateur. Aucune intégration moteur `.rsground`, collision ou transition fonctionnelle n’est annoncée.
