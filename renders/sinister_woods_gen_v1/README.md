# Entree de foret style Sinister Woods — 2 variantes generees (fusion)

Deux sessions paralleles ont produit deux variantes sur la meme branche ;
la fusion les conserve toutes les deux. Aucune n'est un livrable natif.

## Variante A — partition 1408x768 (45 tests)
- Galerie : `apercu_sinister_woods_gen_v1.html` (racine).
- Bruts : `bruts/foret_entree_magenta.png` + `bruts/sol_nu_magenta.png`.
- 7 plans `SinisterGen_*.png` (sol, chemin, rochers, buissons, vegetation,
  ombres, grotte) + composite + `manifest.json`.
- Scripts : `source/sinister_woods_gen_v1/{build,test_build,package}.py`.
- ZIP : `renders/sinister_woods_gen_v1_pack.zip`.
- Details (nettoyages, decoupes, limites) : voir le README d'origine dans
  le commit 4369a7f4 et `manifest.json`.

## Variante B — terrain + avant-plan 656x1376 (32 tests)
- Galerie : `apercu_sinister_woods_v1.html` (racine). Canvas 656x1376, grille 8px.
- Bruts : `bruts/terrain_magenta.png` + `bruts/avant_plan_magenta.png`.
- 7 calques `layers/` : sol reconstitue, chemin, rochers, arbres gauche/droit,
  grotte sombre, avant-plan (+ composites + `manifest.json`, `work/`).
- Arrivee sud (travee 72px), chemin sinueux vers bosquet nord, seuil inclus.
- Scripts (deplaces a la fusion) :
  `source/sinister_woods_terrain_fg_v1/{key_and_crop,split_layers,test_build,package}.py`.
- ZIP : `renders/sinister_woods_v1_terrain_fg_pack.zip`.
- Recomposition exacte (hors frange magenta comblee < 0,6 %, bords) ; sol sous
  les elements reconstitue par echantillonnage same-image.

## Communs (les deux variantes)
- Propositions GENEREES (textures inventees DA PMD) : PAS des tuiles natives /
  canoniques ; pas un Ground PMDO ; pas de collisions, warps, degats ;
  pas de test moteur ; pas d'approbation artistique.
- Piste native relayout (`source/sinister_woods_entry_v1/` +
  `exports/sinister_woods_entry_v1/`) interrompue sur demande explicite
  d'utiliser le generateur ; conservee, non terminee.
