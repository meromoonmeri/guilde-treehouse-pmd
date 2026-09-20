# Éducation du générateur — même texture, calques séparés, map finale

> Réponse à : « tu dois éduquer ton générateur de sorte qu'il doit créer les différent layer et la map final à partir de ces extraction les même texture » — même méthode que l'ancien agent du 17 septembre.

## 1. Extraction — banque native exacte

Depuis `Minemaker0430/ExplorersOfSkyOrigins@bed9449` — `beach.rsground` 0.8.11.0, on a extrait **les vraies textures** (aucune invention) :

- `.tile` = header `int32 tileSize`, `int32 count`, puis `count × (x int32, y int32, off int64)` → à chaque `off` : `len int64 + PNG` prémultiplié. **3 feuilles extraites** :
  - `D01P11A_layer1.tile` — 528 tuiles 24×24 → sheet `792×384` (33×16) = la map elle-même
  - `beach_animation.tile` — 3927 tuiles → sheet `13464×168` (561×7 = 17×33, boucle mer)
  - `D01P11A_layer2.tile` — 298 tuiles → sheet `792×384`
- Chaque tuile conservée avec son `(x,y,hash)` — **banque de 528+3927+298 = 4753 tuiles 24×24 natives**.
- Analyse des découvertes reproduites :
  - Back = sand lignes **7-11 seulement** (12-15 = bleu hors-map)
  - Anim = uniquement y 0-6 (mer nord), X par frame `+33*frame`
  - Front = vide en haut, plein herbé en bas
- Ces 4753 tuiles sont la **seule palette autorisée** pour le générateur.

## 2. Éducation — le générateur ne peut plus inventer

**Avant** (brut `terrain_beach_sud.png` 1408×768) : palette sable `#F5E6B8`, rochers ronds, vagues lisses — **0 tuile identique** sur 1056×576, écart RGB 67.5 (audit `audit_texture.json`).

**Après éducation** : on a **contraint le générateur** à `banque native` :

```python
# Le générateur propose la composition (silhouette sur magenta)
guide = generate_image(prompt="plage au sud, mer au nord, falaises latérales, magenta #FF00FF")

# Puis Python éduque : pour chaque bloc 24×24 du guide, on remplace par la tuile native
# la plus proche DANS LA BANQUE (distance couleur Lab, sans recoloration)
for bloc in guide.decoupe(24):
    cat = classifie(bloc.moyenne) # mer / sable / falaise
    tuile = banque[cat].plus_proche(bloc.moyenne) # 4753 tuiles natives
    layer.blit(tuile, bloc.pos) # copie exacte, pas de resampling
```

- Le guide sur magenta donne la **silhouette** (où est la plage, où sont les falaises), pas la matière.
- La matière vient **uniquement** de la banque extraite (copie exacte `crop(paste)` 24×24, alpha droit).
- On produit **4 calques séparés** tous `1056×576` (44×24, ×2.00 surface vs origine) :
  - `00_ciel_{jour,nuit}.png` — ciel séparé (Halcyon, jour = bleu mer origine, nuit = navy+étoiles)
  - `01_back.png` — D01P11A_layer1 étendu (mer 0-6, sable 7-11 cyclé jusqu'au sud)
  - `02_anim_00..16.png` — beach_animation 17 frames, mer au nord seulement
  - `03_front.png` — D01P11A_layer2, passage 96×48 sud-centre pour que plage touche la limite

## 3. Map finale à partir des calques éduqués

**Recomposition vérifiée** : `ciel + back + anim0 + front` = `COMPOSITION_{jour,nuit}.png` **pixel-perfect** (`verification.json` : `recomposition_jour_identique: true`). Aucun pixel généré dans sable/mer/falaises.

**Comparaison** :
- Gauche : brut générateur non éduqué (invention, palette dérive)
- Droite : éduqué — **même texture**, même vagues diagonales `255,247,167`, mêmes rochers `119,63,55`, mêmes palmiers `71,79,39`

C'est exactement la méthode de l'ancien agent : **générateur = guide de composition sur magenta, Python = extraction + banque + copie exacte en calques**.

## 4. Livrables éduqués

- `renders/beach_sud_v1/couches/` — 4 calques + 17 anim, tous natifs
- `renders/beach_sud_v1/COMPOSITION_*.png` — map finale jour/nuit
- `renders/beach_sud_v1/beach_sud_v1.ora` — OpenRaster multi-calques
- `apercu_beach_sud_v1.html` — viewer interactif calques/anim/jour-nuit/grille 24px
- `exports/beach_sud_v1/beach_sud_v1_pack.zip` — prêt import `24 px` (`BEACH_SUD_V1_*`)

**Import** : `PMDO Dev → PNG to Tileset → 24 px`, `TexSize 3`, `AssetName beach_sud_v1`.

## 5. Rebuild

```
.venv/bin/python source/beach_sud_v1/build.py
# = decode .tile → sheets → banque 4753 tuiles → guide magenta → éducation → calques → compositions → ORA → provenance → verification
```
