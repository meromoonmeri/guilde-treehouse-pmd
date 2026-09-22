# Banque de textures canoniques — inventaire

Atlas PNG 1:1 (alpha droit) décodés depuis les feuilles natives `.tile` conservées dans le dépôt, dédoublonnés par SHA-256. Les vignettes de `planches/` sont réduites : ne pas les importer.

Reconstruction : `.venv/bin/python tools/banque_canonique.py` · lecture/rendu : `tools/pmdo_tiles.py`.

## Feuilles natives

| Famille | Feuille | Tuile | Tuiles | Atlas (px) | Provenance | Source dans le dépôt |
|---|---|---:|---:|---|---|---|
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Base](atlas/Altere_Pond_Base.png) | 8 | 11044 | 928×768 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Base.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Cliffs](atlas/Altere_Pond_Cliffs.png) | 8 | 1840 | 928×456 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Cliffs.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Fringe](atlas/Altere_Pond_Fringe.png) | 8 | 2075 | 928×664 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Fringe.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Objects](atlas/Altere_Pond_Objects.png) | 8 | 4601 | 928×768 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Objects.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Objects_Over](atlas/Altere_Pond_Objects_Over.png) | 8 | 144 | 592×296 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Objects_Over.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Objects_Under](atlas/Altere_Pond_Objects_Under.png) | 8 | 841 | 928×768 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Objects_Under.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_River](atlas/Altere_Pond_River.png) | 8 | 1036 | 680×480 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_River.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_River_Animations](atlas/Altere_Pond_River_Animations.png) | 8 | 4236 | 1368×480 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_River_Animations.tile` |
| Altere Pond (étang, falaises sable, cascade) | [Altere_Pond_Shadows](atlas/Altere_Pond_Shadows.png) | 8 | 56 | 928×656 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/antre_harmonie_v3/references/Altere_Pond_Shadows.tile` |
| Crooked Cavern (entrée de grotte) | [Halcyon__Crooked_Cavern_Base](atlas/Halcyon__Crooked_Cavern_Base.png) | 8 | 1200 | 320×240 | Halcyon da6c2130 (Palikadude/Halcyon) | `source/cote_v5_expeditions/references/Halcyon__Crooked_Cavern_Base.tile` |
| Crooked Cavern (entrée de grotte) | [Halcyon__Crooked_Cavern_Objects](atlas/Halcyon__Crooked_Cavern_Objects.png) | 8 | 116 | 288×240 | Halcyon da6c2130 (Palikadude/Halcyon) | `source/cote_v5_expeditions/references/Halcyon__Crooked_Cavern_Objects.tile` |
| Crooked Cavern (entrée de grotte) | [Halcyon__Crooked_Cavern_Shadows](atlas/Halcyon__Crooked_Cavern_Shadows.png) | 8 | 83 | 296×240 | Halcyon da6c2130 (Palikadude/Halcyon) | `source/cote_v5_expeditions/references/Halcyon__Crooked_Cavern_Shadows.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [AppleWoods](atlas/AppleWoods.png) | 24 | 1233 | 1200×4800 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/dungeon_autotiles_v1/references/assets/AppleWoods.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [BeachCave](atlas/BeachCave.png) | 24 | 1596 | 1200×5952 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/dungeon_autotiles_v1/references/assets/BeachCave.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [CrystalCave1](atlas/CrystalCave1.png) | 24 | 716 | 1200×2496 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/CrystalCave1.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [DarkCrater](atlas/DarkCrater.png) | 24 | 3742 | 1200×12264 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/DarkCrater.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [MurkyForest](atlas/MurkyForest.png) | 24 | 623 | 1200×2112 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/MurkyForest.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [QuicksandCave](atlas/QuicksandCave.png) | 24 | 2377 | 1200×9408 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/QuicksandCave.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [SealedRuin](atlas/SealedRuin.png) | 24 | 153 | 1200×192 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/SealedRuin.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [SkyPeak4thPass](atlas/SkyPeak4thPass.png) | 24 | 340 | 1200×960 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/SkyPeak4thPass.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [SouthernCavern1](atlas/SouthernCavern1.png) | 24 | 1247 | 1200×4800 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/SouthernCavern1.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [SouthernJungle](atlas/SouthernJungle.png) | 24 | 905 | 1200×3264 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/SouthernJungle.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [SteamCave](atlas/SteamCave.png) | 24 | 1189 | 1200×4416 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/SteamCave.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [TreeshroudForest1](atlas/TreeshroudForest1.png) | 24 | 1234 | 1200×4800 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/TreeshroudForest1.tile` |
| Donjons PMDO — autotiles 24 px (DTEF 47 cases) | [VastIceMountain](atlas/VastIceMountain.png) | 24 | 158 | 1200×192 | PMDO DumpAsset 3e767571 (audinowho/DumpAsset) | `source/donjons_dtef_v2/references/DumpAsset/Content/Tile/VastIceMountain.tile` |
| EoSO — Brine Cave / Drenched Bluff (entrées) | [ExplorersOfSkyOrigins__Brine_Cave_Entrance](atlas/ExplorersOfSkyOrigins__Brine_Cave_Entrance.png) | 24 | 8505 | 9720×504 | Explorers of Sky Origins (EoSO) | `source/cote_v5_expeditions/references/ExplorersOfSkyOrigins__Brine_Cave_Entrance.tile` |
| EoSO — Brine Cave / Drenched Bluff (entrées) | [ExplorersOfSkyOrigins__DrenchedBluffEntranceBackground](atlas/ExplorersOfSkyOrigins__DrenchedBluffEntranceBackground.png) | 8 | 3366 | 528×408 | Explorers of Sky Origins (EoSO) | `source/cote_v5_expeditions/references/ExplorersOfSkyOrigins__DrenchedBluffEntranceBackground.tile` |
| EoSO — Brine Cave / Drenched Bluff (entrées) | [ExplorersOfSkyOrigins__DrenchedBluffEntranceDetails](atlas/ExplorersOfSkyOrigins__DrenchedBluffEntranceDetails.png) | 8 | 1674 | 528×408 | Explorers of Sky Origins (EoSO) | `source/cote_v5_expeditions/references/ExplorersOfSkyOrigins__DrenchedBluffEntranceDetails.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Cascades_Metano_Exact](atlas/Cascades_Metano_Exact.png) | 8 | 544 | 256×136 | Construit par ce dépôt (voir README du dossier source) | `sprites/eau_metano/Cascades_Metano_Exact.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Extension_Metano](atlas/Extension_Metano.png) | 8 | 4864 | 512×608 | Construit par ce dépôt (voir README du dossier source) | `sprites/falaises_metano/Extension_Metano.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Falaises_Metano_Modules](atlas/Falaises_Metano_Modules.png) | 8 | 3000 | 400×480 | Construit par ce dépôt (voir README du dossier source) | `sprites/falaises_modulaires_v2/Falaises_Metano_Modules.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Falaises_V2_Decor](atlas/Falaises_V2_Decor.png) | 8 | 2368 | 512×296 | Construit par ce dépôt (voir README du dossier source) | `sprites/falaises_modulaires_v2/decor/Falaises_V2_Decor.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Maisons_Metano_jour](atlas/Maisons_Metano_jour.png) | 8 | 2240 | 560×256 | Construit par ce dépôt (voir README du dossier source) | `sprites/maisons_metano/Maisons_Metano_jour.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Maisons_Metano_nuit](atlas/Maisons_Metano_nuit.png) | 8 | 2240 | 560×256 | Construit par ce dépôt (voir README du dossier source) | `sprites/maisons_metano/Maisons_Metano_nuit.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Maisons_Organiques_V2_jour](atlas/Maisons_Organiques_V2_jour.png) | 8 | 2240 | 560×256 | Construit par ce dépôt (voir README du dossier source) | `sprites/maisons_organiques_v2/Maisons_Organiques_V2_jour.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Maisons_Organiques_V2_nuit](atlas/Maisons_Organiques_V2_nuit.png) | 8 | 2240 | 560×256 | Construit par ce dépôt (voir README du dossier source) | `sprites/maisons_organiques_v2/Maisons_Organiques_V2_nuit.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Metano_Canonique_8px](atlas/Metano_Canonique_8px.png) | 8 | 10624 | 512×1328 | Construit par ce dépôt (voir README du dossier source) | `sprites/metano_pixel_perfect/Metano_Canonique_8px.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_jour_1](atlas/Ponts_Dores_jour_1.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_jour_1.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_jour_2](atlas/Ponts_Dores_jour_2.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_jour_2.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_jour_4](atlas/Ponts_Dores_jour_4.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_jour_4.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_nuit_1](atlas/Ponts_Dores_nuit_1.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_nuit_1.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_nuit_2](atlas/Ponts_Dores_nuit_2.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_nuit_2.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Ponts_Dores_nuit_4](atlas/Ponts_Dores_nuit_4.png) | 8 | 600 | 480×80 | Construit par ce dépôt (voir README du dossier source) | `sprites/ponts_pmdo/Ponts_Dores_nuit_4.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Riviere_Metano_Compacte](atlas/Riviere_Metano_Compacte.png) | 8 | 3904 | 128×1952 | Construit par ce dépôt (voir README du dossier source) | `sprites/eau_metano/Riviere_Metano_Compacte.tile` |
| Feuilles construites par ce dépôt (non natives, à ne pas confondre) | [Zones_Guidees_Canon_8px](atlas/Zones_Guidees_Canon_8px.png) | 8 | 9792 | 512×1224 | Construit par ce dépôt (voir README du dossier source) | `sprites/zones_guidees/Zones_Guidees_Canon_8px.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Floor](atlas/Guild_Second_Floor_Floor.png) | 8 | 2464 | 640×416 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Floor.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Fringe](atlas/Guild_Second_Floor_Fringe.png) | 8 | 9 | 600×280 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Fringe.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Objects](atlas/Guild_Second_Floor_Objects.png) | 8 | 747 | 608×392 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Objects.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Objects_Over](atlas/Guild_Second_Floor_Objects_Over.png) | 8 | 30 | 600×200 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Objects_Over.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Objects_Under](atlas/Guild_Second_Floor_Objects_Under.png) | 8 | 18 | 600×240 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Objects_Under.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Shadows](atlas/Guild_Second_Floor_Shadows.png) | 8 | 43 | 608×400 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Shadows.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Supports](atlas/Guild_Second_Floor_Supports.png) | 8 | 2596 | 672×448 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Supports.tile` |
| Halcyon — décors Ground divers | [Guild_Second_Floor_Walls](atlas/Guild_Second_Floor_Walls.png) | 8 | 987 | 608×256 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v3/references/Guild_Second_Floor_Walls.tile` |
| Halcyon — décors Ground divers | [Illuminant_Riverbed_Base](atlas/Illuminant_Riverbed_Base.png) | 8 | 1002 | 320×240 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/donjons_dtef_v2/references/Content/Tile/Illuminant_Riverbed_Base.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Animated](atlas/Ledian_Dojo_Animated.png) | 8 | 114 | 184×72 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Animated.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Ceiling](atlas/Ledian_Dojo_Ceiling.png) | 8 | 1293 | 408×312 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Ceiling.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Floor](atlas/Ledian_Dojo_Floor.png) | 8 | 923 | 336×312 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Floor.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Objects](atlas/Ledian_Dojo_Objects.png) | 8 | 179 | 320×312 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Objects.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Objects_Over](atlas/Ledian_Dojo_Objects_Over.png) | 8 | 46 | 304×200 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Objects_Over.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Objects_Under](atlas/Ledian_Dojo_Objects_Under.png) | 8 | 64 | 296×152 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Objects_Under.tile` |
| Halcyon — décors Ground divers | [Ledian_Dojo_Shadows](atlas/Ledian_Dojo_Shadows.png) | 8 | 105 | 296×248 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/ledian_dojo_v1/references/Ledian_Dojo_Shadows.tile` |
| Halcyon — décors Ground divers | [Relic_Forest_Base](atlas/Relic_Forest_Base.png) | 8 | 5625 | 600×600 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/donjons_dtef_v2/references/Content/Tile/Relic_Forest_Base.tile` |
| Métano Café (intérieur) | [Metano_Town_Cafe_Base](atlas/Metano_Town_Cafe_Base.png) | 8 | 2280 | 456×320 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/Metano_Town_Cafe_Base.tile` |
| Métano Café (intérieur) | [Metano_Town_Cafe_Objects](atlas/Metano_Town_Cafe_Objects.png) | 8 | 629 | 432×320 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/Metano_Town_Cafe_Objects.tile` |
| Métano Café (intérieur) | [Metano_Town_Cafe_Objects_Fringe](atlas/Metano_Town_Cafe_Objects_Fringe.png) | 8 | 7 | 424×216 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/Metano_Town_Cafe_Objects_Fringe.tile` |
| Métano Café (intérieur) | [Metano_Town_Cafe_Objects_Over](atlas/Metano_Town_Cafe_Objects_Over.png) | 8 | 148 | 408×296 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/Metano_Town_Cafe_Objects_Over.tile` |
| Métano Café (intérieur) | [Metano_Town_Cafe_Objects_Under](atlas/Metano_Town_Cafe_Objects_Under.png) | 8 | 138 | 408×296 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/Metano_Town_Cafe_Objects_Under.tile` |
| Métano Café (intérieur) | [SpindaCafe1](atlas/SpindaCafe1.png) | 8 | 4959 | 696×456 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/SpindaCafe1.tile` |
| Métano Café (intérieur) | [SpindaCafe2](atlas/SpindaCafe2.png) | 8 | 835 | 560×320 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cafe_multietage_v1/references/SpindaCafe2.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Animation_Tileset](atlas/Metano_Town_Animation_Tileset.png) | 8 | 4367 | 512×1408 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Base](atlas/Metano_Town_Base.png) | 8 | 35646 | 1512×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Metano_Town_Base.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Base](atlas/Metano_Town_Base.png) | 8 | 35646 | 1512×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/falaises_metano/natifs/Metano_Town_Base.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Base_Night](atlas/Metano_Town_Base_Night.png) | 8 | 35646 | 1512×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cote_v4_abyss/natifs/Metano_Town_Base_Night.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Cliffs](atlas/Metano_Town_Cliffs.png) | 8 | 2169 | 1512×544 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cote_v4_abyss/natifs/Metano_Town_Cliffs.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Cliffs_Night](atlas/Metano_Town_Cliffs_Night.png) | 8 | 2169 | 1512×544 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cote_v4_abyss/natifs/Metano_Town_Cliffs_Night.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Fringe](atlas/Metano_Town_Fringe.png) | 8 | 135 | 1064×1144 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cote_v4_abyss/natifs/Metano_Town_Fringe.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Fringe_Night](atlas/Metano_Town_Fringe_Night.png) | 8 | 135 | 1064×1144 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/cote_v4_abyss/natifs/Metano_Town_Fringe_Night.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_Objects](atlas/Metano_Town_Objects.png) | 8 | 16766 | 1512×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Metano_Town_Objects.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_River_Animation_1](atlas/Metano_Town_River_Animation_1.png) | 8 | 3204 | 1136×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_River_Animation_1.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_River_Animation_2](atlas/Metano_Town_River_Animation_2.png) | 8 | 3204 | 1136×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_River_Animation_2.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_River_Animation_3](atlas/Metano_Town_River_Animation_3.png) | 8 | 3204 | 1136×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_River_Animation_3.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_River_Animation_4](atlas/Metano_Town_River_Animation_4.png) | 8 | 3204 | 1136×1512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_River_Animation_4.tile` |
| Métano Town (village côtier, falaises ocre, rivière) | [Metano_Town_River_Sparkles](atlas/Metano_Town_River_Sparkles.png) | 8 | 128 | 40×224 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/eau_metano/natifs/Metano_Town_River_Sparkles.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Base](atlas/Vast_Steppe_Base.png) | 8 | 4096 | 512×512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Base.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Cliifs](atlas/Vast_Steppe_Cliifs.png) | 8 | 697 | 512×280 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Cliifs.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Flower_Animations](atlas/Vast_Steppe_Flower_Animations.png) | 8 | 27 | 72×24 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Flower_Animations.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Fringe](atlas/Vast_Steppe_Fringe.png) | 8 | 959 | 512×512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Fringe.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Objects](atlas/Vast_Steppe_Objects.png) | 8 | 689 | 512×512 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Objects.tile` |
| Vast Steppe (plaine, rampe herbeuse, fleurs animées) | [Vast_Steppe_Objects_Under](atlas/Vast_Steppe_Objects_Under.png) | 8 | 135 | 504×488 | Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy) | `source/amp_plains_fleurie_v1/references/Vast_Steppe_Objects_Under.tile` |

## Cartes natives rendues (phase 0, feuilles disponibles seulement)

| Carte | Nom | TexSize | Cellules | Pixels | Calques | Feuilles manquantes |
|---|---|---:|---|---|---|---|
| [vast_steppe_entrance.rsground](cartes_natives/vast_steppe_entrance.png) | Vast Steppe Entrance | 1 | 64×64 | 512×512 | Base, Cliffs, Objects Under, Objects, Fringe | — |
| [altere_pond.rsground](cartes_natives/altere_pond.png) | Altere Pond | 1 | 116×96 | 928×768 | Base, River, Cliffs, Shadows, Objects Under, Objects, Objects Over, Fringe | — |
| [metano_cafe.rsground](cartes_natives/metano_cafe.png) | Metano Café | 1 | 57×40 | 456×320 | Base, Objects Under, Objects, Objects Over, Fringe | — |
| [spinda_cafe.rsground](cartes_natives/spinda_cafe.png) | Spinda Cafe | 1 | 87×57 | 696×456 | Background, Decorations | — |
| [guild_second_floor.rsground](cartes_natives/guild_second_floor.png) | Guild Second Floor | 1 | 84×56 | 672×448 | Floor, Walls, Objects Under, Objects, Objects Over, Shadows, Fringe, Supports | — |
| [ExplorersOfSkyOrigins__Brine_Cave_Entrance.rsground](cartes_natives/ExplorersOfSkyOrigins__Brine_Cave_Entrance.png) |  | 3 | 27×21 | 648×504 | New Layer | — |
| [ExplorersOfSkyOrigins__drenched_bluff_entrance.rsground](cartes_natives/ExplorersOfSkyOrigins__drenched_bluff_entrance.png) |  | 1 | 66×51 | 528×408 | Background, Details | — |
| [Halcyon__crooked_cavern_entrance.rsground](cartes_natives/Halcyon__crooked_cavern_entrance.png) | Crooked Cavern Entrance | 1 | 40×30 | 320×240 | Base, Objects, Shadows | — |
| [ledian_dojo.rsground](cartes_natives/ledian_dojo.png) | Ledian Dojo | 1 | 51×39 | 408×312 | Floor, Objects Under, Objects, Objects Over, Shadows, Ceiling | — |
| [cliffdaytest.rsground](cartes_natives/cliffdaytest.png) | CliffReverietownnordest | 1 | 123×99 | 984×792 | New Layer, Layer 2, Layer 2, Layer 4, Layer 3, Cloud/nuage | 00_ciel, CanyonCamp, v2_promontoire_jour_03, 13_avancee_basse_gauche_terrain, INVERSEPATHWAY, CLIFF MIROR-Photoroom, P01P01A_layer1, , Metano_Town_Animated, 01_long_cap_jour_02, Metano_Town_Trimmed, Metano_Inn_Objects |
| [cliffnordouesttest1.rsground](cartes_natives/cliffnordouesttest1.png) |  | 1 | 138×98 | 1104×784 | Layer 2, Layer 1, New Layer, Layer 3 | 00_ciel, v2_promontoire_jour_03, terrain, Metano_Altere_Transition_Base, terrain (4), terrain (3), terrain (2), INVERSEPATHWAY |

## Références PNG canoniques fournies par l’utilisateur (racine du dépôt)

| Fichier | Taille |
|---|---|
| `arenapmdskybeach.png` | 456×480 |
| `aurorepmdsky.png` | 264×216 |
| `bassinchauffantpmdsky.png` | 504×408 |
| `bgnightbackgroundpmdskyda.png` | 456×240 |
| `entrancearidedungeonpmdsky.png` | 408×288 |
| `forêtglomypmdsky.png` | 600×312 |
| `iceroadpmdsky.png` | 504×360 |
| `interiorbedroompmdsky.png` | 504×384 |
| `junglewaterfallzonepmdsky.png` | 744×1032 |
| `lakecrystalpmdsky.png` | 696×600 |
| `large.P27P01A.png.c5ad9818930eb0d4f403f64607318c37.png` | 360×312 |
| `large.S01P03A.png.84e22fb77c4061e77b0f546545fed2c7.png` | 456×456 |
| `large.S05P03A.png.301f7a1eadda348357be0801e81faa2a.png` | 312×720 |
| `oldcastlepmd.png` | 408×408 |
| `pmdskyicearena.png` | 504×408 |
| `roadundergound.png` | 504×408 |
| `rockgeyserlike.png` | 456×528 |
| `rockroadpmd.png` | 624×288 |
| `secretgarden.png` | 408×408 |
| `starcavepmdsky.png` | 1008×504 |
| `undergroundpmd.png` | 816×408 |
| `energeticforest.png` | 480×336 |
| `finalisland.png` | 480×312 |
| `witheringdesert.png` | 456×336 |
| `DSVFS.png` | 702×466 |
| `Amp_Plains_entrance_TD.png` | 456×408 |
| `Apple_Woods_entrance_TDS.png` | 552×408 |
| `Dark_Crater_Pit_TDS.png` | 552×576 |
| `Dark_Crater_entrance_TDS.png` | 360×456 |
| `Foggy_Forest_Base_Camp_TDS.png` | 600×792 |
| `Mt_Bristle_entrance_TD.png` | 552×480 |
| `Mt_Horn_entrance_Sky.png` | 552×360 |
| `Mystifying_Forest_entrance_TDS.png` | 600×504 |
| `Sealed_Ruin_entrance_TDS.png` | 600×384 |
| `Sealed_Ruin_pit_TDS.png` | 648×528 |
| `Southern_Jungle_entrance_S.png` | 504×432 |
| `Southern_Jungle_exit_2_S.png` | 600×456 |
| `Southern_Jungle_exit_S.png` | 504×456 |
| `Steam_Cave_Peak_TDS.png` | 648×624 |
| `Steam_Cave_entrance_TDS.png` | 504×440 |
| `Underground_Lake_shore_TDS.png` | 600×600 |
| `Waterfall_Cave_gem_TDS.png` | 504×432 |
| `Waterfall_Cave_ledge_TDS.png` | 408×552 |
| `DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Sky - Maps - Murky Forest & Armaldo House.png` | 1162×697 |
| `DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Time _ Darkness - Backgrounds - Beach & Path to Beach.png` | 1650×990 |
| `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Mt. Thunder.png` | 432×498 |
| `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Northern Range.png` | 456×432 |
| `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest.png` | 857×372 |
| `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Mushroom Forest.png` | 456×445 |
| `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png` | 456×312 |
