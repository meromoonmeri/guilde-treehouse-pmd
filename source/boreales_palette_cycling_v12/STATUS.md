# V12 — onde boréale en palette cycling (style Halcyon), sans ciel

Demande : « générer les onde boréal sans ciel et que leurs mouvement soit logique les un après les autres en palette cycling dans le style halcyon ».

- **Planche générée** (`bruts/palette_cycle_8.png`, 2×4) : le MÊME ruban dans les 8 cases, silhouette strictement identique, et les bandes de couleur avancent d'un pas par frame — c'est le principe du palette cycling Halcyon : la forme est fixe, la lumière circule.
- Extraction par inondation du magenta depuis les bords (V11), calques 768×256 transparents : `couches/PaletteCycleV12_frame_00..07.png`.
- 8 frames × 120 ms = **0,96 s**, boucle fermée (frame 8 ≈ frame 1).
- Livrables : WebP transparent 8 frames, GIF effet seul, planche, scènes sur notre ciel (V3+étoiles / glace V8 / terrain V3 byte-identiques), aperçu autonome `apercu_palette_cycling_v12.html`, ZIP.

9 tests dédiés PASS : provenance, 8 calques, silhouette identique (>97 % IoU), couleurs avancent, boucle fermée, bords sans ciel, contexte intact, WebP/GIF, manifeste. Pas de test navigateur ni runtime PMDO. Génération d'après la référence canonique © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft — pas le cycle officiel du jeu.

Rebuild : `.venv/bin/python source/boreales_palette_cycling_v12/build.py` puis `package.py`.
