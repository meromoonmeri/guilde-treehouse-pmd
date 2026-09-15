# Terapagos #1024 — forme Stellaire, sprite

Livrable : [`sprite/1024/`](../../sprite/1024/) et `sprite-1024.zip`,
dossier multi-sheet importable dans PMDO via **Char Sprites > Import**.

## Constat de départ

Sur SpriteCollab, au moment du travail :

- `sprite/1024/0001` (**Terastal**) : jeu complet de 13 animations ;
- `sprite/1024/0002` (**Stellaire**) : **n'existe pas** ;
- `portrait/1024/0002` (**Stellaire**) : uniquement `Normal` et `Normal^`.

## Méthode

Terastal et Stellaire sont la même créature dans la même pose : la forme
Stellaire est une **recoloration** de la carapace, pas un autre corps. Le
sprite Stellaire reprend donc la géométrie Terastal frame par frame et applique
une recoloration déterministe.

La palette cible n'est pas inventée : c'est celle du **portrait Stellaire
publié**, seule source faisant autorité sur les couleurs de cette forme.

- correspondance par **luminance la plus proche**, chaque teinte Stellaire
  n'étant réutilisée que si nécessaire, afin que des tons distincts le restent ;
- le noir de contour est **épinglé** sur le violet de contour Stellaire, car il
  est structurel et ne doit pas suivre le classement ;
- les feuilles `-Offsets` et `-Shadow` sont des **données de marqueurs** :
  recopiées telles quelles, jamais recolorées ;
- `AnimData.xml`, durées, `HitFrame`/`ReturnFrame` : ceux du canonique.

Une première tentative par **répartition des rangs** a été testée puis
**rejetée** : elle écrasait le contraste, la palette Stellaire étant nettement
plus claire que le sprite Terastal. C'est documenté dans le code.

Aucun pixel généré par IA dans ce lot.

## Couverture

13 animations : `Walk` (0), `Attack` (1), `Strike` (2, CopyOf), `Shoot` (3),
`SpAttack` (4, CopyOf), `Sleep` (5), `Hurt` (6), `Idle` (7), `Swing` (8),
`Double` (9), `Hop` (10), `Charge` (11), `Rotate` (12).

## Contrôle

```bash
python source/sprites_terapagos/build_sprites.py
python source/sprites_terapagos/verify_sprites.py
python source/sprites_terapagos/make_gifs.py
```

Le vérificateur contrôle notamment que **la silhouette de chaque feuille est
identique au pixel près à la géométrie Terastal**, ce qui prouve qu'il s'agit
bien d'une recoloration et non d'un redessin.

## Réserves honnêtes

- Les animations **starter** (13–34) ne sont pas fournies : absentes du
  canonique pour ce Pokémon.
- La recoloration est une **transposition raisonnée**, pas une référence
  officielle : aucun sprite Stellaire officiel n'existe pour comparaison.
- **Aucun test moteur PMDO ou SkyTemple n'a été effectué.** À vérifier avant
  toute soumission SpriteBot.

## Crédits

Base Terastal : `<@!350050109741858829>` et `<@!702275233125630042>`,
CC BY-NC 4.0. Recoloration Stellaire attribuée à
`meromoonmeri / Arena.ai Agent` dans `sprite/1024/credits.txt`.
