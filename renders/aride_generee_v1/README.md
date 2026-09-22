# Entree aride generee V1

Map finale 400x360 (grille 8 px) : parois canyon + bouche de grotte a l'ouest,
sol sableux avec sentier, 8 props (4 arbres morts, 2 arbustes, 2 blocs),
poussiere animee en 3 bandes (12 frames x 100 ms, boucle parfaite).

## Methode (rendus generes, PAS natif)
4 bruts generateur guides par `entrancearidedungeonpmdsky.png` :
parois/bouche, sol, planche de props, planche de poussiere.
Downscale /3 (BOX), detourage magenta (seuil global d<170 + pelage 2 anneaux),
quantification 128 couleurs, assemblage par calques, raccord dithere (Bayer 8)
entre le seuil de la paroi et le sol.

## Contenu
- `couches/` : plafond, sol, parois, 8 props separes (pieds sur grille 8 px)
- `fx/fx_00..11.png` : derive horizontale wrap (48/72/36 px par cycle) + scintillement alpha
- `compos_anim/` : 12 composites, `scene_animee.gif` / `.webp`
- `aride_generee_v1.ora` : calques editables
- `composite.png`, `access_review.png` (arrivee sud [185, 356] -> seuil [130, 203])
- `manifest.json` : bouche {'x0': 86, 'x1': 174, 'y0': 119, 'y1': 197}, sentier, pieds, parametres

## Limites honnetes
Textures generees dans la DA PMD, pas des tuiles natives ; bouche/x et cadence
choisies ; animation proposee, pas cycle officiel ; pas de test PMDO/GPU ;
collisions et warp grotte a configurer moteur.

Reproduction : `.venv/bin/python source/aride_generee_v1/build.py` puis
`.venv/bin/python source/aride_generee_v1/package.py` (les tests tournent avant le ZIP).
