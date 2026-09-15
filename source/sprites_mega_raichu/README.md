# Mega Raichu (#0026 Mega_X) — pack PMDO complet

Livrables : [`sprite/0026_mega_x/`](../../sprite/0026_mega_x/) (107 fichiers),
`sprite-0026-mega-x.zip`, aperçus dans `gifs/0026_mega_x/` (57 GIFs).

Dossier multi-sheet importable dans PMDO via **Char Sprites > Import**.

## Couverture

**35 animations sur 35, aucune `CopyOf`.**

| | |
| --- | --- |
| Animations en **8 directions** | 22 |
| Animations **mono-direction** | 13 |

Les 13 mono-direction (`Sleep`, `Eat`, `Tumble`, `Pull`, `DeepBreath`, `Sit`,
`LookUp`, `Sink`, `LeapForth`, `Cringe`, `LostBalance`, `TumbleBack`,
`HitGround`) le sont **exactement comme en amont** : SpriteCollab livre
lui-même ces poses sur une seule ligne, car elles ne sont jamais vues sous un
autre angle. Ce n'est pas un manque, c'est la convention PMD.

## Méthode

Le problème : l'artwork Mega Raichu (commit `a214a07`) n'existe qu'en **un seul
angle**, de face, en deux courtes boucles. La première passe se contentait de
miroiter cette vue de face — le personnage fixait la caméra depuis tous les
angles.

La solution : **Raichu canonique (#0026) possède déjà les 35 animations dans
les 8 directions**, avec vraies poses, vraies durées, vrais offsets et vraies
ombres. Mega Raichu est le même animal : même squelette, même silhouette, même
mouvement. Ce qui change, c'est la **coloration**.

Donc :

1. chaque frame canonique **garde sa pose, son timing et ses feuilles de
   marqueurs** ;
2. sa palette est remplacée par la palette Mega via une correspondance **par
   rôle** — contour, trois tons de fourrure, ventre, tons d'éclair, bouche —
   dérivée de la comparaison des deux sprites de face ;
3. résultat : un Raichu aux couleurs Mega qui s'anime correctement dans les
   huit directions, pour les trente-cinq animations.

### Pourquoi une correspondance par rôle et non par luminance

Les deux palettes ne partagent **aucune couleur**, et leurs ordres de
luminance divergent : le ton moyen de la fourrure Mega est plus sombre que
l'ombre d'éclair canonique. Un classement par luminance aurait donc envoyé des
couleurs de fourrure dans les éclairs, et inversement. La table est écrite
explicitement, rôle par rôle.

Les roses de la bouche (visibles seulement quand la gueule s'ouvre : `Eat`,
`Shoot`, `DeepBreath`, `Pain`…) sont **conservés tels quels** : la source Mega
est une idle bouche fermée et n'en fournit pas, et inventer une bouche Mega
serait de la fabrication.

## Contrôle

```bash
python source/sprites_mega_raichu/build_full.py
python source/sprites_mega_raichu/verify_sprite.py
```

Le vérificateur contrôle : indices contigus 0–34, dimensions paires, grilles à
1 ou 8 lignes, **14 couleurs** (limite 15), alpha binaire, couleurs de
marqueurs légales, **silhouettes identiques au pixel près à la géométrie
canonique** (preuve qu'il s'agit d'une recoloration et non d'un redessin),
**feuilles `-Offsets` et `-Shadow` strictement identiques aux canoniques**, et
**aucune couleur canonique survivante**. Tout passe.

## Réserves honnêtes — à lire

- **Les ailes-éclairs surdimensionnées du design Mega ne sont pas greffées.**
  C'est la limite réelle de ce pack. L'artwork source les montre de face ; les
  reporter de façon crédible sur 35 animations × 8 angles, avec la bonne
  perspective et le bon mouvement à chaque frame, est un travail
  d'animation à la main, pas quelque chose qu'un script peut simuler
  honnêtement. Le pack livre donc un **Raichu recoloré en Mega**, pas la
  silhouette Mega complète.
- Même remarque pour les **yeux bleus** du design Mega : le canonique n'a pas
  de pixel d'œil distinct à recolorer sans retoucher le visage.
- Le dossier est nommé **`sprite/0026_mega_x`** et non `sprite/0026/0002` :
  en amont, `Mega_X` a été échangé avec `Altcolor` (commit `e50bbab4`) et
  `sprite/0026/0002` **n'existe pas** (404). L'emplacement final suppose de
  trancher ce conflit de numérotation.
- **Aucun test moteur PMDO ou SkyTemple n'a été effectué.**

## Crédits

Design et artwork Mega Raichu : `meromoonmeri` (commit `a214a07`).
Jeu d'animations Raichu #0026 : contributeurs SpriteCollab, CC BY-NC 4.0.
Recoloration et assemblage : `Arena.ai Agent`.
Voir `sprite/0026_mega_x/credits.txt`.
