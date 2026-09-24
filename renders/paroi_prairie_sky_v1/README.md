# Paroi + prairie Sky Peak — layer unique 1008×176 natif

Bande falaise + prairie en **un seul calque** : bande GIF native y328..504
(504×176, fleurs retirées par infill 4 frames), carrelée en miroir [F][M(F)].
Joint unique à x=504, continu par colonne dupliquée. 100% pixels natifs 1×.

- `paroi_prairie_1008x176_jour.png` / `..._nuit.png` (Abyss exact)
- `PLANCHE_PAROI_NE_PAS_IMPORTER.png` : jour/nuit + joints 2x
- Fleurs exclues (couche séparée, voir vista) ; symétrie miroir assumée.

Vérifications (`verification.json`, PASS) : égalité native exhaustive,
joint continu, nuit exacte. Limites : pas de test PMDO/GPU. Reproduction :
`source/paroi_prairie_sky_v1/{build,verify}.py`.
