# Southern Jungle — deux zones à geysers, jour/nuit

Deux layouts générés séparément d’après `Southern_Jungle_entrance_S.png` et `Southern_Jungle_exit_S.png` :
- **clairiere** : jungle entourant les geysers, chemin au sud et passage végétal au nord ;
- **clairiere_grotte** : même intention de clairière tropicale, avec grotte rocheuse au nord. La référence Steam Cave Entrance a aussi guidé la roche.

Ce sont deux propositions apparentées, pas un seul layout où seule la grotte serait activée/désactivée. Chaque scène648×504 contient un geyser central et quatre petits.

## Génération et végétation native
Le sol, les chemins assortis, le relief, les bouches de geyser et une partie de la végétation viennent des deux nouveaux bruts générés. Des **groupes de végétation natifs Southern Jungle** sont ajoutés sur les côtés à l’échelle1:1, sans changement de RGB ni redimensionnement. Ce sont les groupes d’arbres et de palmes de la référence, pas des arbres génériques recolorés.

Le fond de sol de ces groupes est rendu transparent, et ils sont découpés pour dégager chemins et bouches. Une transition d’alpha32px en haut évite une jonction rectangulaire avec le décor généré. Les RGB natifs sont vérifiés ; il ne s’agit donc pas de sprites RGBA intégralement intacts. **Toute la végétation de la scène n’est pas native** : le fond généré reste présent derrière ces groupes.

## Calques et animation
**29calques par version**, tous alignés648×504 :
- sol reconstruit sous les éléments masqués ;
- chemins ; roche/grotte ; végétation de fond, gauche, droite ;
- deux groupes végétaux natifs ; orifices d’émission ;
- cinq bouches de geyser et cinq rebords avant ;
- cinq jets et cinq couches de vapeur.

Les masques du décor sont reconstruits depuis le brut. Avant ajout des groupes natifs/orifices et animations, la recomposition reproduit exactement le brut réduit au cadrage final. Le sol caché est rempli depuis les pixels de sol voisins : c’est une reconstruction éditable, pas une surface cachée récupérée de la génération.

Les geysers utilisent **quatre poses réellement générées**, détourées du magenta, puis séparées en eau et vapeur. Cycle de12états sur4secondes ; petites émissions décalées les unes des autres. La taille des petits geysers est adaptée à leurs bouches. Les bouches ne bougent pas. Jets et vapeur générés, **pas des animations canoniques récupérées**.

PNG par calque et par état, compositions, WebP animés et ORA de l’état0. Filtre exact Abyss appliqué par calque. Les transparences peuvent rendre le filtrage par calque différent du filtrage d’une scène déjà aplatie : les contrôles portent sur le filtre exact par calque et la recomposition.

## Vérifications / limites
48compositions recomposées,4ORA,29calques par zone, filtre nuit exact par calque et RGB/échelle des groupes végétaux natifs vérifiés. Contrôles communs : `renders/donjons_generes_dtef_v3/verification_finale.json`.

**Aucun test PMDO, collisions, navigation ou échelle en jeu effectué.** Les chemins sont visuellement dégagés ; ce n’est pas une validation moteur. Les scènes Ground ne sont pas des DTEF de donjon. Import PNG Ground éventuel en8px, en conservant leur cadrage ; basenames distincts `jgv2_<zone>_<mode>_*`.

Bruts et sprites intermédiaires conservés dans le dépôt. Scripts : `source/jungle_geysers_v2/build.py`. Les versions Steam Cave antérieures sont préservées, non remplacées.
