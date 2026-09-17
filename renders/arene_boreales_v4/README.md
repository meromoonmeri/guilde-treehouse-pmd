# Boréales V4 : animation interne, pas seulement un défilement

Correction utilisateur : la V3 n'animait pas les rideaux eux-mêmes. Ses nombreuses frames étaient les positions successives d'une bande fixe. **Cette méthode est insuffisante pour cette demande.**

La V4 fournit **88 poses intrinsèques distinctes** sur 8,8 secondes : plis voyageurs, ondulations verticales et latérales, variations de hauteur des rideaux et scintillement par alpha. Les pixels de couleur proviennent du dessin canonique ; la déformation et le scintillement sont nouvellement créés, non extraits d'un cycle officiel.

L'aperçu démarre **sans défilement** : on voit les formes changer sur place. Une case indépendante ajoute le wrap. L'animation des formes peut aussi être arrêtée pour comparer avec le défilement seul. Pause, frame suivante, curseur et bouton de raccord disponibles.

## Livrables
- `animation/frames/AuroreV4_000..087.png` : 88 calques RGBA 792×240, 100 ms par pose.
- `animation/aurore_sans_defilement.webp` : aurore seule réellement animée sur transparence, sans perte pour alpha et couleurs visibles. Les RGB invisibles sous alpha zéro peuvent être réencodés par WebP ; les PNG sont exacts.
- `review/aurore_ANIMEE_sans_scroll.gif` : démonstration animée, fond sombre fixe, aucun défilement.
- `review/scene_animee_wrap.gif` : scène complète, 264 étapes / 26,4 s, aperçu à demi-résolution ; terrain/ciel restent fixes.
- `review/poses_sans_defilement.png` : quatre poses à placement identique.
- `calques/` : ciel, étoiles et terrain large de V3 conservés byte-identiques, séparés.
- `apercu.html` dans le ZIP ; `apercu_boreales_animees_v4.html` à la racine du dépôt.

## Lecture / wrap
Toutes les 100 ms : afficher la pose `f modulo 88`. Optionnellement, dessiner deux copies jointives à x=`-(3*f modulo 792)` et x+792. Le cycle combiné revient exactement après264 étapes, soit trois cycles de formes. Ce ne sont **pas** 264 copies d'une image statique. Le terrain et le ciel ne changent pas.

La déformation est périodique spatialement et temporellement. Les fonctions utilisent des harmoniques entières ; pose88=pose0. Le saut87→0 est contrôlé par rapport aux pas internes. Pas de dernière image dupliquée qui créerait un arrêt.

9 tests dédiés : 88poses distinctes, changements non rigides et visibles sans scroll, cycles exacts, raccord temporel, calques préservés, WebP transparent, GIF réellement animé et terrain fixe. Syntaxe JS vérifiée ; pas de test interactif navigateur ou runtime/import/collision PMDO. Autres zones non terminées. La V3 et les références restent préservées.

Références PMD fournies dans le dépôt : Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft. Aucune permission supplémentaire de redistribution présumée. Voir manifeste V3 pour provenance des dessins et des générations terrain/ciel.

Rebuild : `.venv/bin/python source/arene_boreales_v4/build.py` puis `.venv/bin/python source/arene_boreales_v4/package.py`.
