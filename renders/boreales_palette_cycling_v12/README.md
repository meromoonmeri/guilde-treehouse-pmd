# V12 — onde boréale en palette cycling (style Halcyon), sans ciel

Demande : « générer les onde boréal sans ciel et que leurs mouvement soit logique les un après les autres en palette cycling dans le style halcyon ».

- **Planche générée** (`bruts/palette_cycle_8.png`, 2×4) : ruban boréal sur fond magenta. Les cases faisaient varier les **silhouettes** entre elles (IoU 0,51) : le cycling n'est donc **pas** pris case par case, et ces variantes de pose ne sont pas réutilisées comme animation. Seule la géométrie du ruban de la case 0 est retenue.
- Extraction par inondation du magenta depuis les bords (méthode V11), suppression des composantes < 60 px, calque 768×256 transparent.
- **Vrai palette cycling** : une seule image indexée (9 entrées — rampe cyan 0–3, rampe magenta 4–7, corps sombre 8 fixe) et 8 rotations de palette (+1 cyan, −1 magenta, période 4). La forme est fixe, la lumière circule.
- 8 frames × 120 ms = **0,96 s** ; la reprise frame 8 → frame 1 est exacte (période 4 sur les deux rampes).
- **Assets moteur** : `onde_indexee.png` (mode P) + `onde_alpha.png` + `palettes_8frames.json`. Les calques `couches/PaletteCycleV12_frame_00..07.png` restent la version éditable livrée en parallèle.
- Livrables : WebP transparent 8 frames, GIF effet seul, planche de contrôle, scènes posées sur notre ciel (ciel+étoiles V3 / glace V8 / terrain V3 byte-identiques), aperçu autonome `apercu_palette_cycling_v12.html`, ZIP. Aucun wrap.
- **À ne pas refaire** : alignement des cases par décalage (formes trop différentes, dx ±8, erreur 9–26 px) et extraction multi-cases comme base du cycling. Un `aligner()` subsiste dans `build.py` mais ne déplace rien ici : le test d'égalité calque/décodage indexé le vérifie.

10 tests dédiés PASS : provenance du brut, 8 calques, silhouette identique (>97 % IoU), couleurs avancent, boucle fermée, bords sans ciel, contexte intact, **décodage indexé identique aux calques (RGBA à l'octet près, alpha inclus)**, WebP/GIF et durées, manifeste. Pas de test navigateur ni runtime PMDO. Génération d'après la référence canonique © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft — pas le cycle officiel du jeu.

Rebuild : `.venv/bin/python source/boreales_palette_cycling_v12/build.py` puis `package.py`.
