# Forêt 928×1152 — sud → grotte nord (multicalque 10 layers)

**Taille:** 928×1152 px = 116×144 cases de 8 px  
**Orientation:** SUD (arrivée 432,1144 64×8 au bas) → NORD grotte (478,100)  
**Grille:** 8 px, cases 8×8, tous les PNG divisibles  
**Méthode:** textures **100% canoniques**, aucun pixel généré — générateur uniquement comme inspiration de layout, reconstruction pixel-exacte avec `NPZ source_sxy`  
**Viewer:** `apercu_foret_grotte_928_v1.html` à la racine — toggle calques jour/nuit, grille, composite, trajet

## Calques (10) — jour et nuit

| # | id | fichier jour | fichier nuit | source |
|---|---|---|---|---|
|1|01_soil|Foret928_forest_cave_928_01_soil.png|Foret928_NUIT_01_soil.png|forêtglomypmdsky 0,144-176 patch quilting |
|2|02_continuous_earth_path|…02…|NUIT|terre pure extraite sans frange verte, 72px large, continu sud→entrée |
|3|03_north_canopy|…|NUIT|canopée haute 0-144, masque foliage (G>R, sat) |
|4|04_white_cliff|…|NUIT|falaise blanche 288,0,600,216 masquée + retours 64px |
|5|05_cave_opening|…|NUIT|bouche grotte polygonale dans falaise |
|6|06_tree_trunks|…|NUIT|troncs Vast Steppe 72,160,120,216 |
|7|07_tree_canopies|…|NUIT|canopées Vast Steppe 16,96,160,216 |
|8|08_stones|…|NUIT|pierres 400,184,440,208 |
|9|09_cliff_foot_bushes|…|NUIT|buissons pied falaise 408,184,600,264 |
|10|10_foreground_bushes|…|NUIT|premier plan bas 0,184,240,312 |

Chaque PNG a son `*_source.npz` (`source_sxy[y,x]=[source_index, x_source, y_source]`, -1 si transparent) et son `.tsx` 8×8. Recomposition des 10 calques = `composite.png` (jour) et `composite_nuit.png` (nuit) octet-exact vérifié.

## Provenance
- `forêtglomypmdsky.png` (600×312) — commit 9ec9a081, SHA préservé
- `Vast Steppe` Halcyon 1522c7a — `vast_steppe_layer_3.png` (troncs) + `layer_4.png` (foliage)
- Pas de rotation/miroir/échelle/recoloration jour. Nuit = filtre **Abyss V4 exact** `tools/tile_night.py` blob `438383f4` (une seule application): gris 0.299/0.587/0.114, k=0.20+0.30*lum, sat 0.95, x0.52/0.70/1.60 +6*lum.

## Vérifications
`python3 source/foret_grotte_928_v1/verify.py` → PASS:
- dimensions 928×1152, grille 8px, orientation S→N, entrée nord <250, accès sud 1144
- chemin continu entre entrée et sud (masque binaire 1px/row)
- 10 layers, chaque pixel opaque == pixel source exact (200 échantillons/layer)
- recomposition == composite (jour et nuit)
- zéro magenta résiduel (d<40)
- TSX 8×8 présents
- Pas de test PMDO/runtime, art non approuvé, collisions non fournies — masque ≠ collision moteur

## Usage Tiled / PMDO
Importer chaque PNG en **8 px** (PNG to Tileset) ou utiliser les TSX fournis. Ordre d'empilement: 01 sol → 10 premier plan. Entrée grotte en 05, chemin en 02. Collisions à dessiner: herbe/chemin praticable, falaises/arbres bloqués, seuil 32×16 à (462,92).

## Reproduction
```bash
python3 source/foret_grotte_928_v1/build.py
python3 source/foret_grotte_928_v1/verify.py
python3 source/foret_grotte_928_v1/build_night.py
```
ZIP: `foret_grotte_928_v1_pack.zip` (PNG + NPZ + TSX + composites + manifests + viewer partiel)

Généré d'après références PMD Sky / Halcyon — textures natives, layout nouveau. Autres zones ouvertes, runtime PMDO NON TESTÉ.
