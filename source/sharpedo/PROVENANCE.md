# Retouche courante — bordures PMD Sky dans toutes les orientations

La consigne est de redessiner les motifs de bordures validés dans PMD Explorateurs du Ciel et de les adapter au cap, plutôt que conserver un contour générique uniforme.

Une bibliothèque de **20 motifs en 24 × 24 px** est conservée dans `../bordures_pmd/`, avec les références, les guides, la génération normalisée et les orientations. Elle comprend quatre rives cardinales, quatre angles sortants, quatre angles rentrants, quatre diagonales et quatre motifs de paroi. Les références sont des extraits attribués des cartes Treasure Town, GuildOutside et Sharpedo Bluff ; les motifs finaux sont redessinés au générateur et leur palette est adaptée à notre cap.

## Application à la scène

- `falaise_avant_bordures_pmd.png` conserve la version précédente comme référence de protection.
- `masque_bordures_pmd.png` sélectionne **14 312 pixels** de rives, angles et contours latéraux. `masque_chemin_protege.png` protège le chemin et sa marge.
- Le générateur a repris ces zones, guidé par les références PMD et le tileset redessiné ; le prompt est dans `../bordures_pmd/prompt_adaptation_cap.txt`.
- Le crop de 368 × 296 px est remis en place à `(136,88)` dans `bordures_layout_base.png`. 279 pixels de bord ont été prolongés de cinq pixels au maximum pour épouser l’emprise, sans redessiner les textures par code.
- La rive N est composée directement à partir de quatre lignes du motif N, selon les placements conservés. Le gazon juste sous ce rebord est conservé pour éviter une deuxième ligne de pierre isolée. Les autres contours non rectangulaires utilisent la retouche adaptée au générateur.
- `prepare_bordures_pmd.py` reconstruit la bibliothèque et cette adaptation. `prepare_sharpedo.py` l’applique après le remplacement de l’ancienne paroi, sans changer l’alpha du cap.

Le chemin, l’intérieur de la prairie, la paroi hors bande et tous les calques animés sont conservés. Le prolongement du chemin à l’est reste ouvert, et il n’y a pas de rebord artificiel sur la limite droite/basse du canevas. Les changements de bordure sont permis dans la prairie périphérique ; l’ancienne garantie de prairie entièrement identique ci-dessous appartient donc à la version précédente.

## Livrables

Atlas PNG jour/nuit, tilesets TSJ et catalogues Tiled en 24 px. Le tileset est chargé dans la palette des cartes ; le rendu du cap est une adaptation organique en PNG, non un placement automatique de toutes les bordures en tuiles carrées. Les tests contrôlent cette bibliothèque, les liens, le chemin, les sorties ouvertes et les recompositions, sans prétendre une inspection artistique automatisée.

---

# Historique — étapes précédentes

# Version courante — paroi naturelle et cycle de mer adapté

## Deux corrections de l’utilisateur

1. La falaise ne doit **pas représenter Sharpedo** : nouvelle paroi naturelle, sans yeux, bouche, dents ni silhouette de créature.
2. La mer doit s’animer à la manière de la référence, adaptée à notre carte, plutôt qu’avec le petit va-et-vient de l’ancien overlay.

Le nom affiché est désormais **Falaise côtière**. Le dossier et l’identifiant `sharpedo` sont gardés pour compatibilité des liens et des scripts.

## Paroi réellement repeinte au générateur

- Le guide transmis au générateur ne contenait plus de tête : la prairie retenue surmontait une masse de roche neutre. Les références de style étaient une portion de paroi naturelle et les reliefs du projet, pas une image de créature.
- `paroi_naturelle_generee.png` conserve cette génération au format natif, après réduction au plus proche voisin et palette de 192 couleurs. Le prompt est conservé dans `prompt_paroi_naturelle.txt`.
- `falaise_avant_paroi_naturelle.png` est le point de comparaison. `masque_paroi_naturelle.png` protège toute la prairie et son chemin, puis raccorde la nouvelle roche sous la bordure.
- `prepare_sharpedo.py` remplace aussi l’alpha de la partie inférieure : la forme de mâchoire n’est pas conservée. La transition est calculée en couleurs prémultipliées pour éviter un halo sombre sur la mer.
- Le sommet est identique à la version précédente. La paroi et sa silhouette inférieure sont nouvelles. Les guides courants sont actualisés et ne suggèrent plus de créature.

## Dix images de mer provenant de la référence

La carte `habitat_sharpedo_bluff_day.rsground`, au commit `b8c0de576606c5a24802158462d5d1d7e561f72d`, utilise dix images dans son calque Background, feuille `Habitat_SharpedoBluff_Day_Layer1`, avec `FrameLength: 10`.

`mer_reference_cycle.png` contient seulement dix extraits d’océan `(0,120)-(144,384)`, rangés en cinq colonnes et deux lignes. Ces extraits sont des **régions graphiques tierces de la référence**, pas de nouvelles illustrations générées. Aucun élément du cap ou de la créature ne s’y trouve. Le dépôt de référence et ses crédits, notamment Sloth pour les Ground Maps, restent indiqués dans l’historique ci-dessous ; ne pas attribuer une nouvelle licence à ces régions.

`prepare_mer_reference.py` :

1. extrait le fond modal par ligne de la référence, pour conserver les variations de ses dix phases ;
2. utilise le profil de couleur de notre mer générée, conservée dans `mer_avant_cycle_reference.png`, comme nouvelle profondeur d’eau ;
3. adapte les variations à cette palette avec un facteur de 0,85 et étend la largeur par réflexion continue ;
4. sépare le fond `mer_native.png` et l’overlay RGBA animé `vagues_cycle.png`, avec `vagues_native.png` comme image 0.

La recomposition retrouve les couleurs adaptées sans erreur lors de la préparation retenue. La référence est décrite dans `animation_mer_reference.json`. Les sorties emploient 250 ms par phase, cadence du kit ; `FrameLength` reste une donnée du moteur d’origine, pas une durée en millisecondes.

Le cycle court de mer dure 2,5 s. Le PPCM des périodes des nuages (504 images), étoiles (24) et mer (10) donne 2 520 images pour la boucle globale, sans saut au raccord. Les cels récurrents sont liés dans Aseprite ; les animations Tiled ont chacune leur période propre. L’aperçu embarque les dix phases de vagues exportées, et n’utilise plus le déplacement sinusoïdal de l’ancien rendu.

## Conservation et vérification

Prairie, chemin, ciels, lune, étoiles et six familles de nuages sont conservés. La première falaise de la guilde et les anciens intérieurs ne sont pas retouchés. Les tests protègent les pixels du sommet, relisent toutes les frames des exports et contrôlent les dix phases de mer, la lune fixe, le terrain fixe et les compositions dans le navigateur.

Il s’agit toujours de ressources graphiques éditables et d’un aperçu, pas d’une intégration native PMDO.

---

# Historique — cap précédent, profil remplacé

# Provenance du cap Sharpedo

## Référence de disposition

[Minemaker0430/ExplorersOfSkyOrigins, commit b8c0de576606c5a24802158462d5d1d7e561f72d](https://github.com/Minemaker0430/ExplorersOfSkyOrigins/tree/b8c0de576606c5a24802158462d5d1d7e561f72d), carte `Data/Ground/habitat_sharpedo_bluff_day.rsground`.

La carte a été relue et recomposée pour comprendre son implantation : **504 × 384 px**, grille 8 px, cap à droite, mer à gauche et en contrebas, profil rocheux évoquant Sharpedo. Les feuilles de référence sont `Habitat_SharpedoBluff_Day_Layer1`, `Layer2` et `Rock_and_Sky`. Le README du dépôt de référence crédite notamment **Sloth** pour les Ground Maps. Les fichiers complets `.tile` et `.rsground` restent dans le cache de recherche, pas dans ce module.

`guide_falaise.png` et `guide_emprise.png` sont des guides dérivés de cette disposition ; le guide de falaise contient des régions de la référence tierce. Ce ne sont pas les illustrations finales et il ne faut pas les réattribuer à une création originale.

## Illustrations retenues

1. Une première génération a peint le cap, en conservant un sommet nu et le profil rocheux fourni en guide. La native normalisée à 504 × 384 px est conservée dans `falaise_avant_prairie.png`.
2. Après la dernière instruction « prairie sur le sommet avec un chemin », une **nouvelle génération** a repris toute la surface : prairie, chemin depuis l’est, rebord herbeux, terre et raccord à la roche. Le résultat du crop 360 × 280 px est placé à `(144,104)` dans `sommet_genere.png` ; palette de 192 couleurs.
3. `masque_sommet.png` décrit la surface utilisée à 100 % (**40 793 pixels**). `masque_harmonisation_sol.png` ajoute une étroite transition de bordure. La normalisation a prolongé 39 pixels de bord, de 3,17 px au maximum, pour éviter tout trou de transparence.
4. `prepare_sharpedo.py` assemble ces deux sources, vérifie la conservation de la silhouette et de la paroi hors raccord, puis écrit `falaise_native.png`. Il ne dessine pas de nouveau terrain par code.
5. Une image de mer indépendante a été générée : océan turquoise/azur/cobalt vu d’en haut, vagues fines au loin et plus espacées vers l’avant. Elle est normalisée à 504 × 264 px et placée sous l’horizon `y=120`.
6. Les crêtes et reflets sont séparés par contraste local et inpainting du fond, puis décomposés en RGBA : `mer_native.png` et `vagues_native.png`. L’overlay garde une petite marge transparente pour ses déplacements cycliques.

Les variantes jour et nuit sont exportées. Les ciels, la lune/les étoiles et les six familles de nuages utilisent les sources de la première scène, adaptées au format du cap au plus proche voisin.

## Animation

La falaise est fixe. Les nuages se déplacent de 1 px par image. Les vagues ont 24 phases de déplacement et d’intensité ; les étoiles 24 phases d’opacité par groupes. La lune est exclue du scintillement. Toutes les phases se répètent exactement dans la boucle globale de 504 images.

Les illustrations et retouches viennent du générateur ; Python sert à la normalisation, aux masques, aux palettes, à la séparation des plans, à l’animation et aux exports. Les sources retenues suffisent à reconstruire les livrables sans rappeler le générateur.

## Limite de livraison

Il s’agit d’un module graphique éditable et d’un aperçu animé, pas d’une carte PMDO fonctionnelle. Les repères Tiled ne définissent pas de navigation ni de destinations. Les validations concernent la lecture/recomposition des fichiers et le navigateur, pas les interfaces d’Aseprite ou de Tiled.
