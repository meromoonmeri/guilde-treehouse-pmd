# V10 — effet onde boréal CANONIQUE : texture récupérée, sans ciel, 10 frames sur son calque

Demande : « tu dois générer les effet onde boréal sans le ciel derrière comme tu avais fais pour les étoiles et l’effet boréal doit s’animer sur son propre layer en plusieurs frame tu dois récupérer la texture de l’onde boréal canonique ».

## Texture récupérée, pas redessinée
- Source : `aurorepmdsky.png`, la texture canonique du ciel boréal PMD Sky (fournie), SHA consigné au manifeste.
- Extraction **comme pour les étoiles V3** : les rubans lumineux sont retenus par luminosité + saturation ; le ciel sombre canonique (lum ~21, sat ~63) n’est **pas** dans le calque ; les étoiles sont exclues (petites composantes isolées, puis passe finale : point visible peu saturé à > 10 px d’un ruban saturé — zéro résidu testé) ; nuages et pics (y ≥ 144) hors calque, fondu bas 134→144 ; ×2 nearest (528×288), bords à zéro, RGB nettoyé sous alpha 0.
- `effet_canonique_extrait.png` : l’effet lumineux seul, transparent — **aucun ciel derrière**.

## Animation : onde transversale, 10 frames sur son propre layer
- `couches/EffetBorealeV10_frame_00..09.png` : chaque frame est un calque indépendant 528×288 RGBA.
- Décalage **strictement vertical** par colonne : `8·sin(2π(2x/528 − t/10)) + 4·sin(2π(5x/528 − t/10) + 0,4)` sous enveloppe de bord 40 px — la phase voyage horizontalement, les rubans ondulent, la matière ne glisse pas latéralement. Périodes entières : **frame 10 ≡ frame 0 exactement** (testé colonne par colonne). 10 × 160 ms = 1,6 s.
- Posé **une seule fois** à (120, 0) dans la scène 768×512, entre le ciel V3 (+ étoiles V3) et la glace V8 + terrain V3 (tous byte-identiques, copiés dans `contexte/`). Aucun wrap.

## Livrables
`effet_boreale_canonique_10frames.webp` (transparent), `review/` (planche des 10 couches, GIF scène 384×256, GIF effet seul sur fond nuit), scènes PNG 0/3/6/9, aperçu autonome `apercu_effet_boreale_canonique_v10.html` : scène, calque seul, togglable, ghost de frame, frame par frame. ZIP `renders/effet_boreale_canonique_v10_pack.zip`.

9 tests dédiés : SHA canonique, extrait sans ciel/étoiles/bas fondu, 10 couches, **physique exacte colonne par colonne**, boucle exacte, pas de translation de masse, scène recomposée + contexte byte-identique, WebP/GIF fidèles, manifeste. Pas de test navigateur interactif ni runtime PMDO. La **texture est canonique** ; la découpe du calque et la cadence/amplitude de l’onde sont nos choix — le cycle officiel du jeu n’a pas été récupéré. © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.

Rebuild : `.venv/bin/python source/effet_boreale_canonique_v10/build.py` puis `package.py`.
