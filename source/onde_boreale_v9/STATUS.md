# V9 — onde boréale : 10 frames sur 10 calques, physique d’onde transversale

Demande : « Génère 10 frame sur leurs propre layer, l’animation physique et logique d’onde boréale ».

## Physique de l’onde
- **Dessin maître** généré (fond magenta/blanc, 1792×592 réel) → extraction : fonds retirés par composantes claires connexes, voile intérieur rempli **sauf** zones de fond et poches ouvertes entre les rayons (le remplissage `fill_holes` seul créait un voile gris parasite — corrigé deux fois), démelage des bords contre le fond le plus proche (transformée de distance). Master final 768×256 : `rideau_master_extrait.png`.
- **Onde transversale pure** : chaque colonne x du master est décalée **uniquement verticalement** de `round(12·sin(2π(2x/768 − t/10)) + 5·sin(2π(5x/768 − t/10) + 0,35)·enveloppe(x))` avec enveloppe de bord 48 px. La **phase voyage horizontalement** le long du rideau : les crêtes et les creux se propagent, la matière ne fait que monter/descendre — comme une corde qui ondule.
- **Boucle exacte** : phases à périodes entières en x (2 et 5 longueurs d’onde) et en t (t/10). Frame 10 ≡ frame 0, testé exactement (colonne par colonne).
- 10 frames × **160 ms** = 1,6 s. Aucun wrap, aucune translation horizontale (centroïde stable < 1 px, testé).

## Calques
- `couches/OndeBorealeV9_frame_00..09.png` : **chaque frame est son propre calque** 768×256 RGBA indépendant.
- `contexte/` : ciel + étoiles V3, glace latérale V8, terrain V3 — **byte-identiques** aux originaux.
- Scène 768×512 : ciel → onde (frame t) → glace → terrain. Aucun défilement.

## Livrables
`onde_boreale_10frames.webp` (10 frames transparentes, sans perte visible), `review/scene_onde_gif.gif` (scène 384×256), `review/aurore_seule.gif` (fond nuit), `review/planche_10_couches.png`, scènes PNG 0/3/6/9, aperçu autonome `apercu_onde_boreale_v9.html` (racine) : scène, calque seul, ghost de la frame précédente, frame par frame.

10 tests dédiés : master propre (aucun voile pâle), 10 couches 768×256, **physique colonne par colonne exacte** (décalage vertical pur), boucle exacte, pas de translation de masse, couverture pleine largeur, scène recomposée à l’identique, contexte byte-identique, WebP/GIF fidèles (10×160 ms), manifeste. Pas de test navigateur interactif ni runtime PMDO. Dessin et cadence choisis — pas le cycle officiel du jeu. Référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.

Rebuild : `.venv/bin/python source/onde_boreale_v9/build.py` puis `package.py`.
