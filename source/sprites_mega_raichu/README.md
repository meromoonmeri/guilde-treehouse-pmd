# Mega Raichu (#0026 Mega_X) — conversion au format PMDO / SpriteCollab

Livrables : [`sprite/0026_mega_x/`](../../sprite/0026_mega_x/),
`sprite-0026-mega-x.zip`, aperçus dans `gifs/0026_mega_x/`.

Dossier multi-sheet importable dans PMDO via **Char Sprites > Import**.

## Source

Commit **`a214a07`** sur `main` (« raichu mega evolve ») :
`dkk6pm0-...gif`, 480 × 480, 68 frames. C'est le dernier commit contenant
Mega Raichu ; copié ici dans `source.gif`.

## Ce que la mesure a établi avant toute conversion

1. **Le GIF est un agrandissement entier ×5.** La réduction en 96 × 96 par
   NEAREST est donc **sans aucune perte** : le ré-agrandissement reproduit
   l'original **au pixel près, 0 différence**. L'art natif est *récupéré*, pas
   approximé. Le script refuse de continuer si ce contrôle échoue.
2. **Sur 68 frames, 14 sont uniques** ; le reste est une boucle. Deux mouvements
   distincts : un balancement calme (frames 0–17) et un mouvement d'oreilles et
   de bras plus ample (frames 37–50).
3. **13 couleurs, alpha déjà binaire** — conforme d'emblée aux règles
   SpriteCollab.

## Échelle : pourquoi rien n'est redimensionné

Le sujet occupe **77 × 65 px natifs**. Le Raichu canonique occupe **29 × 26**.
L'art source est donc à **~2,6× l'échelle PMD**.

Il n'est **pas réduit**. Rééchantillonner du pixel art par un facteur non
entier le détruit — c'est exactement l'erreur commise sur les VFX plus tôt dans
cette session. PMDO lit les dimensions de frame dans `AnimData.xml` : le pack
déclare donc simplement ses propres frames de **78 × 66** et reste exact.

## Contenu

| Animation | Frames | Origine |
| --- | --- | --- |
| `Idle` (idx 7) | 9 | balancement, frames 0–17 de la source |
| `Charge` (idx 11) | 8 | mouvement ample, frames 37–50 de la source |
| 33 autres | — | `CopyOf Idle` |

Les **35 animations canoniques de Raichu** sont déclarées, avec les mêmes noms
et indices que `sprite/0026/AnimData.xml` en amont. Celles qu'on ne peut pas
sourcer pointent vers `Idle` par `CopyOf` : le pack est **complet et
importable** plutôt qu'à moitié vide.

## Contrôle

```bash
python source/sprites_mega_raichu/build_sprite.py
python source/sprites_mega_raichu/verify_sprite.py
```

Le vérificateur contrôle : indices contigus, cibles `CopyOf` valides,
dimensions paires, grilles 8 directions complètes, ≤ 15 couleurs, alpha
binaire, couleurs de marqueurs légales sur `-Offsets` et `-Shadow`, et
**identité pixel entre le pack et le GIF source**. Tout passe.

## Réserves honnêtes — à lire

- **La source ne contient qu'UN angle de caméra : de face.** PMD en attend 8.
  Les 7 autres ne peuvent pas être déduits d'une vue de face sans inventer du
  dessin. Chaque ligne de direction reçoit donc **le vrai artwork de face**,
  **retourné horizontalement** pour les trois lignes tournées à gauche. Le pack
  est structurellement valide et importable, mais **ce n'est pas une vraie
  rotation à 8 angles** : en jeu, le Pokémon regardera toujours la caméra.
  Corriger cela demande de redessiner les vues de profil et de dos.
- **33 animations sur 35 sont des `CopyOf Idle`** : elles existent pour que
  l'import soit propre, elles ne sont pas animées spécifiquement.
- Les **offsets** (tête, corps, mains) sont **déduits géométriquement** de la
  silhouette, pas placés à la main par un artiste. À reprendre dans SkyTemple
  pour un rendu soigné.
- **Aucun test moteur PMDO ou SkyTemple n'a été effectué.**
- Le dossier est nommé **`sprite/0026_mega_x`** et non `sprite/0026/0002` :
  en amont, `Mega_X` a été échangé avec `Altcolor` (commit `e50bbab4`) et
  `sprite/0026/0002` **n'existe pas** (404). Placer le pack au bon emplacement
  suppose de trancher ce conflit de numérotation.

## Crédits

Artwork Mega Raichu : `meromoonmeri` (commit `a214a07`). Extraction et
conversion : `Arena.ai Agent`. Voir `sprite/0026_mega_x/credits.txt`.
