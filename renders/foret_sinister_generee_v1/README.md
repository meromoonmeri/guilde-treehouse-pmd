# Forêt Sinister générée V1 — entrée de donjon (rendu généré)

Entrée de forêt style Sinister Woods : chemin sud → grotte sombre nord,
gros arbres à racines, rochers, lisière noire. **Dessin 100 % généré**
(d'après références Mystifying Forest + guide V3), PAS des pixels natifs,
PAS des bouts de map. 848 x 1264 (grille 8 px), aucun resampling.

## Contenu
- `bruts/foret_sinister_complete.png` : scène complète générée (2e essai conservé : `brume_magenta.png` remplacé par `brume_noir.png` pour la brume).
- `bruts/foret_sinister_sol.png` : variante sol nu non recalée (bonus, même courbe approximative).
- `calques/SinisterGenV1_*.png` : 8 calques (sol reconstitué sous les éléments, chemin, sous-bois, rochers, troncs, canopées, profondeur, frange). Recomposition = brut exact (0 px d'écart).
- `SinisterGenV1.ora` : projet multicouche éditable (GIMP/Krita/MyPaint).
- `SinisterGenV1_composite.png` : composition de contrôle (= brut).
- `anim/overlay_00..47.png` + `anim_overlay.webp` : 48 frames x 100 ms (4,8 s, boucle exacte), brume dérivante + 54 lucioles.
- `preview_scene.gif` / `preview_scene.webp` : aperçu animé x0.5.
- Galerie : `apercu_foret_sinister_v1.html` à la racine du dépôt.

## Limites
- Les calques sont des partitions de surfaces visibles : les faces cachées (sous canopées) sont reconstituées, pas dessinées.
- Le sol caché est un remplissage plausible (voronoï d'herbe), visible uniquement si on masque les calques supérieurs.
- Aucun test PMDO/GPU, aucune collision/warp. Prochaine version prévue : méthode canonique (guide générateur + tuiles natives multicouches style Halcyon).

## Reproduction
```
.venv/bin/python source/foret_sinister_generee_v1/build.py
.venv/bin/python source/foret_sinister_generee_v1/animate.py
.venv/bin/python source/foret_sinister_generee_v1/package.py
.venv/bin/python source/foret_sinister_generee_v1/test_v1.py
```
