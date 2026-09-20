# Beach Sud — agrandissement natif pixel-perfect de la plage EoSO

**Demande** : même plage que `beach.rsground` (ExplorersOfSkyOrigins), mais **plus grande**, avec **plage au sud** (touche la limite de carte) et **ciel jour/nuit** séparé. **Même visuel, même texture, jamais inventée** — méthode native par calques, pas génération.

**Référence** : `Minemaker0430/ExplorersOfSkyOrigins` commit `bed9449` (16 sep 2026), `Data/Ground/beach.rsground` version `0.8.11.0`, `TexSize 3` → cellules 24 px, map d'origine `792×384` (33×16), 3 layers `Back`/`Anim`/`Front` avec sheets `D01P11A_layer1` / `beach_animation` / `D01P11A_layer2`. Hashes et provenance dans `provenance.json`.

**Méthode reproduite exactement comme l'agent du 17 septembre (branche parente)** : 
- Composition guide sur magenta → alpha par inondation **abandonnée ici** car l'utilisateur exige texture identique : on **n'utilise PAS le générateur** pour la matière, il ne peut pas cloner le 24 px nuancé (audit `audit_texture.json` : 0% de tuiles identiques, palette dérive).
- Pipeline natif calques séparés, comme `zones_relayout_v1/v2` et `zones_south_north_v3` : extraction directe des `.tile` (header 32b tileSize, 32b count, puis `(x,y,offs64)` + payload PNG 64b length), reconstruction des sheets `792×384` et `13464×168`, puis **re-layout par copie exacte de tuiles 24×24 sans recoloration/rotation/échelle/miroir**. Grille 24 px conservée, dimensions multiples de 24, alpha droit.

**Nouveau layout — plage au sud, plus grande** :
- Nouvelle taille `1056×576` (44×24 tuiles) = **+33% largeur, +50% hauteur**, soit **608 256 px vs 304 128 px (+100% pixels, +2× surface)**. Tous bords multiples de 8 et 24.
- Arrivée sud-centre dégagée `16×16` sur sable, trajet sud→nord jusqu'à la mer en `32×32` libre, seuil dégagé.
- **Dos (Back) `D01P11A_layer1`** : bande mer (lignes 0-5 origine), écume (6), sable vagues (7-12 répété) étendu pour remplir `y 7-23` ; largeur étendue par tuilage `x%33` (tuile centrale sable) → **zéro pixel généré**, NPZ `source_xy` vérifiable.
- **Animation mer `beach_animation`** : 17 frames (FrameLength 10 → ~2.83s à 60Hz), même 17×33 décalage X par frame (0,33,…,528) conservé, 44×24 tuiles par frame. Frame 0 = tuiles `X 0-43`, frame 1 = `X 33-76`, etc. Transparent/opaque identique, pas d'invention d'écume.
- **Devant `D01P11A_layer2`** : falaises rouges + palmiers repositionnés, découpés pour ouvrir **passage sud-centre 96 px** (4 tuiles) où la plage touche la limite — 4 tuiles front supprimées à `y 22-23, x 20-23`, laissant le sable visible. Le reste inchangé, pas de resampling.
- **Ciel séparé** : deux calques BG indépendants `00_ciel_jour.png` (bleu jour `31,151,207` → `31,199,255` repris du haut de Back) et `00_ciel_nuit.png` (navy `12,24,60` + étoiles/lune extraites de `bgnightbackgroundpmdskyda.png` référence halcyon, pas de lune étirée). Le ciel n'est PAS fusionné dans Back : on le pose sous la map comme Halcyon.

**Calques livrés** (`renders/beach_sud_v1/couches/`) :
```
00_ciel_jour.png      1056×576  (BG jour, opaque)
00_ciel_nuit.png      1056×576  (BG nuit, opaque)
01_back_*.png         1056×576  (1 frame, opaque, D01P11A_layer1 natif)
02_anim_00..16.png    1056×576  (17 frames, RGBA, beach_animation natif)
03_front.png          1056×576  (1 frame, RGBA, D01P11A_layer2 natif)
```
+ `COMPOSITION_jour.png` / `COMPOSITION_nuit.png` (assemblages vérifiés), `front_masque.png`, `arrivee_masque.png`, ORA `beach_sud_v1.ora`, WebP/GIF animés, manifestes.

**Audit avant livraison** (`audit_texture.json`, `verification.json`) :
- Dimensions divisibles par 24 et 8, alpha droit, pas de resampling/miroir, zéro magenta résiduel.
- Recomposition = Back+Anim0+Front exacte, pixel-perfect, zéro différence RGB dans masque opaque.
- Provenance .tile SHA-256 conservée, offsets et tileSize vérifiés.
- Comparaison générateur : `terrain_beach_sud.png` généré testé = **0 tuile identique** sur 1056, palette sable générée `~#F5E6B8` vs native `255,247,167` + vagues diagonales absentes → **non conforme**, écart assumé, non livré comme tuile.
- Collisions : plage praticable `y>12` tuiles, falaises bloquantes, passage sud dégagé testé (pas de runtime PMDO, pas de warp testé).

**Import PMDO** : `TexSize 3` (24 px) comme origine, `Import → PNG to Tileset → 24 px`, basenames uniques `BEACH_SUD_V1_*` (l'import nomme par basename). À placer dans `Data/Ground/beach_sud_v1.rsground` (exemple JSON fourni), `AssetName beach_sud_v1`. Test d'aperçu HTML jour/nuit + calques + grille 24 px + zoom 1× inclus, pas de test moteur graphique (code 139 historique).

**Limites** : ciel étoilé/lune est une recomposition de BG halcyon, pas extraction native 1:1 du ciel EoSO (qui n'a pas de BG séparé). Animation mer est native 17 phases, pas recoloration procédurale. Aucune texture inventée pour sable/falaises/mer : 100% pixels natifs.

Rebuild : `.venv/bin/python source/beach_sud_v1/build.py`
