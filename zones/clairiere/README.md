# Clairière de l'arbre ancien — au format PMDO

Zone récupérée de `meromoonmeri/zone-pmd` (commit `0f9805e`, « Reconstruit la
clairiere au format PMDO Tiled »), mise à l'échelle PMDO et exportée dans les
formats **natifs** de RogueEssence, prête à déposer dans un mod.

## Ce qui n'allait pas dans l'export d'origine

| | `zone-pmd@0f9805e` | ici |
|---|---|---|
| Fond | `base.png` **1088 × 976** (ni multiple de 8 ni de 24), rééchantillonné flou | **560 × 480** = 70 × 60 cellules de 8 px, ÷2 exact |
| Couleurs du fond | ~250 000 | **256** (palette k-means), aplats nets |
| Calques | 3 `imagelayer` Tiled, animations non câblées | `.tile` + `.rsground` natifs, eau animée dans le moteur ; Tiled avec **tileset dédoublonné** et tuiles animées |
| Collision | absente | grille 8 px : 1 058 cellules libres / 4 200, entrée sud ouverte |

## Échelle

Master 1120 × 960 → **÷2 exact par blocs de 2 × 2**, sans rognage : toute la
composition est conservée. 560 × 480 = **23,3 × 20 cases de 24 px**, soit 3,5
écrans de 320 × 240 ; le bassin tient dans un écran. Les sprites de Halcyon
(Salamèche 26 × 22, Arcko 22 × 21) posés à 1:1 sur `apercu_echelle.png` font la
taille d'une pierre de margelle : c'est la lecture attendue en PMD.

> Pourquoi pas 504 × 456 (21 × 19 cases) comme les autres zones : il aurait fallu
> rogner 112 px de large sur le master ou réduire d'un facteur non entier (flou).
> 560 × 480 reste dans la fourchette Halcyon (Altere Pond fait 928 × 768).

## Fichiers

```
zones/clairiere/
├── pmdo/                       ← à copier dans le dossier du mod PMDO
│   ├── Content/Tile/Clairiere_Base.tile               (4 200 tuiles)
│   ├── Content/Tile/Clairiere_Eau.tile                (4 états, 221 tuiles uniques)
│   ├── Content/Tile/Clairiere_Lumiere_Rayon.tile      (3 états)
│   ├── Content/Tile/Clairiere_Lumiere_Etincelles.tile (5 états)
│   └── Data/Ground/clairiere.rsground
├── tiled/clairiere.tmx  + clairiere_tuiles.tsx / .png  (8 px, 4 441 tuiles, 77 animées)
├── calques/               PNG séparés : base, eau ×4, rayon ×3, étincelles ×5, planches
├── fond.png               base + eau (frame 0)
├── fond_lumiere.png       idem + les deux calques de lumière
├── collision.png          1 px par cellule, blanc = mur
├── obstacles.txt          la même grille en texte (# mur, . libre)
├── apercu_collision.png   grille 24 px, murs en rouge, cadre viewport 320 × 240
├── apercu_echelle.png     sprites étalon posés à 1:1
├── apercu_eau_frames.png  les 4 états de l'eau côte à côte
├── apercu_x3.png          fond ×3 au plus proche voisin
└── zone.json              descripteur (tailles, calques, séquences, stats)
```

## Dans PMDO

1. Copier `pmdo/Content/Tile/*.tile` dans `<mod>/Content/Tile/` et
   `pmdo/Data/Ground/clairiere.rsground` dans `<mod>/Data/Ground/`.
2. Ouvrir la carte dans l'éditeur ground (`Ground Edit → Load → clairiere`).
   L'eau s'anime toute seule : 8 frames de `FrameLength` 8 ticks (≈ 1,1 s de cycle).
3. Les calques **Lumiere Rayon** et **Lumiere Etincelles** sont livrés
   `Visible: false`, en `DrawLayer.Top`. Les activer depuis l'éditeur (ou par
   script) pour la scène d'évolution.
4. L'entrée est au sud : déclencheur `South_Exit` (23 cellules de large, sur le
   bord) et marqueur `Main_Entrance_Marker` juste au-dessus, comme dans les cartes
   de Halcyon. Le reste (script, musique, PNJ) se fait dans l'éditeur.

La collision a été relevée sur le master (herbe + sable = praticable, bassin,
pierres, troncs et canopée = mur) puis limitée à la composante joignable depuis
le sud. Elle se retouche à la souris dans l'éditeur PMDO ou dans Tiled (calque
`Collision`, deux pinceaux).

## Reproduire / vérifier

```bash
python3 source/build_clairiere.py     # regénère tout depuis source/clairiere_master/
python3 source/verify_clairiere.py    # relit .tile/.rsground/.tmx et recompose l'image
```

`source/pmdo_format.py` contient les lecteurs/écrivains des formats
(`.tile`, `.rsground`) relevés dans le code de RogueEssence.
