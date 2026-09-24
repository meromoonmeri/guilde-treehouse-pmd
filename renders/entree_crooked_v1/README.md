# Entrée grotte v1 — paroi Crooked générée + compléments natifs Halcyon/Sky Peak

Carte 848×1264 sud→nord (canevas = brut G1b 1:1) : bouche au nord (424, ~450),
parvis sableux en entonnoir, chemin au sud, prairie Sky Peak, 4 arbres Halcyon,
4 rochers Crooked, 22 fleurs Sky Peak animées (4 phases natives @200 ms).

## Généré vs natif (étiquetage strict)

- **GÉNÉRÉ** (brut `source/entree_crooked_v1/bruts/G1b_paroi_bouche.png`, style Crooked,
  plan + ref native en guides) : `02_chemin_sable`, `03_paroi`, `04_bouche`, par
  masques matière (règles dans `manifest.json → masques`), translation nulle.
  Redessiné d'après références, jamais « natif ».
- **NATIF** (translation seule, vérifié pixel à pixel) : `01_sol_herbe` (patches
  24×16 du GIF sommet Sky Peak, quiltés sans fondu), `05_rochers` (Crooked
  Objects+Shadows, 4 modules V1), `06_fleurs` (applewoods `fleur_sky_*`, 10
  sprites × 4 phases), `07_troncs` + `08_canopées` (Vast Steppe L3/L4, couple V3).
- Rejetée : G1 (double paroi barrant le chemin), conservée dans `bruts/rejetes/`.

## Fichiers

`EntreeCrookedV1_<calque>_<jour|nuit>.png` (origine commune), phases fleurs
`_phase1..3`, `composite_{jour,nuit}.png`, `composite_phase{0..3}_jour.png`,
`entreecrookedv1.ora`, `manifest.json`, `verification.json` (47 PASS).
Galerie : `apercu_entree_crooked_v1.html` (calques, jour/nuit, fleurs animées).

Nuit = Abyss exact, une fois par calque. Chemin sud→bouche connecté (masque
pixel, pas une collision moteur). **PMDO non testé, art non approuvé.**

Reconstruction : `source/entree_crooked_v1/{build,verify,make_gallery}.py`.
Méthode et audit : `source/entree_crooked_v1/AUDIT.md`.
