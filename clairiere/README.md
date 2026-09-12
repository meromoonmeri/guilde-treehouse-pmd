# Clairière de la guilde — zone extérieure en calques

La clairière qui abrite la guilde, vue de dessus en **vue 3/4 PMD**. Elle
fusionne les deux références : le **cadre de jungle dense et sombre** qui
cerne la carte (feuilles en surplomb, couloirs de passage), et la
**clairière ensoleillée** avec son grand arbre, ses chemins de sable et son
**grand bassin au nord** muni de **plateformes de pierre**.

- Dimensions : **1024 × 768 px**, grille de **8 × 8 px** (comme le kit).
- Quatre passages ouverts : **nord** (le canal du bassin fuit hors carte),
  **sud, ouest, est** — des continuités de sol, sans porte.
- Deux ambiances : **jour** et **nuit** (partage de la géométrie).

## Les onze calques

| # | Calque | Contenu |
|---|--------|---------|
| 00 | `00_jungle_bordure` | Jungle immersive, assombrie vers l'extérieur, coupée aux passages |
| 01 | `01_sol` | Herbe claire + chemins de sable creusés, s'arrête à la jungle |
| 02 | `02_bassin` | **Animé** — 12 images : nappe qui glisse et ondule |
| 03 | `03_plateformes` | Rive de sable + 5 plateformes de pierre posées sur l'eau |
| 04 | `04_arbre` | Grand arbre central et son ombre de contact |
| 05 | `05_objets` | Buissons, rochers, souches, fleurs, champignons |
| 06 | `06_lueurs` | **Animé** — reflets clairs de la végétation qui scintillent |
| 07 | `07_lumiere` | **Animé, additif** — puits de lumière au-dessus du bassin |
| 08 | `08_particules` | **Animé, additif** — pollen (jour) / lucioles (nuit) |
| 09 | `09_bordure_avant` | Frange de feuilles en surplomb sur la clairière |
| 10 | `10_vignette` | Vignette multiplicatrice |

`calques/jour/` et `calques/nuit/` : un PNG par calque, `_00` à `_11`
pour les calques animés.

## Export

- **Tiled** : `tiled/clairiere_jour.tmj` et `clairiere_nuit.tmj` — 11
  calques de tuiles 8×8 reconstituant chaque image (un tileset-image par
  calque, embarqué). L'eau du bassin est posée depuis `bassin_eau.tsx`
  (`bassin_eau_nuit.tsx` la nuit) : **1 572 tuiles animées**, 12 images à
  110 ms — l'animation est une vraie animation Tiled, pas un GIF.
- **Aseprite** : `clairiere_jour.aseprite` / `clairiere_nuit.aseprite`
  (écrits maison, RGBA) — 12 images, 11 calques, cels liés pour les calques
  fixes.
- **Aperçus** : `apercus/apercu_jour.png`, `apercu_nuit.png`,
  `apercu_anime.gif` (24 images, aller-retour jour↔nuit).
- **Visionneuse** : `apercu_clairiere.html` — autonome, hors ligne, avec
  bascule jour/nuit, lecture de l'animation et calques masquables.

## Règnes du bassin

- La nappe d'eau est **tuilée** : le `.tsx` découpe le bassin en cellules
  8×8 et anime chaque cellule sur les 12 images de la bande
  `bassin_eau.png`.
- Les **5 plateformes** sont mises à l'échelle (46–118 px), posées dans la
  zone intérieure du bassin avec une ombre de contact.
- Le **canal nord** relie le bassin au bord de la carte : l'eau continue
  hors champ, la jungle s'écarte autour.

## Reproduire

```
~/.venv/bin/python outils/composer_clairiere.py
```

Régénère tout depuis `sources_ia/` (textures générées : jungle, herbe,
sable, eau, plateformes, arbre, objets). Les tirages sont seedés : la
sortie est reproductible.
