# Entrée de forêt style Sinister Woods — v1 (générateur)

Galerie : `apercu_sinister_woods_v1.html` (racine). Canvas 656×1376, grille 8px.

## Ce que c'est
- **Proposition générée** (2 images au générateur, DA PMD) : terrain de forêt
  sombre + plan d'avant-plan (troncs et feuillages), détourés du magenta,
  découpés en **7 calques** : sol reconstitué, chemin, rochers, arbres
  gauche/droit, grotte sombre, avant-plan.
- Parcours : arrivée au sud (travée 72px), chemin sinueux vers le bosquet
  sombre au nord, seuil inclus. Connectivité sud→grotte testée.
- Recomposition des calques = pixels d'origine à l'identique (hors frange
  magenta comblée < 0,6 %, bords).

## Ce que ce N'EST PAS
- Pas des tuiles natives / canoniques ; pas un Ground PMDO ; pas de collisions,
  warps, dégâts ; pas de test moteur ; pas d'approbation artistique.
- Le sol sous les éléments est **reconstitué** (échantillonnage same-image),
  pas un sol caché d'origine. Les faces arrière des arbres ne sont pas
  dessinées pour des mouvements arbitraires.

## Fichiers
- `bruts/` : 2 générations magenta (conservées telles quelles).
- `work/` : keying, revues, planches de contrôle.
- `layers/` : 7 PNG RGBA + composites + `manifest.json`.
- Scripts : `source/sinister_woods_gen_v1/` (`key_and_crop.py`,
  `split_layers.py`, `test_build.py` — 32 tests PASS).

## Historique
- Piste native relayout (`source/sinister_woods_entry_v1/`) interrompue sur
  demande explicite d'utiliser le générateur ; conservée, non terminée.
