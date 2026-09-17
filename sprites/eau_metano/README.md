# Métano Town — rivière et cascades originales

**Extraction des ressources de Palika/Halcyon, pas une création générée.** Aucun dessin refait, redimensionnement, lissage, recoloration ou changement de palette. Les quatre cascades côte à côte sont bien traitées comme des **frames d'animation**, pas comme quatre modèles de cascades.

Source : [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Les six blobs `.tile` utilisés ont été comparés à leurs identifiants GitHub ; leurs octets sont conservés dans `source/eau_metano/natifs/`. Preuve dans `source/eau_metano/sources_github.json`.

## 1. Cascades — 4 frames identiques à la source

- `Cascades_Metano_Exact.png` : **256 × 136 px**, les quatre frames côte à côte, sans intervalle.
- `cascade_frame_1.png` … `cascade_frame_4.png` : **64 × 136 px** chacune.
- `Cascades_Metano_Exact.tile` : nouvelle ressource PMDO, **8 × 8 px**, 32 colonnes × 17 lignes.
- `Cascades_Metano_Exact.tsj` : tileset Tiled avec animation. Placer les **8 × 17 cellules de la première frame** ; les suivantes sont les phases, pas d'autres cascades.

Rectangles extraits de `Metano_Town_Animation_Tileset`, coordonnées en pixels, borne droite/basse exclue :

| Frame | Rectangle x0, y0, x1, y1 | Origine en cellules de 8 px |
|---|---|---|
| 1 | 8, 496, 72, 632 | 1, 62 |
| 2 | 80, 496, 144, 632 | 10, 62 |
| 3 | 152, 496, 216, 632 | 19, 62 |
| 4 | 224, 496, 288, 632 | 28, 62 |

Tous les pixels, y compris les poteaux et bords de falaise présents dans les rectangles, sont conservés. Seules les marges **entre** les frames ont été retirées pour la planche pratique. L'atlas complet ci-dessous conserve l'organisation source.

**Cadence :** la carte inspectée ne référence pas ces quatre rectangles autonomes comme une séquence complète. Leur ordre spatial est conservé ; l'aperçu et les métadonnées proposent **10 ticks par phase**, sans prétendre que ce timing autonome est prouvé par la carte. Il ne faut pas confondre cette proposition avec la cadence de rivière réellement vérifiée.

## 2. Rivière — les 4 vraies planches de Métano

`Metano_Town_River_Animation_1.png` à `Metano_Town_River_Animation_4.png` : **1136 × 1512 px**, mêmes positions, aucune réduction ni recadrage. Les parties transparentes sont conservées pour ne pas casser les `TexLoc`. Chaque fichier contient 3204 cellules présentes dans sa ressource native ; la carte en anime 3200.

La carte originale **`Data/Ground/metano_town.rsground` de Palika** a été téléchargée et lue cette fois :

- `TexSize = 1` : grille Ground de **8 px** ;
- quatre `Frames`, ordre **1 → 2 → 3 → 4** ;
- mêmes `TexLoc X/Y` entre les quatre planches ;
- **`FrameLength = 10`**, cadence native PMDO.

Le relevé utile est conservé dans `source/eau_metano/animations_carte.json`, avec identifiants et empreinte du fichier original. La carte de 39 Mo n'est pas recopiée dans ce kit et n'est pas modifiée.

### Banque compacte pour l'éditeur

`Riviere_Metano_Compacte.png`, `.tile` et `.tsj` regroupent les cellules en **970 séquences uniques**, 16 colonnes, sur quatre phases rangées **de haut en bas**. Chaque phase mesure **128 × 488 px**, planche complète **128 × 1952 px**.

Une cellule n'a été regroupée avec une autre **que si ses quatre images étaient identiques**. Aucune rotation, interpolation ni modification des pixels. `eau_metano.json` conserve toutes les coordonnées source afin de retrouver chaque cellule dans les planches originales.

Pour une nouvelle Ground, poser les tuiles de la première phase et utiliser leurs frames indiquées dans le manifeste. Cette banque contient le dessin précis des berges de Métano : elle n'est **pas** un autotile universel inventant de nouveaux raccords.

## 3. Atlas originaux et scintillements

- `Metano_Town_Animation_Tileset.png` : **512 × 1408 px**, atlas source complet ; cascades et toutes les autres animations restent à leur emplacement original.
- `Metano_Town_River_Sparkles.png` : **40 × 224 px**, atlas original des scintillements. Les séquences natives utilisées dans la carte figurent dans le relevé d'animations source. Aucune nouvelle séquence n'est devinée pour les parties inutilisées.

Les fumées, moulins, plantes, bâtiments et pierres également présents dans l'atlas complet ne sont pas présentés comme des animations d'eau.

## Alpha et fidélité

Les PNG internes des `.tile` PMDO sont **prémultipliés**. Les PNG exportés pour un éditeur d'image sont en alpha droit. Les pixels opaques restent identiques ; seuls les RGB des pixels à alpha partiel de l'atlas complet sont déprémultipliés pour préserver leur rendu normal.

Le test retransforme les exports en alpha prémultiplié et obtient **zéro différence** avec les pixels source. Les cascades et les planches de rivière ont un alpha binaire : leurs pixels RGBA sont directement identiques, sans cette conversion.

## PMDO et Tiled

- Les deux nouvelles ressources `.tile` (`Cascades_Metano_Exact`, `Riviere_Metano_Compacte`) peuvent être ajoutées à `Content/Tile/`, puis **réindexées** dans le mod. Ne pas écraser l'index avec un index partiel.
- Les noms des six ressources originales de Halcyon sont conservés dans les sources. S'ils existent déjà dans votre mod, **ne pas les remplacer** inutilement.
- Pour PMDO, les `Frames`, `TexLoc` et `FrameLength` des nouvelles planches sont dans `eau_metano.json`. Ce JSON est un **manifeste auxiliaire**, pas une carte importable automatiquement.
- Une durée de 10 ticks équivaut à environ **166,67 ms à 60 Hz**. Tiled exprime des millisecondes entières : le TSJ utilise 167 ms, approximation légère. L'aperçu calcule les ticks à 60 Hz.
- Les nouvelles ressources n'ajoutent ni collision ni logique de baignade/franchissement. Placement et rendu dans le moteur à contrôler dans l'éditeur.

## Aperçu et contrôles

Ouvrir `../../apercu_eau_metano.html` : lecture/pause, avance d'une frame, zoom, grille, comparaison des quatre cascades et aperçu de la rivière. Les `apercu_riviere_frame_*.png` sont seulement des extraits de visualisation, pas un remplacement des planches complètes.

```sh
python source/build_water_metano.py
python source/verify_water_metano.py
```

Pillow requis. Tests : quatre cascades comparées aux rectangles originaux, **12816 comparaisons de cellules/frames de rivière**, recomposition des deux `.tile`, alpha, coordonnées et références Tiled. Résultat : `verification.json`. Lancement dans PMDO non effectué.

## Attribution

Ressources du projet **Halcyon de Palika**, et de ses auteurs crédités. Le [README de Halcyon](https://github.com/Palikadude/Halcyon#credits) cite notamment **Jaifain pour les animations de rivière de Métano Town**, ainsi que les autres artistes du projet. L'attribution individuelle de chaque pixel de cascade n'est pas déduite de ce crédit général.

Ce kit ne revendique pas ces sprites comme originaux et n'accorde pas de nouvelle licence sur les ressources tierces. Vérifier les autorisations des auteurs avant redistribution publique.
