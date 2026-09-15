# Mega Raichu (#0026 Mega_X) — pack PMD / SpriteCollab complet

Livrables : [`sprite/0026_mega_x/`](../../sprite/0026_mega_x/) (107 fichiers),
`sprite-0026-mega-x.zip`, 57 aperçus dans `gifs/0026_mega_x/`.

Importable dans PMDO via **Char Sprites > Import**.

## Ce que contient le pack

**35 animations sur 35, aucune `CopyOf`, 1275 frames.**
Toutes portent les **ailes-éclairs** du design Mega.

| | |
| --- | --- |
| Animations en **8 directions** | 22 |
| Animations **mono-direction** | 13 |
| Frames totales | 1275 |
| Couleurs | 14 (limite 15) |

Les 13 mono-direction (`Sleep`, `Eat`, `Tumble`, `Pull`, `DeepBreath`, `Sit`,
`LookUp`, `Sink`, `LeapForth`, `Cringe`, `LostBalance`, `TumbleBack`,
`HitGround`) le sont **exactement comme en amont** : SpriteCollab livre
lui-même ces poses sur une seule ligne. Ce n'est pas un manque.

## Méthode

Le corps, les pattes, la queue et les oreilles **s'animent réellement** : la
géométrie vient du jeu d'animations canonique de Raichu #0026, qui fournit 35
animations, vraies poses, vraies durées, vrais marqueurs.

Deux transformations lui sont appliquées :

1. **Recoloration par rôle** vers la palette Mega (`build_full.py`). La table
   est écrite explicitement — contour, trois tons de fourrure, ventre, éclairs,
   bouche — parce que les deux palettes ne partagent aucune couleur et que
   leurs ordres de luminance divergent : un classement automatique aurait
   envoyé de la fourrure dans les éclairs.
2. **Greffe des ailes** sur **chacune des 1275 frames** (`build_winged.py`).

### L'ancrage des ailes

Chaque frame de chaque feuille `-Offsets` contient un **marqueur de tête** (le
pixel noir). Comme ce marqueur suit le crâne quand le corps se balance, marche,
bondit ou tombe, les ailes y sont ancrées et **suivent donc l'animation** au
lieu de flotter à une position fixe.

La forme d'aile est choisie **par ligne de direction** : vue de face, trois-
quarts, profil et dos ont chacune leur dessin, avec le raccourci correct. Les
ailes sont peintes **derrière le corps**, pour que la tête et les oreilles
restent lisibles.

Les frames sont élargies pour loger l'envergure, `AnimData.xml` est réécrit
avec les nouvelles dimensions, et les marqueurs sont décalés d'autant afin de
continuer à désigner les mêmes parties du corps.

### Pourquoi les ailes sont dessinées à la main

Trois voies automatiques ont été tentées puis **rejetées** :

- **découpe horizontale** de la planche générée : elle tranchait les ailes en
  deux et laissait la queue attachée ;
- **composantes connexes** sur les pixels jaunes : les ailes se fragmentent en
  20+ morceaux selon l'angle et fusionnent avec la queue à d'autres, si bien
  que les directions 3 et 5 ressortaient quasi vides ;
- **génération d'une planche d'ailes seules** : le modèle n'a rendu aucune
  image.

Les ailes sont donc **écrites en dur** dans `wings.py`, en art ASCII, à la
résolution native. C'est la seule façon d'obtenir une forme propre, cohérente
et réutilisable à cette taille.

## Contrôle

```bash
python source/sprites_mega_raichu/build_full.py     # recoloration
python source/sprites_mega_raichu/build_winged.py   # greffe des ailes
python source/sprites_mega_raichu/verify_winged.py  # validation
```

Le vérificateur contrôle : indices contigus 0–34, dimensions paires, grilles à
1 ou 8 lignes, 14 couleurs, alpha binaire, marqueurs légaux, **chaque frame non
vide porte des pixels d'éclair**, et **les animations multi-frames changent
réellement d'une frame à l'autre**. Tout passe.

## Réserves honnêtes

- Les ailes sont une **forme statique par direction**, ancrée sur la tête.
  Elles suivent le corps, mais **ne battent pas** et ne se déforment pas selon
  la pose. Une vraie animation d'ailes demanderait un dessin par frame.
- Les **yeux bleus** du design Mega ne sont pas rendus : le canonique n'a pas
  de pixel d'œil isolable sans retoucher le visage à la main.
- Le dossier est nommé **`sprite/0026_mega_x`** et non `sprite/0026/0002` :
  en amont, `Mega_X` a été échangé avec `Altcolor` (commit `e50bbab4`) et
  `sprite/0026/0002` **n'existe pas** (404).
- **Aucun test moteur PMDO ou SkyTemple n'a été effectué.**

## Crédits

Design Mega Raichu : `meromoonmeri` (commit `a214a07`).
Jeu d'animations Raichu #0026 : contributeurs SpriteCollab, CC BY-NC 4.0.
Recoloration, ailes et assemblage : `Arena.ai Agent`.
