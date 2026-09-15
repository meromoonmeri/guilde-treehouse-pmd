# Steam Cave — un geyser central et quatre petits geysers

Décor original648×624 de `Steam_Cave_Peak_TDS.png`, partagé **sans perte** en sol et parois. L’entrée rocheuse au nord et les textures/layout d’origine sont conservés. La référence `Steam_Cave_entrance_TDS.png` a également été inspectée, mais le fond effectivement utilisé est Peak.

Ajouts :1geyser central et4mini-geysers ; chaque bouche fixe, jet ascendant et vapeur sont sur des calques indépendants. Cycles décalés,12poses/4secondes. Le geyser central monte davantage ; les mini-geysers n’émettent pas tous simultanément au maximum. Aucun déplacement des bouches.

**17calques** au total :2de décor,5bouches,5jets,5vapeurs. PNG alignés, compositions, WebP et ORA de la pose0, jour/nuit.

Bouches, jets et vapeur sont **dessinés procéduralement en pixel art**, pas générés par le modèle et pas extraits d’une animation canonique Steam Cave. La limite du générateur avait été atteinte après les raccords de cascades et les neuf autres biomes ; les références originales ont servi directement à ce décor.

Filtre exact Abyss appliqué à chaque calque. La vapeur possède une transparence variable : filtrer ses calques puis les composer n’est pas bit-identique à filtrer une scène déjà aplatie, du fait des arrondis et de la transformation colorimétrique. Le filtre de chaque calque est vérifié, sans approximation ajoutée.

Contrôles : fond recomposé identique à l’original,24compositions recomposées,2ORA, filtre nocturne exact par calque. **Aucun test PMDO, collisions ou échelle moteur.** Les passages visuels autour des geysers ne constituent pas une définition de collisions.

Import éventuel8px, basenames distincts `steam1_jour_*` et `steam1_nuit_*`. Scripts : `source/steam_cave_geysers_v1/build.py` ; vérification commune `source/donjons_10_biomes_v1/verify_all.py`.
