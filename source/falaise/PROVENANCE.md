# Version courante — reprise complète EoS

À la demande de l’utilisateur, toute la falaise de guilde a été repassée au générateur, pas seulement sa bordure : prairie, chemin, lèvres de terrain et paroi rocheuse. Les entrées étaient la falaise existante, la carte GuildOutside recomposée au commit fourni et les références de bordures PMD Sky.

Le crop 352 × 294 px est placé à `(64,114)` dans `falaise_eos_generee.png`, puis normalisé en RGBA avec une palette de 192 couleurs. 54 pixels de bord ont été prolongés de quatre pixels au maximum pour épouser l’emprise canonique. Le rectangle `(196,328)-(284,408)` des marches est rétabli depuis la référence, afin de garder sa fidélité pixel pour pixel.

`prepare_falaise_reference.py` reconstruit cette version complète ; il ne remet plus l’ancienne juxtaposition de textures ou une retouche limitée au sommet. Les contrôles protègent l’emprise, les marches, la présence de prairie et l’arrivée du chemin.

La fidélité à la direction artistique EoS a été contrôlée visuellement. Il ne s’agit pas d’une promesse impossible de 100 % d’identité aux pixels du jeu pour les parties redessinées. Les pixels d’escalier de référence restent des graphismes tiers attribués dans l’historique.

---

# Historique des étapes précédentes

# Version courante — prairie, chemin et ciel animé

La dernière instruction remplace explicitement le sommet nu : **repasser tout le sommet au générateur, créer une prairie avec un chemin et des bordures logiques avec le relief**. Cette version est celle à reconstruire.

- `sommet_genere.png` contient la retouche réellement issue du générateur, normalisée au plus proche voisin et conservée en RGBA ; sa palette est limitée à 192 couleurs. L’image de départ était un guide de prairie/chemin avec la paroi et les marches en contexte.
- Le sommet entier (`masque_sommet.png`, **55 321 pixels**) utilise la génération à 100 %. Le raccord progressif n’est appliqué que dans la bordure, via `masque_harmonisation_sol.png` ; il ne réintroduit pas la vieille texture sur la prairie.
- `falaise_avant_harmonisation.png` garde la version précédente pour protéger le contour et la paroi hors raccord. Le rectangle d’escalier `(196,328)-(284,408)` reste inchangé, comme l’attestent les contrôles.
- La normalisation du crop de 352 × 234 px a prolongé 17 pixels de son bord d’un pixel au maximum pour épouser l’emprise. Ce n’est pas une nouvelle texture dessinée par code.
- `prepare_falaise_reference.py` est désormais un **assembleur de la retouche générée**, pas un remplissage par fragments. Il contrôle aussi la couverture de prairie et l’arrivée du chemin aux marches.
- Les essais de sommet nu et la première retouche qui conservait des éléments de jardin ont été abandonnés après les corrections de l’utilisateur. Ils ne sont pas les sources de la prairie finale.

## Nuages et étoiles

Une nouvelle banque de **six silhouettes différentes** a été générée : cumulus, forme effilée, banc, cirrus, fragments et forme déchiquetée. Elle est conservée dans `../exterieurs/nuages_six_formes.png`, en deux colonnes et trois lignes. `prepare_nuages.py` extrait les six cellules, les place au format natif et réduit leur palette à 96 tons, sans changer leurs silhouettes.

La lune et les étoiles restent séparées du ciel. Les composantes d’étoiles sont regroupées ; la plus grande composante, celle de la lune, est exclue du scintillement. Les courbes ont 24 phases de 250 ms, avec des périodes internes et des phases différentes. Le cycle global dure six secondes, sans clignotement brutal. Les PNG des astres correspondent à l’intensité de l’image 0.

`exterior_animation.py` exporte les mêmes opérations vers Aseprite et Tiled, avec cels liés et atlas de périodes courtes. Le navigateur reprend ces phases, sans requête réseau. Les vérificateurs relisent les fichiers, contrôlent la lune fixe, le contour, l’escalier, les boucles et les pixels des compositions.

Les autres ciels et le relief lointain retenus dans la version précédente restent en place. La seconde scène, décrite dans `../sharpedo/PROVENANCE.md`, ne remplace pas celle-ci. Les anciennes salles et la terrasse ne sont pas modifiées.

Les marches et les parties de paroi d’origine restent des régions graphiques tierces provenant de la référence attribuée ci-dessous ; la nouvelle prairie, les nuages et les ciels sont générés. Ne pas réattribuer les régions de référence à une génération originale ni supposer une nouvelle licence pour elles.

---

# Historique — versions précédentes, pas la recette courante

# Sources de la falaise — correction du 9 septembre 2026

## Consigne de cette révision

L’utilisateur demande **le même escalier et le même sol que la référence, sans les arbres**, ainsi qu’un ciel amélioré avec une vraie version nocturne. Cette demande remplace l’approximation de terrain de la première proposition.

## Sol et marches : fidélité à GuildOutside

Référence : [Minemaker0430/ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins/tree/b8c0de576606c5a24802158462d5d1d7e561f72d), commit `b8c0de576606c5a24802158462d5d1d7e561f72d`, `Data/Ground/guild_outside.rsground`, texture `Content/Tile/GuildOutside.tile`. Le README de cette référence crédite notamment **Sloth** pour les Ground Maps.

- `reference_terrain.png` conserve **48 988 pixels** de sol et de paroi dans leurs positions natives. Le reste est transparent.
- `reference_escalier.png` est le rectangle original `(196,328)-(284,408)`, soit 88 × 80 px. Il inclut toutes les marches et leurs raccords immédiats. Il n’est ni redimensionné ni redessiné.
- `masque_falaise.png` délimite le terrain ; `masque_retouche_sol.png` délimite les régions à dégager, anciennement occupées par le bâtiment, la grille, les arbres et accessoires du plateau.
- `prepare_falaise_reference.py` comble uniquement ces régions avec des fragments de 16 × 16 px du sol déjà dégagé : sélection par continuité de couleur aux bords, recouvrement de 4 px, graine `809`. Les fragments de chemin trop clairs sont exclus pour ne pas dupliquer la voie centrale partout. Aucun pixel protégé n’est modifié.
- Le résultat `falaise_native.png` est conservé en **RGBA**, sans nouvelle réduction de palette. Le reconstructeur ne lui applique plus de chroma-key susceptible d’altérer un pixel de roche.
- Le jour conserve exactement les couleurs protégées ; les autres ambiances changent leur palette sans déplacer aucun pixel. Il n’est donc pas prétendu que leurs couleurs sont celles des versions nocturnes du dépôt tiers.
- L’overlay `vegetation_native.png` et son guide sont maintenant entièrement vides. Les petites herbes, fleurs et plantes déjà présentes dans les régions conservées du terrain restent en place. Les deux arbres du plateau sont retirés, pas la forêt du paysage lointain.

Un essai de restauration au générateur a été réalisé, mais rejeté pour le terrain : il modifiait le cadrage et dupliquait des éléments. Ses pixels ne sont pas utilisés dans la native finale. La conservation et la prolongation de la texture réelle évitent de proposer une nouvelle approximation des marches et du sol.

**Provenance tierce :** contrairement à la première proposition, cette correction réutilise des régions graphiques de la référence à la demande de l’utilisateur. Ces régions ne doivent pas être présentées comme des illustrations originales générées ni recevoir une nouvelle licence supposée. Les fichiers `.tile` et `.rsground` complets ne sont pas inclus.

## Nouveaux ciels et nuages

Trois nouvelles images panoramiques ont été produites au générateur, puis ramenées au plus proche voisin à 480 × 160 px :

1. **Jour** : atmosphère bleu-cornflower/céruléen évoluant vers cyan/turquoise, bandes de tons et tramage pixel fin ; aucun nuage ou astre peint dans ce fond.
2. **Nuit** : fond indigo/violet dédié, croissant de lune ivoire et étoiles éparses. La lune et les points lumineux sont séparés du ciel : estimation locale du fond par inpainting, puis décomposition en vrai RGBA pour éviter des rectangles opaques autour des astres. La recomposition du ciel nocturne et des astres retrouve les pixels de l’image normalisée.
3. **Nuages** : quatre groupes de formes et tailles variées, crêtes ivoire, ombres bleues/pervenche, sur magenta. Détourage et palette de 48 couleurs ; les colonnes extrêmes restent transparentes pour le défilement cyclique.

Sources retenues : `ciel_jour_native.png`, `ciel_nuit_native.png`, `astres_nuit_native.png`, `nuages_native.png`. Elles mesurent toutes 480 × 408 px, avec l’illustration de ciel dans les 160 premières lignes. La couleur d’horizon se prolonge en dessous, derrière le terrain. Le ciel de nuit n’est **pas** obtenu en assombrissant celui de jour. Les quatre ambiances complémentaires reprennent leur palette avec le grain du nouveau ciel.

Le paysage rocheux lointain `reliefs_native.png` reste celui de la première proposition. Les douze salles et le panorama de terrasse antérieur ne sont pas modifiés.

## Contrôles

Le vérificateur contrôle les pixels de référence protégés, tout le rectangle de l’escalier, les deux nouveaux fonds de ciel, le calque d’arbres vide, les PNG composés et chaque frame Aseprite/Tiled. L’examen visuel reste nécessaire pour juger la retouche et le style. Le navigateur vérifie également les nouveaux boutons Jour / Nuit.

---

## Historique : première proposition, remplacée pour le terrain et le ciel

Les notes ci-dessous décrivent **la version précédente**, pas la recette actuelle. Elles sont conservées pour tracer les choix et l’essai initial ; ses natives de falaise et de végétation ont été remplacées dans cette révision.


Les choix « falaise seule, plateau libre » et « reliefs rocheux » ont été confirmés par l'utilisateur le 8 septembre 2026.

## Références et méthode

- Disposition : `GuildOutside`, carte `guild_outside.rsground` au commit `b8c0de576606c5a24802158462d5d1d7e561f72d` de [Minemaker0430/ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins/tree/b8c0de576606c5a24802158462d5d1d7e561f72d). Le README de ce projet crédite notamment Sloth pour les Ground Maps.
- La référence a été recomposée dans le cache pour examiner son implantation : 480 × 408 px, plateau au centre, escalier sud, entrée au nord. Ses fichiers `.tile`, `.rsground` et leur rendu ne sont pas redistribués ici.
- Style du projet : `exterieur/jour.png`, paysage validé déjà présent. La nouvelle scène ne réutilise pas la vallée, le village ou la rivière de cette image.
- Les trois guides en aplats sont des **guides de placement**, pas les dessins finaux. La falaise, les reliefs et la végétation ont été réalisés avec le générateur d'images, sur magenta, puis normalisés au format natif. Une retouche supplémentaire du sol a ajouté la texture légère de terre et d'herbe.
- Les natives `*_native.png` sont les **sources retenues pour la reconstruction**. Les PNG livrés en sont dérivés par détourage, composition et palettes, sans nouvel appel au générateur.
- Nuages : réutilisation de `source/paysage_reference/jour_03_nuages.png`, réduit au plus proche voisin à 480 × 320 puis placé à `(0, 78)`.
- Astres nocturnes : `source/paysage_reference/nuit_02_astres.png`, réduit de la même façon puis placé à `(0, 15)`.
- Ciels, palettes et petits soleils aube/soir : traitements Python, selon la méthode déjà employée dans `rebuild_landscapes.py`.

## Normalisation des images retenues

Les premières sorties du générateur mesuraient 1120 × 944 px. Leurs marges ne respectaient pas exactement le guide ; elles n'ont pas été livrées telles quelles.

1. Réduction au plus proche voisin à 480 × 408.
2. Falaise : correspondance verticale source → cible `(0 → 0, 20 → 118, 238 → 333, 310 → 408)`. Cela rétablit l'espace de ciel et la hauteur de la face avant. Le bas flottant de la sortie initiale est hors cadre : le rocher et l'escalier continuent au bord sud.
3. Reliefs : translation verticale de 30 px, sans déplacement horizontal. La canopée continue jusqu'au bas du cadre.
4. Végétation : détourage en six composantes, puis placement de deux arbres dans les rectangles `(66,191,84,84)` et `(330,191,84,84)`, et de quatre petits arbustes dans `(76,305,24,24)`, `(377,301,24,24)`, `(109,363,20,20)`, `(350,365,20,20)`.
5. Texture du plateau : retouche au générateur d'un extrait `(64,117)-(405,334)`. La texture est appliquée seulement à l'intérieur du plateau, sans toucher à la silhouette ni à l'escalier. Les surfaces restent libres de bâtiment et de mobilier ; les petits éclats sont de la texture de terrain.
6. Conservation des natives sur magenta en palette de 256 couleurs, sans dithering. La reconstruction exporte des PNG **RGBA**, y compris pour les calques vides.

## Consignes des générations

### Falaise

Créer un calque de falaise original en pixel art PMD, sur `#FF00FF`, en suivant le guide de placement et la perspective de `GuildOutside`. Mesa centrale, sommet large et vide, roches sédimentaires chaudes, un escalier rectiligne d'environ 64 px allant de `(208,333)` jusqu'au bord sud. Aucun bâtiment, emblème, porte, tente, personnage, arbre, buisson, mobilier, bannière, ciel ou paysage dans ce calque. Ne pas en faire une île flottante. Conserver un pixel fin, sans blocs de 8 px, flou ou grille.

### Reliefs

Créer un décor lointain continu de mesas rocheuses et de forêt, sans falaise jouable au premier plan. Reliefs pêche, ocre et rose poussiéreux ; canopée olive et verte en bas. Ciel laissé en magenta. Aucun village, rivière, mer, bâtiment, escalier ou accessoire. Le décor doit continuer derrière toute la largeur de la falaise, même dans les zones masquées dans la composition.

### Végétation

Créer seulement deux arbres latéraux et quatre petits arbustes, isolés sur magenta, dans les positions du guide. Feuillage vert mousse/émeraude, lumière jaune-verte, troncs courts. Garder le centre entièrement vide. Aucun sol, rocher, arrière-plan, bâtiment, personnage, mobilier, fleur ou bannière.

### Retouche du sol

Conserver exactement la distribution terre/herbe et la palette, ajouter une texture discrète de sable, de minuscules éclats incrustés et quelques brins d'herbe fins. Aucun nouvel objet ni obstacle. Ne pas transformer la zone libre en surface encombrée. La silhouette, le cadrage et l'escalier restent ceux de la native retenue.

Ces paragraphes consignent les contraintes utilisées, pas une garantie de régénération identique par un modèle d'image. Pour une reprise fidèle, partir des natives conservées.
