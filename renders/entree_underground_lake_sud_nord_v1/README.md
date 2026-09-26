# EUL1 — Entrée Underground Lake sud → nord, format 4:3 vaste

- **Demande** : « go carte suivante choisis ! », après EWC3.
- **Biome** : **Underground Lake**, choisi par l'agent à la demande de l'utilisateur. C'est la carte suivante de la série des entrées de donjon sud → nord.
- **Taille** : **768 × 576 px = 96 × 72 cases de 8 px**.

Fichiers :

- Aperçu : `apercu_entree_underground_lake_sud_nord_v1.html` (racine) ou `review/EUL1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EUL1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EUL1_`) : `EUL1_calques_png_8px.zip`.
- Source : `source/entree_underground_lake_sud_nord_v1/`, 15 tests.
- Base : branche de session. Les utilitaires viennent d'EWC2 / EWC1 ; rien n'est repris des branches sœurs.

## Méthode : textures canoniques par rendu généré référencé

La référence est `Underground_Lake_shore_TDS.png`, la rive du lac souterrain (PMD Explorers). On y voit :

- un sable jaune pâle au grain doux ;
- des parois olive en bosses empilées ;
- un lac bleu nuit, avec une lueur turquoise en anneaux ;
- de grands piliers et de petites stalagmites dans l'eau.

Aucune branche ne l'avait encore utilisée comme référence principale. Elle a été **passée au générateur comme image de référence**. Les prompts complets sont dans `manifest.json` → `generation`.

1. `bruts/decor_magenta.png` (1200 × 896) : décor complet et **nouveau** en 4:3, avec l'eau du lac peinte en magenta.
   - L'arrivée est au sud, par un chemin de sable entre les parois.
   - Le chemin débouche sur une large plage. Au nord, un lac en deux bassins porte les piliers et les stalagmites.
   - Une **chaussée de sable sèche** traverse le lac jusqu'à l'entrée sombre, au nord. Il n'y a pas d'eau devant la bouche (retour de l'utilisateur sur EWC1).
2. `bruts/sol_complet.png` : obtenu par édition du décor (2ᵉ essai ; le premier a rendu une réponse sans image).
   - Le générateur a remplacé le lac, les piliers, les stalagmites et la bouche par du sable, mais il a **gardé les parois**.
   - Les parois sont recalées au pixel près : décalage (0, 0), écart 3,8, contre 7,1 à 1 px.
   - Elles restent cachées sous le calque des parois.
   - Ce brut sert aussi de **témoin** : là où le décor diffère du sol complet (écart moyen 75 contre 4 sur les parois), la roche du décor est un pilier ou une stalagmite.
3. `bruts/gouttes_ronds_poses.png` : planche sur magenta (2ᵉ essai).
   - La grille demandée n'est pas respectée : 4 rangées au lieu de 2. Les 10 poses sont donc choisies à la main par fenêtre : 2 gouttes, un impact, une éclaboussure, 6 ronds.
   - Toutes sont réduites avec le même facteur (×1/8), avec une couverture minimale de 0,3 par bloc. À 0,12 ou 0,2, les traits épaississaient à 2 px et bouchaient le petit rond.

### Fidélité au rip, mesurée par test

Distances entre couleurs moyennes RGB, avec le même classifieur de pixels des deux côtés :

| Matière | Rip | Brut généré | Distance brut | Calque final | Distance finale |
|---|---|---|---|---|---|
| sable | 220,193,120 | 213,187,116 | 9,9 | sable | 3,9 |
| roche | 99,94,60 | 99,93,60 | 1,2 | parois | 5,6 |
| roche | 99,94,60 | — | — | piliers | 15,2 |

- **Sable** : le sable final est plus proche du rip que le brut, parce que la bande assombrie au pied des parois est passée dans le calque ombres.
- **Piliers** : plus clairs, car ils sont éclairés dans le dessin.
- **Eau et lueur** : aucune distance mesurée, car elles n'utilisent **que des couleurs du rip** (sous-ensemble testé des 69 couleurs de la capture).

## Normalisation, segmentation et palettes

**Réduction** : le décor est réduit d'un facteur uniforme 576/896, puis recadré au centre à 768. La moyenne se fait par classe (`down_class`).

**Segmentation** (en pleine résolution) :

- **Eau** : magenta et sa frange violette antialiasée (r − g > 60 et b − g > 60), dilatés de 2 px.
- **Entrée sombre** : composante sombre (lum < 48) qui contient le haut-centre.
- **Sable** : jaune clair (r > 150, r − b > 50, lum > 140), grande composante ; les trous de moins de 300 px sont comblés.
- **Ombres** : sable à 16 px au plus des parois, avec une luminance lissée inférieure à 187.
  - Mesure : le sable passe de lum 159 au contact à 196 au-delà de 15 px.
  - Ce sont les pixels du rendu, séparés, et non une ombre inventée.
- **Berge** : ni sable ni eau, à 14 px au plus de l'eau **et** du sable. C'est le rebord entre le lac et la plage ou la chaussée.
- **Piliers et stalagmites** : roche du décor là où le sol complet diffère (écart lissé sur 5 px supérieur à 20), hors abords de la bouche.
- **Parois** : le reste.

**Palettes séparées** :

| Groupe | Couleurs max |
|---|---|
| Terrain (sol complet, sable, ombres, berge) | 96 |
| Roche (parois, piliers) | 64 |
| Entrée sombre | 12 |

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau du lac | structure rivière Métano (bande, frange dentelée, accent, aplat, onde voyageuse), **couleurs exactes du rip** : aplat (39,39,95), bande (55,55,111), accent (63,63,119) | 4 × 10 ticks |
| 01 | lueur | cœur (31,223,167) et 8 anneaux de 4 px aux couleurs exactes du rip ; le cœur respire (± 4 %) et son bord ondule (5 lobes qui tournent) | 12 × 10 ticks |
| 02 | scintillements | pixels Métano natifs (6 groupes), posés sur le cœur de la lueur | 4 × 10 ticks |
| 03 | gouttes | 10 poses générées, 8 points de chute | 24 × 5 ticks |
| 04 | sol complet | sable généré (les parois du brut restent dessous) | — |
| 05 | sable | chemin, plage et chaussée praticables | — |
| 06 | ombres | sable assombri au pied des parois et de la berge | — |
| 07 | berge | rebord entre le lac et le sable | — |
| 08 | parois | parois rocheuses | — |
| 09 | piliers | 2 grands piliers et 8 stalagmites | — |
| 10 | profondeur | entrée sombre au nord (l'entrée du donjon) | — |

Le Ground ajoute un calque 11 vide, `Layer=4` (Top). La scène complète boucle en **120 ticks (2 s)**, soit le PPCM de 40, 120 et 120.

### Animations

- **Eau sans liseré clair.** Le rip borde le sable d'un filet clair, (119,127,175) puis (167,167,223). Il n'est pas repris, parce que tu avais demandé de retirer les petits traits blancs au bord des rives (retour sur EWC1). Contre la rive, l'eau n'a que la bande (55,55,111) : c'est testé.
- **Lueur.** Il y a une lueur par bassin, collée à la rive nord comme sur le rip ; le haut de l'ellipse passe sous les parois.
  - Centres (231, 134) et (537, 134), demi-axes 92 × 62 px.
  - La phase 12 recalculée est égale à la phase 0, et le pas 11 → 0 n'est pas plus gros que les autres (testé).
- **Scintillements.** Ils ne sont posés que sur le cœur commun aux 12 phases de la lueur. Sur le bleu nuit, ces pixels quasi blancs faisaient de petits traits blancs très visibles.
- **Gouttes.** Chronologie de 24 phases :
  1. la goutte tombe de 16 px (4 phases) ;
  2. impact, puis éclaboussure ;
  3. 6 ronds de plus en plus grands (11 phases) ;
  4. repos (7 phases).
  - Les 8 points de chute sont décalés de 3 phases chacun et placés sur l'eau sombre, loin de la lueur et des rives. La trajectoire de chute est au-dessus de l'eau.
  - L'impact, l'éclaboussure et les ronds sont détourés à l'eau visible.

## Collisions et marqueurs

- **Praticable** : le sable, ombres comprises. Le lac, la berge, les parois, les piliers et la bouche sont bloqués.
- **Cases** : 983 praticables sur 6 912 (une case est bloquée si plus de 25 % de sa surface est hors sable).
- **`entrance`** : (384, 560), au sud, sur le chemin.
- **`donjon_seuil`** : (376, 96), en haut de la chaussée, au pied de l'entrée sombre. **Aucun warp.**
- Un chemin libre de 16 × 16 px a été vérifié sur la grille (BFS).
- Un test vérifie qu'il n'y a pas d'eau sur 40 px sous la bouche.

## PMDO

- **Pack** : une banque `.tile` par calque (16 604 tuiles), `index.idx`, `Mod.xml`, `INSTALLER.py` et un `init.lua` vide.
- **Vérification** : aller-retour du format testé, grâce au lecteur `.tile` natif.
- **Limite** : aucun test fait dans PMDO (runtime, GPU, jeu).

## Limites

- **Pixels générés** : le terrain, les gouttes et les ronds sont générés. Rien n'est présenté comme natif, sauf les scintillements.
- **Animations créées** : la chute, la chronologie des ronds et la respiration de la lueur sont créées par nous ; ce ne sont pas des animations officielles.
- **Validation** : `art_approved: false`.

## Commandes

```bash
.venv/bin/python source/entree_underground_lake_sud_nord_v1/build.py      # ~25 s ; EWC2 et EWC1 doivent être présents
.venv/bin/python -m unittest source.entree_underground_lake_sud_nord_v1.test_build -v
.venv/bin/python source/entree_underground_lake_sud_nord_v1/package.py    # tests + zips + aperçu
```
