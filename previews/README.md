# Previews GIF

- `reve_personnalite.gif` — 640 × 360, 120 images, 10 fps, 12 s. Capture du vrai rendu WebGL : deux validations puis deux retours montrent le déplacement de la sphère, l’alternance gauche/droite et la parallaxe. Le déroulé automatique n’existe que dans cet export de démonstration ; le test réel attend toujours le joueur.
- `falaise_guilde_eos.gif` — 480 × 428, 32 images, 4 fps, 8 s. La falaise de guilde après sa reprise complète au générateur, successivement en jour et nuit. La bande basse est une légende de preview, pas une partie du calque de jeu.

Les GIF sont des aperçus compressés ; les fichiers HTML autonomes et les PNG/Aseprite/Tiled conservent la qualité de travail. Les captures intermédiaires restent dans `.cache/` et ne sont pas poussées.

Reconstruction : `python source/export_previews_gif.py`, avec Playwright/Chromium et imageio-ffmpeg installés.

## Nouvelles références de paysages

Chaque GIF présente six secondes de jour puis six secondes de nuit. Les images identiques peuvent être regroupées par l’encodeur sans modifier la durée totale de 12 s.

- [Cap du large](littoral_jour_nuit.gif) — 384 × 264, pleine lune et reflets nocturnes.
- [Plateaux fleuris](plateaux_jour_nuit.gif) — 384 × 408, terrain fixe et étoiles nocturnes.
- [Étang de la forêt](etang_jour_nuit.gif) — 320 × 462, cascades et reflets.
- [Cascades célestes](cascades_jour_nuit.gif) — 384 × 315, flux séparés du terrain.

Les légendes et marges de GIF ne font pas partie des PNG de jeu. Reconstruction : `python source/export_nouveaux_gifs.py`.
