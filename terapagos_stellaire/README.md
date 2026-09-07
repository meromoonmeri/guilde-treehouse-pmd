# Terapagos — Forme Stellaire (#1024, forme 0002)

Sprite au format **PMDCollab / SpriteCollab** pour la forme Stellaire de
Terapagos, qui n'existe pas dans le dépôt officiel. Le dossier
`sprite/1024/0002/` est prêt à être déposé tel quel dans une arborescence
SpriteCollab.

![Planche de contact](apercus/planche_contact.png)

| | |
|---|---|
| Animations | 11 planches + 2 alias `CopyOf` (`Strike`, `SpAttack`) |
| Cases | 824, en 8 directions |
| `ShadowSize` | 1, repris de la forme Terastal |
| Fichiers | `AnimData.xml`, et par animation `-Anim.png`, `-Offsets.png`, `-Shadow.png` |
| Sources éditables | `aseprite/<Animation>.aseprite`, 7 calques séparés |

## Comment il a été construit

Les sources officielles sont explicites : en forme Stellaire, **le corps de
Terapagos est identique à celui de sa forme Terastal**. Ce qui change est ce
qui l'entoure. Le sprite est donc composé sur les planches Terastal de
SpriteCollab (`sprite/1024/0001/`).

La composition retenue suit la **référence fournie par l'auteur du jeu**
(`apercus/IMG_4844.png`) : pas de dôme sous Terapagos, et la carapace conserve
ses motifs de type colorés. Ces choix sont des options en tête de
`../foulards_pmd/outils/terapagos_stellaire.py`, pour pouvoir revenir au
rendu canonique complet :

| Option | Par défaut | Effet |
|---|---|---|
| `AVEC_DOME` | `False` | dôme de cristal hexagonal au sol |
| `AVEC_GEMMES` | `False` | dix-huit gemmes de type en orbite |
| `AVEC_ETINCELLES` | `False` | scintillements flottants |
| `AVEC_ASTRE` | `True` | Terapagos miniature au sommet de la couronne |
| `AVEC_SYMBOLE` | `False` | symbole Terastal détaché au-dessus |
| `ICONES_CYAN` | `False` | symboles de la carapace virés au cyan |

Les couches générées par-dessus le corps :

| Calque | Contenu |
|---|---|
| `gemmes_arriere` | gemmes de type passées derrière le dôme *(option)* |
| `dome` | dôme de cristal indigo à facettes hexagonales *(option)* |
| `corps` | le corps Terastal, motifs colorés conservés, liseré irisé discret |
| `couronne` | bandeau serti et pointes de cristal, **au contact** de la carapace |
| `astre` | Terapagos miniature en cristal, posé sur la pointe centrale |
| `gemmes_avant` | gemmes de type passées devant le dôme *(option)* |
| `etincelles` | scintillements *(option)* |

Chaque élément est placé à partir des données du format, pas à la main :

* **La couronne** est ancrée sur le sommet de la silhouette du corps, image par
  image, et posée **au contact** : bandeau, puis pointes soudées au bandeau,
  puis le Terapagos miniature posé sur la pointe centrale. Rien ne flotte —
  un élément détaché de quelques pixels se lit comme un défaut d'affichage à
  cette échelle, pas comme un ornement.
* **Le dôme**, quand il est activé, s'ancre sur le pixel blanc de `Shadow.png`,
  qui donne le centre au sol de la case : il suit donc automatiquement le
  Pokémon quand il bondit (`Hop`, `Attack`, `Double`). Le corps est alors
  remonté sur la calotte, avec un décalage calculé **par direction** pour ne
  pas écraser le mouvement de l'animation.
* **`Offsets.png`** reprend les quatre marqueurs de la forme Terastal, décalés
  exactement comme le corps : tête, centre et mains restent justes.
* **`Shadow.png`** reprend celle de la forme Terastal, décalée comme le corps.
  Avec le dôme activé, elle est reconstruite à son emprise, avec ses trois
  zones (petite, normale, grande).

La grille est agrandie de 4 px à gauche et à droite, 16 px en haut et 2 px en
bas, pour loger la couronne (8 / 22 / 8 avec le dôme activé). Toutes les dimensions restent paires,
comme l'exige le format.

## Vérification

```
ShadowSize: 1
  Walk       48x66   6x8   OK        Idle       48x66  13x8   OK
  Attack     80x74  17x8   OK        Swing      96x90   9x8   OK
  Shoot      48x58  10x8   OK        Double     72x74  16x8   OK
  Sleep      48x50   8x1   OK        Hop        48x106 10x8   OK
  Hurt       56x66   2x8   OK        Charge     48x58  10x8   OK
  Rotate     48x58   9x8   OK
conformité: OK — 824 cases, 0 pixel isolé au total
```

Contrôles passés : dimensions paires, les trois planches d'une animation
strictement de même taille, grille exacte, une durée par colonne, 1 ou 8
lignes, **un unique pixel de chaque marqueur par case** pour les quatre
couleurs d'`Offsets.png`, et un unique pixel blanc de centre au sol par case
dans `Shadow.png`. S'y ajoute un contrôle de **pixels isolés** — aucun pixel
opaque sans voisin — qui garantit qu'aucun ornement ne se détache en donnant
l'impression d'un défaut d'affichage.

## Régénérer

```bash
export SPRITECOLLAB=~/sc_tmp
python3 ../foulards_pmd/outils/terapagos_stellaire.py
```

Le script ne vide que `sprite/` et `aseprite/`, les deux dossiers qu'il produit :
le README et les aperçus sont préservés d'un appel à l'autre.

## Portée et limites

* Le corps réutilise les planches Terastal de SpriteCollab. C'est fidèle aux
  sources officielles, mais cela signifie que la forme Stellaire hérite des
  poses de la Terastal.
* Le dôme, les gemmes en orbite et le symbole Terastal détaché font partie du
  design canonique mais sont désactivés par défaut, sur décision artistique :
  à l'échelle PMD ils encombrent la silhouette. Les options ci-dessus les
  réactivent.
* Les animations absentes de la forme Terastal (`Faint`, `Sleep` étendu, etc.)
  le restent ici.
* Ce sprite est un **ajout non officiel**. La politique de SpriteCollab
  n'accepte pas les formes non officielles ; la forme Stellaire est bien
  officielle, mais une soumission au dépôt passerait par leur circuit de
  validation et demanderait vraisemblablement un travail à la main.

## Licence et crédits

Le corps dérive des planches Terastal de **PMDCollab/SpriteCollab**, publiées
sous **CC BY-NC 4.0** — usage non commercial, attribution obligatoire. Les
crédits d'origine sont conservés dans `sprite/1024/0002/credits.txt`. Le dôme,
la couronne, les gemmes, l'astre et les étincelles sont une création originale
de ce dépôt.

Terapagos et la série Pokémon Mystery Dungeon appartiennent à Spike Chunsoft /
The Pokémon Company / Nintendo.

La lecture du design s'appuie sur l'artwork officiel de la forme Stellaire.
Aucun pixel de fan art tiers n'a été repris.
