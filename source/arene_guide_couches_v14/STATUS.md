# V14 — calques exacts de la référence + aurore en 15 frames élégantes

Demandes : « Les layer sont pas exactement celui de la référence » et « 15 frame de mouvement élégant, harmonieux changement de couleur des onde boréal dans le même design et texture à la place des boréal statique ».

- **Calques exacts** : même découpe que V13 mais l’aurore ne retient que les rubans **lumineux** (saturés ET lumineux) ; les **cristaux sombres de l’horizon** vont au terrain. Les 4 calques (ciel, étoiles, aurore, terrain) sont disjoints et **recomposent exactement le guide** — testé pixel par pixel, frame 0 aux couleurs d’origine comprises.
- **15 frames de mouvement élégant** : même design, même texture, géométrie figée (même masque, testé). Le changement de couleur est **harmonieux** : la phase avance de 1/15 de cycle par frame avec **interpolation linéaire circulaire** entre les arrêts des rampes (cyan +1/4 de cycle, magenta -1/4) — pas de saut : pas adjacent ≈ 2-3 niveaux, bien plus petit qu’un décalage de plusieurs frames (testé). Frame 0 = couleurs exactes du guide ; cycle complet en 15 frames, boucle exacte. 15 × 120 ms = 1,8 s.
- Livrables : `couches/` (4 calques, aurore 15 PNG), `aurore_elegante_15frames.webp`, `palettes_15frames.json`, scènes 0/5/10, GIFs, viewer autonome `apercu_arene_guide_couches_v14.html`, ZIP.

9 tests dédiés PASS : copie du guide, disjonction + recomposition exacte, cristaux sombres au terrain, frame 0 exacte, 15 frames géométrie fixe, progression douce, indépendance aurore/ciel, scène recomposée, WebP/GIF/manifeste. Pas de test navigateur ni runtime PMDO. Guide © d’après la référence PMD Sky (Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft) ; cadence et rampes : nos choix.

Rebuild : `.venv/bin/python source/arene_guide_couches_v14/build.py` puis `package.py`.
