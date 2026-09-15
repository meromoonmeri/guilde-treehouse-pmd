# Falinks #0870 — sprite de la forme 0

Livrable : [`sprite/0870/`](../../sprite/0870/) et l'archive `sprite-0870.zip`,
dossier multi-sheet importable dans PMDO via **Char Sprites > Import**.

## Constat de départ, important

Sur SpriteCollab, **la forme 0 de Falinks n'a aucun sprite**. Seules deux
sous-formes existent :

- `sprite/0870/0002` = **Brass**, le chef ;
- `sprite/0870/0003` = **Trooper**, le soldat.

C'est cohérent avec le personnage : Falinks n'est pas un individu mais une
formation. La forme 0 est donc **l'escouade entière**, et non un Pokémon isolé
à inventer.

## Méthode

Les deux feuilles canoniques partagent **exactement la même palette de 13
couleurs** (vérifié). La forme 0 est donc composée directement à partir de
leurs pixels publiés :

- pour chaque animation, chaque direction et chaque frame, le **Brass est placé
  en tête de colonne** et **trois Troopers s'alignent derrière lui** le long de
  l'axe de déplacement ;
- l'ordre de dessin va de l'arrière vers l'avant, pour que le chef passe
  correctement devant sa troupe ;
- espacement de 7 px entre deux membres, cadre agrandi en conséquence et gardé
  à des dimensions **paires** ;
- **aucune recoloration, aucun rééchantillonnage, aucune rotation** : les
  pixels sont ceux des feuilles publiées ;
- les `-Offsets` décrivent le **Brass seul**, c'est lui le corps qui agit ;
- les `-Shadow` et les durées suivent les feuilles canoniques.

Aucun pixel n'est généré par IA dans ce lot.

## Couverture

Les 12 animations de la base canonique : `Walk` (0), `Attack` (1),
`Strike` (2, CopyOf), `Shoot` (3), `Sleep` (5), `Hurt` (6), `Idle` (7),
`Swing` (8), `Double` (9), `Hop` (10), `Charge` (11), `Rotate` (12).

Chaque animation fournit `Name-Anim.png`, `Name-Offsets.png`,
`Name-Shadow.png`, plus `AnimData.xml`.

## Contrôle

```bash
python source/sprites_falinks/build_sprites.py
python source/sprites_falinks/verify_sprites.py
python source/sprites_falinks/make_gifs.py
```

Le vérificateur contrôle : indices uniques, dimensions paires, grilles
entières, concordance de taille entre les trois feuilles, transparence binaire,
couleurs légales d'ombre et d'offsets, palette partagée ≤ 15 couleurs et
strictement issue des feuilles canoniques.

## Réserves honnêtes

- Les animations **starter** (indices 13–34) ne sont pas fournies : la base
  canonique ne les contient pas pour ce Pokémon.
- Le nombre de Troopers (3) et l'espacement (7 px) sont un choix de lisibilité
  au zoom donjon, pas une donnée canonique.
- Contrôle effectué sur les feuilles et les GIF ; **aucun test moteur PMDO ou
  SkyTemple n'a été réalisé**. À vérifier avant toute soumission SpriteBot.

## Crédits

La base Brass est créditée `<@!215638650434617345>` / PMDCollab_1, la base
Trooper `<@!544245909639397378>` / CC BY-NC 4.0. La composition de la forme 0
est attribuée à `meromoonmeri / Arena.ai Agent` dans `sprite/0870/credits.txt`.
Licence des références : CC BY-NC 4.0, usage non commercial, crédit obligatoire.
