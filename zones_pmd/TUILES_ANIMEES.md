# Tuiles animées — méthode Chunsoft, empaquetées pour Tiled et Aseprite

Sept jeux de tuiles dessinés puis animés selon le format **DPLA** du jeu, prêts
à l'emploi dans Tiled et éditables dans Aseprite.

| Aperçu | Jeu | Tuiles | Palette DPLA | Crans animés |
|---|---|---|---|---|
| `apercus/anim_eau.gif` | `eau` | 4 | 10 | 12, à partir du cran 0 |
| `apercus/anim_lave.gif` | `lave` | 4 | 10 | 12, à partir du cran 0 |
| `apercus/anim_lueurs.gif` | `lueurs` — brasier, cristal, champignons, braises | 4 | 11 | 6, à partir du cran 6 |
| `apercus/anim_cascade.gif` | `cascade` | 1 | 10 | 10, à partir du cran 2 |
| `apercus/anim_marais.gif` | `marais` | 1 | 10 | 10, à partir du cran 2 |
| `apercus/anim_sable.gif` | `sable` | 1 | 10 | 6, à partir du cran 6 |
| `apercus/anim_rune.gif` | `rune` | 1 | 11 | 7, à partir du cran 5 |

## La chaîne

1. **Dessin** — les tuiles sont produites au générateur d'image, en consigne
   stricte de pixel art DS : basse résolution, arêtes franches, une dizaine
   d'aplats, aucun dégradé. Elles sont ensuite découpées par composantes
   connexes, ramenées à 24 px et, pour les surfaces, rendues raccordables par
   fondu croisé de leurs bords.
2. **Indexation** — chaque jeu est projeté sur une rampe de 12 couleurs triée
   par luminance. C'est cette rampe que le format anime.
3. **Animation DPLA** — les images sont produites par **substitution de
   couleurs**. Les indices des pixels ne changent jamais.
4. **Empaquetage** — planche de tuiles, `.tsx` Tiled, `.aseprite`, table
   `dpla.json`, carte `.tmx` de démonstration.

## Les deux palettes animées

Le format n'en anime que deux, aux indices **10 et 11**. Cette contrainte est
respectée, et elle est utile :

* **palette 10** pour les liquides et les surfaces — toute la rampe miroite ;
* **palette 11** pour les lueurs — seuls les crans clairs bougent. Le paramètre
  `depuis` laisse fixes les premiers crans, si bien que la flamme d'un brasier
  ou l'éclat d'un cristal vibre pendant que la pierre qui le porte reste
  parfaitement immobile. C'est exactement ce que fait le jeu.

## Trois réglages, tous obtenus en corrigeant un défaut visible

* **Variation locale.** Chaque emplacement oscille de ±1 cran autour de sa
  propre couleur. Ma première version lui faisait parcourir toute la rampe :
  les pixels sombres devenaient clairs, et la nappe clignotait au lieu de
  miroiter.
* **Amplitude mesurée.** Le réglage n'est pas à l'œil. En relevant la luminance
  moyenne image par image, l'écart-type tombe de 16 à **9** en passant d'une
  amplitude de 2 à 1 avec deux ondes le long de la rampe. La nappe miroite sans
  battre globalement du clair au sombre.
* **Une rampe par texture.** Les quatre surfaces ont d'abord partagé une rampe
  commune : cascade, marais, sable et rune se sont mélangés en teintes fausses.
  Chacune a désormais la sienne.

## Dans Tiled

Chaque `.tsx` déclare de vraies **tuiles animées** :

```xml
<tile id="0">
 <animation>
  <frame tileid="0" duration="100"/>
  <frame tileid="1" duration="100"/>
  …
 </animation>
</tile>
```

Tiled les joue dans l'éditeur, et tout moteur lisant le `.tsx` retrouve
l'animation sans une ligne de code. Les cartes `tiled/demo_*.tmx` posent une
mare de chaque type : les ouvrir suffit à voir le résultat bouger.

## Dans Aseprite

Un calque par tuile, une image par pas d'animation, et un tag `liquide` couvrant
le cycle. Repeindre une tuile dans Aseprite puis relancer
`outils/construire_animes.py` régénère la planche, le `.tsx` et les tables.

## Pour un moteur qui fait le DPLA lui-même

Les fichiers `tuiles/<jeu>_dpla.json` donnent la table complète : pour chaque
emplacement de couleur, sa liste d'images et sa durée. Le moteur n'a alors
besoin **que de la première image** de la planche — il substitue les couleurs
à la volée, comme le matériel. C'est la voie la plus fidèle et la plus légère.

## Régénérer

```bash
python3 outils/construire_animes.py
```
