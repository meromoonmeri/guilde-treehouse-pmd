# Plage falaises rouges V2 — eau canonique EoSO (17 frames natives)

**Demande** : mer/texture d'eau comme les maps *beach* de [Minemaker0430/ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins).

## Ce qui change vs V1

- **Eau = ressource native décodée** de `Content/Tile/beach_animation.tile` (17 frames de 792×168, cadence native `FrameLength=16` ticks ≈ **266 ms**). Réécodage pixel-exact vérifié par relecture (test 06), hash SHA-256 dans `manifest.json`.
- **Animation récupérée, pas proposée** : les 17 phases sont celles de la map beach EoSO. Boucle native.
- Adaptation à notre crique : **row natif = hauteur−1 − distance au sable** (transformée EDT). La bande « écume + sable » n'arrive qu'au contact de notre rivage ; contre les falaises, la mer montre ses rangs d'eau — le raccord observé dans les maps EoSO. Sélection par pixel, **aucune déformation** (pas d'étirement/rotation/miroir/recoloration).
- Terrain : **byte-identique au lot V1** (composition hybride générée+palette), testé (test 04).

## Contenu

- `apercu_plage_rouge_v2.html` (racine) et `renders/plage_rouge_v2_eoso/apercu.html` — viewer (17 frames, calques, sèche, grille, zoom).
- `couches/` : `00_fond_void`, `02_sable`, `03_parois_falaises`, `04_bordures_herbe`, `05_ombres_objets`, `06_objets` (= V1) + `mer_frames/MerV2_00..16.png` (eau native adaptée).
- `canonique/mer_natif_00..16.png` : les 17 bandes natives pixel-exactes (792×168).
- `scene/scene_eoso_00..16.png`, `scene_seche.png`, `scene_eoso17f.webp` (lossless), `review/scene_eoso.gif`, `review/frames_mer_eoso_zoom_1x.png`.
- `ora/plage_rouge_v2_eoso.ora` (23 calques).
- `source/plage_rouge_v2/references/` : copie du `.tile` + `provenance.json` (commit EoSO épinglé, SHA-256).

## Limites

- Silhouette = notre crique (pas le layout de la map beach EoSO) ; le mapping par distance est une adaptation documentée, pas une déclaration d'équivalence au rendu de la map d'origine.
- Art non approuvé ; collisions/warps/runtime PMDO **NON TESTÉS**.
- Terrain V1 = pixels générés quantifiés (méthode hybride) ; seule la mer est native.

Reproduction : `.venv/bin/python source/plage_rouge_v2/build.py && .venv/bin/python source/plage_rouge_v2/test_build.py` (18 tests).

Références : EoSO © Minemaker0430 ; artworks originaux PMD © Pokémon/Nintendo/Creatures/GAME FREAK/Chunsoft — usage d'étude fan-project.
