# EGC1 — Entrée Grotte des Cascades, sud → nord

- **Aperçu interactif autonome :** `apercu_entree_grotte_cascade_sud_nord_v1.html` à la racine.
- **Projet PMDO 0.8.12 :** `EGC1_projet_pmdo_0812.zip`.
- **Calques PNG 8 px + OpenRaster :** `EGC1_calques_png_8px.zip` et `EGC1_entree_grotte_cascade_calques.ora`.
- **Source et bruts générés :** `source/entree_grotte_cascade_sud_nord_v1/`.

La composition est guidée par `Waterfall_Cave_ledge_TDS.png`, une référence disponible dans le dépôt et non utilisée par la série récente. Le décor, le sol sous-jacent et la matière d’eau ont été générés séparément sur fond magenta, sans collage de fragments de cartes. Les bruts 1200 × 896 sont normalisés uniformément en **768 × 576 px**, grille **96 × 72 cases de 8 px**, sans étirement anisotrope.

Le décor comporte une entrée au nord, une approche large depuis le sud, des parois de caverne et quatre bassins/courants. L’eau est sur un calque indépendant : 12 phases de palette-cycling, 10 ticks par phase (boucle proposée de 2 s). Les calques sont alignés à l’origine (0, 0), avec un sol complet sous les éléments visibles.

**Provenance :** textures de terrain et matière d’eau générées en DA PMD, et non pixels de tiles natives certifiés. L’animation est une proposition créée pour ce lot, pas un cycle officiel récupéré. Cette carte n’a pas encore reçu d’approbation artistique.

## Marqueurs et contrôles

Le Ground contient `entrance` au sud et `donjon_seuil` au nord, sans warp/destination de donjon. 9 tests d’assets couvrent les tailles/grille, le détourage, l’animation, la recomposition OpenRaster, l’accès avec collider 16 × 16 et la reconstruction des calques depuis les `.tile` du Ground. **Aucun rendu GPU, mouvement de personnage ou gameplay dans PMDO n’a été validé.**

- `review/EGC1_scene_phase00.png` : composition à 1×.
- `review/EGC1_scene_x2.png` : zoom entier ×2.
- `review/EGC1_scene_animee.webp` : aperçu de l’eau animée.
- `review/EGC1_collisions_marqueurs.png` : obstacles calculés en rouge, arrivée jaune, seuil cyan.
- `manifest.json` : référence, hashes, normalisation, règles du masque magenta, provenance des calques, accès et limites.
