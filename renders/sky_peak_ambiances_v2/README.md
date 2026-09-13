# Sky Peak — légère variation du layout et cinq ambiances

Version qui applique la dernière précision : **reprendre le layout de la référence, le modifier légèrement, sans ajouter de relief sur le plateau**, et proposer plusieurs moments de la journée.

## Voir
- Galerie autonome : **`apercu_sky_peak_ambiances_v2.html`** à la racine, ouverte par défaut au crépuscule.
- [Planche des cinq ambiances](PLANCHE_5_AMBIANCES.png)
- [Avant/après du layout, même éclairage](AVANT_APRES_LAYOUT.png)
- [Aube](aube/composition.png), [jour](jour/composition.png), [crépuscule](crepuscule/composition.png), [heure bleue](heure_bleue/composition.png), [nuit](nuit/composition.png).

## Modification du terrain
La base reste le terrain du GIF `2cwdrrs469f61.gif`, pas un nouveau promontoire généré. La prairie centrale est un peu élargie en écartant les bordures intérieures. Le déplacement horizontal maximal est de **12 pixels sur une toile 504×504** ; aucun déplacement vertical, aucun nouveau gradin ou relief ajouté. Les falaises latérales existantes restent présentes, puisque leur layout est la référence demandée.

Transformation documentée dans `manifest.json`, par redistribution horizontale nearest des pixels :
- Abscisses source : 0,142,174,330,362,503.
- Abscisses destination : 0,136,162,342,368,503.

Cela conserve le matériau source mais **ne constitue plus une conservation pixel-identique du layout** : certains pixels sont répétés/omis par la faible redistribution horizontale. Les fleurs suivent la même transformation pour rester posées sur l’herbe. Les versions antérieures restent disponibles.

## Ambiances
- **Aube** : ciel mauve/rosé, lumière douce.
- **Jour** : ciel bleu, prairie vive.
- **Crépuscule** : ciel violet/pêche, teintes plus chaudes et adoucies.
- **Heure bleue** : atmosphère froide, lune et étoiles.
- **Nuit** : filtre Abyss existant appliqué au terrain et aux éléments, lune et étoiles.

Les étalonnages aube/crépuscule/heure bleue sont nouveaux. Ce ne sont pas des palettes natives récupérées. Les astres passent derrière les montagnes et les nuages : au lever/coucher, le disque peut être partiellement ou entièrement masqué par le relief.

## Calques et animation
Chaque ambiance contient neuf PNG alignés 504×504 : ciel, étoiles, astre/halo, nuages lointains, montagnes, nuages proches, sol/rebord herbeux, paroi/rochers, fleurs.

`fleurs/00.png`…`31.png` : 32 phases à 50 ms, boucle de **1,6 s**. Les clés 00/08/16/24 permettent aussi la lecture au rythme original de quatre images à 200 ms. Les phases intermédiaires restent une interpolation alpha des pétales issus de la référence, pas 32 nouveaux dessins natifs.

Nuages en wrap séparé : largeur504, **−2 px/s** et **−6 px/s**, périodes252 et84 secondes. Leur horloge ne repart pas à zéro au raccord des fleurs. Les `fleurs_animation.webp` montrent uniquement les fleurs, nuages fixes pour éviter un saut artificiel ; la galerie montre le défilement continu des nuages.

## Vérifications
- Remapping terrain contrôlé exactement contre les pixels de la version source et les coordonnées annoncées.
- Déplacement limité à12px horizontal, aucune transformation verticale.
- Terrain nuit exactement égal au filtre Abyss.
- **5 compositions et160 images WebP** identiques aux recompositions de leurs calques PNG.
- Galerie testée en DOM simulé, pas de validation GPU/PMDO.

Scripts : `source/sky_peak_v1/{build_ambiances,gallery_ambiances,verify_ambiances}.py`. Ressources d’origine et provenance dans la version `sky_peak_canonique_v1`. Aucun mod natif, collision ou transition de zone modifié.
