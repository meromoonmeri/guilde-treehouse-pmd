# Plage canonique EoSO v1 — six layouts en calques, eau animée native

Galerie : **`apercu_beach_canonique_v1.html`** (17 frames d'eau natives,
calques masquables, zoom, export PNG).

Six compositions neuves (1056 × 720 px, cellules 24 px) faites **uniquement de
tuiles natives** de [ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins)
(commit `bed944992c32e7e7927cc3480c72edb0b1782e26`, pins dans
`source/beach_eoso/sources_eoso.json`) :

| Feuille | Rôle |
|---|---|
| `D01P11A_layer1` | terrain : mer de secours, sable ondulé (rangées 8-11, colonnes 5-30) |
| `beach_animation` | eau **canoniquement animée** : 7 bandes de rivage, 17 frames, FrameLength 16, pas +33 |
| `D01P11A_layer2` | calque avant : falaises, palmiers, herbe, rochers, îlots |

## Les six layouts

| Dossier | Composition |
|---|---|
| `01_cote_reference/` | Reprise fidèle de la référence utilisateur : mer nord, falaises cadrantes, pente de sable à gauche, palmiers au milieu, rochers épars, rangée falaises/herbe au sud |
| `02_maree_haute/` | Même structure, mer plus présente et plage réduite |
| `03_ilot_au_large/` | La référence élargie avec un îlot rocheux natif face à la plage |
| `04_plage_abritee/` | Falaises empilées des deux côtés, crique fermée, palmiers centrés |
| `05_double_rivage/` | Mer au nord + chenal d'eau animée au sud, palmiers entre les deux |
| `06_lagon_clair/` | Mer haute piquetée de deux îlots, grande plage basse, double bosquet |

## Contenu par dossier

- `calques/back.png` (terrain), `calques/eau_01..17.png` (eau animée, RGBA),
  `calques/front.png` (falaises/palmiers) ;
- `composition_frame01.png` : rendu complet ;
- `carte.tmj` : carte Tiled 3 calques, tilesets natifs avec animation 17 frames
  (267 ms/frame ≈ FrameLength 16).

Au niveau du pack : `D01P11A_layer1/2.png+.tsj`, `beach_animation.png+.tsj`
(animations incluses), `provenance.json`, `verification.json`.

## Reproduction et contrôle

```bash
python source/build_beach_canonique.py   # reconstruit pack + aperçu
python source/verify_beach_canonique.py  # contrôle indépendant
```

Le vérificateur (indépendant du build) contrôle : blobs Git/SHA des trois
feuilles ; chaque cellule 24 px de chaque calque = copie exacte d'une tuile
native ; séquence d'eau de chaque cellule = un des 33 cycles natifs (+33/frame) ;
17 frames distinctes ; recomposition `carte.tmj` = PNG livrés.

**Non vérifié :** import runtime PMDO, collisions/transitions, continuité
artistique des raccords. TexSize de la map d'origine EoSO : 3 (24 px).
