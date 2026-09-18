# V13 — rebase sur layout_guide.png (V1) : couches séparées, aurore animée indépendante

Demande : « me rebase sur source/ice_arena_aurora_v1/generation/layout_guide.png, faire les plusieurs layer, aurores animées indépendantes du ciel ».

- **Source** : `layout_guide.png` (928×1152) copié intact dans `guide/`, SHA consigné.
- **4 calques disjoints** (`couches/`) : `ciel_fixe.png` (navy, inondé depuis le haut), `etoiles_fixes.png` (petites taches 1-40 px), `aurore/AuroreGuideV13_frame_00..07.png` (8 frames), `terrain_fixe.png` (murailles, cratère, chemin). Recomposition = guide exact (testé, y compris frame 0 aux couleurs d'origine).
- **Aurore indépendante du ciel** : palette cycling des **vraies couleurs du guide** — pixels classés par famille (cyan/magenta) et quartile de luminosité ; frame 0 = origine exacte ; frames 1-7 = rotation des rampes (cyan +1, magenta -1, période 4 | 8, boucle exacte). Géométrie verrouillée : même masque dans les 8 frames. Ciel, étoiles et terrain strictement figés.
- 8 × 120 ms = 0,96 s. Livrables : WebP 8 frames, GIFs (scène, aurore seule), palettes JSON, scènes 0/2/4/6, viewer autonome `apercu_arene_guide_couches_v13.html` (calques togglables), ZIP.

8 tests dédiés PASS : copie du guide, calques disjoints recomposant exactement le guide, frame 0 = aurore du guide, 8 frames même géométrie avec cycling réel, indépendance aurore/ciel/étoiles, scène recomposée, WebP/GIF, manifeste. Pas de test navigateur ni runtime PMDO. Guide d'après la référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft ; cadence et rampes : nos choix, pas le cycle officiel.

Rebuild : `.venv/bin/python source/arene_guide_couches_v13/build.py` puis `package.py`.
