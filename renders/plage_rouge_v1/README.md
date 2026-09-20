# Plage falaises rouges V1 — map « arenapmdskybeach » (plage canonique PMD Sky)

**Demandes** : produire la map de la plage entre falaises rouges (référence `arenapmdskybeach.png`, audit `exports/zones_bg_audit_v1`) avec les **textures canoniques**, en **méthode hybride**, en **version sèche + version animée**, livraison **standard**.

## Contenu

- `apercu_plage_rouge_v1.html` (à la racine) : viewer hors-ligne — calques activables, animation 16 frames, version sèche, grille 8 px, zoom, changement de fond, export PNG.
- `couches/` : calques alignés 344×512 (RGBA) :
  - `00_fond_void.png` — fond sombre (39,39,55) de la référence, option dans le viewer ;
  - `mer_frames/MerV1_00..15.png` — **16 frames** de mer (8 poses planche réordonnées + 8 fondus 50 %), silhouette maîtresse commune, 120 ms ;
  - `02_sable.png`, `03_parois_falaises.png`, `04_bordures_herbe.png` — terrain découpé par masques couleur (`review/masques_debug.png`) ;
  - `05_ombres_objets.png` — **ombres calculées** (ellipses alpha 72 sous les objets au sol), pas des textures natives ;
  - `06_objets.png` — rochers/plantes placés sur grille 8 px ;
  - `01_mer_pose_peinte.png` — pose de mer « peinte » générée en place (export statique).
- `scene/` : `scene_anim_00..15.png` + `scene_seche.png` (sans eau).
- `scene_anim16f.webp` (lossless, boucle) et `review/scene_anim.gif`.
- `exports/scene_pose_peinte.png` : composition statique avec la mer peinte.
- `sprites_pack/` : 11 sprites décoratifs individuels (extraits de la planche magenta, normalisés, quantifiés).
- `ora/plage_rouge_v1.ora` : OpenRaster 22 calques (frames mer cachées sauf f00).
- `review/` : palette native 147 couleurs, planches, masques debug, GIF de contrôle.
- `bruts/` : les 4 images générées sources (sha-256 dans `manifest.json`).

## Méthode (hybride)

1. Génération guidée par la référence canonique : terrain sur magenta (zone mer vide), mer générée en place, planche 2×4 de vagues (silhouette quasi identique par cellule), planche de 11 objets sur magenta.
2. Détourage par inondation magenta (pas de `fill_holes`, leçon V9), normalisation NEAREST au canvas 344×512 (ratio natif du brut, arrondi 8).
3. **Quantification chaque pixel opaque au plus proche des 147 couleurs natives de la référence (CIEDE2000)**. Audit dE moyen : sable 1,21 · mer 2,02–3,54 (voir `manifest.json › audit_palette`).
4. Animation : 8 poses de vague **réordonnées** par cycle Hamiltonien (saut max ramené de ~33 à 5,33 en différence RGB moyenne) + 8 fondus 50 % → boucle de 1,92 s.

## Limites explicites

- **Conformité palette ≠ preuve de motif** : zéro couleur hors palette ne valide ni raccords, ni qualité de tuile, ni art (leçon caps_terrasses_v4). Art NON approuvé.
- L'animation des vagues est **proposée**, pas le cycle officiel PMD récupéré.
- Ombres des objets = overlays calculés, pas des ombres natives ; objets générés puis quantifiés, pas des tiles canoniques.
- Collisions, warps, import/runtime PMDO : **NON TESTÉS** (niveau E du protocole non atteint).
- Sème/terrain : la pose peinte `mer_f0` est vérifiée alignée sur le terrain (ratio diff 1,07 %), sinon elle aurait été écartée de l'animé.

Reconstruction : `.venv/bin/python source/plage_rouge_v1/build.py` puis `test_build.py` (19 tests) puis `package.py`.

Référence : captures PMD © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft — usage d'étude du fan-project.
