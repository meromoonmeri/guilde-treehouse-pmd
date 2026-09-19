# Structures Métano Town / Treasure Town — lot V1 + carte village terminée

Huit sprites de structures extraits **pixel-par-pixel** des feuilles canoniques des
dépôts de référence, puis une carte village terminée (terrain natif + calque
structures). Aucun pixel n'est généré, recoloré, retourné ou rééchantillonné : on
extrait, on détouré, on réassemble.

## Provenance

- **Palikadude/Halcyon** (master `da6c2130`) : feuilles `Metano_*` (style Métano, 8 px).
- **Minemaker0430/ExplorersOfSkyOrigins** (main `bed9449`) : `TreasureTownEast/West.tile`,
  `GuildOutside.tile`, `GuildOutsideNight.tile`, `treasure_town.rsground`,
  `guild_outside.rsground` (style Treasure Town / Guilde, 24 px).
- **audinowho/PMDODump** : utilisé comme référence de *format/données* PMDO
  (schémas, DataGenerator), pas comme source de pixels.

`provenance.json` fige le commit, le chemin et le **sha256** de chaque fichier de
référence ; `test_build.py` vérifie que les copies locales sont byte-identiques.

## Structures livrées (grille 24 px)

| id | libellé | style |
|----|---------|-------|
| kangaskhan_reserve | Réserve Kangaskhan | Treasure Town |
| kecleon_boutique | Boutique Kecleon | Treasure Town |
| xatu_expertise | Expertise Xatu | Treasure Town |
| duskull_banque | Banque Duskull | Treasure Town |
| electivire_liaison | Liaison Élekable | Treasure Town |
| marowak_dojo | Dojo Ossatueur | Treasure Town |
| guilde_qg | QG de la Guilde (jour) | Guilde / Treasure Town |
| guilde_qg_nuit | QG de la Guilde (nuit) | Guilde / Treasure Town |

Fichiers : `individuels/StructureTT_<id>.png`, atlas `Structures_TreasureTown_atlas.png`,
manifeste `manifest.json` (rectangles atlas, tailles, placements).

## Méthode de détourage

Le sol (herbe / chemin / ciel / roche) est rendu transparent par **propagation depuis
les bords** : seuls les pixels de sol *connectés au bord* et proches des couleurs des
bords sont retirés. Les pixels des bâtiments sont conservés tels quels. La variante
nuit du QG réutilise exactement le masque alpha du jour (géométrie identique vérifiée).

## Carte village terminée

`map/village_00_terrain.png` (herbe + chemin reconstruits à partir de tuiles de sol
natives 24 px), `map/village_01_structures.png` (calque structures), `map/village_composite.png`.
Tiled : `map/village.tmx` (calque terrain en tuiles + calque structures en objets) et
`map/village_sol.tsx` / `map/village_sol_2tiles.png`.

## Reconstruction et tests

```sh
python source/structures_metano_treasure_v1/build.py
python source/structures_metano_treasure_v1/test_build.py
```

Le test re-extrait chaque sprite et vérifie : pixels canoniques identiques au rendu de
référence, alignement 24 px, géométrie nuit == jour, atlas recomposable, carte
recomposable (composite == terrain+structures), TMX/TSX valides et objets existants,
références byte-intactes.

## Limites

Pas d'import PMDO réel, pas de collisions / warps / occlusion configurés, appréciation
artistique non certifiée. Les terrains créés entre le 13 et le 17 septembre sont
considérés **validés** ; cette livraison ajoute les structures et termine la carte.
Ressources natives © leurs auteurs ; voir crédits dans `manifest.json`.
