# Previews GIF

- `reve_personnalite.gif` — 640 × 360, 120 images, 10 fps, 12 s. Capture du vrai rendu WebGL : deux validations puis deux retours montrent le déplacement de la sphère, l’alternance gauche/droite et la parallaxe. Le déroulé automatique n’existe que dans cet export de démonstration ; le test réel attend toujours le joueur.
- `falaise_guilde_eos.gif` — 480 × 428, 32 images, 4 fps, 8 s. La falaise de guilde après sa reprise complète au générateur, successivement en jour et nuit. La bande basse est une légende de preview, pas une partie du calque de jeu.

Les GIF sont des aperçus compressés ; les fichiers HTML autonomes et les PNG/Aseprite/Tiled conservent la qualité de travail. Les captures intermédiaires restent dans `.cache/` et ne sont pas poussées.

Reconstruction : `python source/export_previews_gif.py`, avec Playwright/Chromium et imageio-ffmpeg installés.

## Zones Treasure Town — layouts et calques créés séparément

Ces aperçus remplacent les anciennes captures nettoyées. Chaque GIF montre six secondes de jour puis six secondes de nuit.

- [Cap des Alizés](littoral_jour_nuit.gif) — 384 × 317.
- [Prairies suspendues](plateaux_jour_nuit.gif) — 384 × 335.
- [Clairière des sources](etang_jour_nuit.gif) — 320 × 312.
- [Ressauts célestes](cascades_jour_nuit.gif) — 384 × 312.
- [Démonstration du palette cycling](palette_cycling_tt.gif) — indices immobiles à gauche, palette animée à droite.

Les cartes d’indices et palettes sont livrées avec les PNG, les Aseprite indexés et les compositions Aseprite/Tiled. Génération des GIFs : `python source/export_nouveaux_gifs.py` puis `python source/export_palette_demo.py`.
