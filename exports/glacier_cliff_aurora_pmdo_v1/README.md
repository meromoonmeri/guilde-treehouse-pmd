# Glacier Cliff Aurora — Ground PMDO 0.8.12

Carte PMDO native et editable : une arene de glace jouable au sommet, une
arrivee sud, une vue vers une foret enneigee et des montagnes, avec l'aurore
canonique sur un calque de fond distinct.

## Fichier principal

`Data/Ground/glacier_cliff_aurora_v1.rsground` est une vraie serialisation
`RogueEssence.Ground.GroundMap`, version `0.8.12.0`, `TexSize=3`, grille de
collision 72 x 54 cellules de 8 px. Le terrain jouable est une surface
continue ; les parois, le rebord avant et tout le decor de fond sont bloques.

Le tileset `Content/Tile/VastIceMountain.tile` est copie byte a byte depuis la
ressource native PMDO. Les calques du Ground sont :

1. sol praticable `VastIceMountain` / AutoTile Floor ;
2. parois et rebords `VastIceMountain` / AutoTile Wall ;
3. details secondaires `VastIceMountain` / AutoTile Secondary ;
4. calque reserve au decor d'arriere-plan ;
5. rebord de glace d'avant-plan, `Layer=4`.

## Fonds et provenance

Les fonds sont des `.dir` PMDO separes. Les pixels sont issus des references
canoniques suivantes : `aurorepmdsky.png`, `iceroadpmdsky.png`,
`bgnightbackgroundpmdskyda.png` et `source/references_54d3731/snow.png`.
Le generateur les recupere au debut du build, les copie byte a byte dans
`provenance/references/` et arrete la production si un hash change. Les bandes
montagne/foret sont des crops de pixels natifs documentes dans
`provenance/provenance.json`.

Le dossier `layers/` expose la pile demandee : nuit, aurore, montagnes,
foret en contrebas, reference de materiau d'arene, sol d'arene, parois,
rebord avant et collision. Les cinq premiers sont des sources/crops ou une
reference canonique ; les quatre derniers sont des reconstructions de controle
depuis `VastIceMountain.tile`, pas des textures
inventees. Le Ground PMDO et ses `.dir`/`.tile` restent les fichiers a
importer.

Le guide genere
`renders/glacier_cliff_aurora_v1/raw/canonical_composition_guide.png` n'est
pas importe dans le Ground et n'est pas une texture de jeu.

L'aurore livree est une image canonique statique. Aucun cycle d'animation PMDO
officiel n'ayant ete etabli pour ce panorama, aucune animation inventee n'est
presentee comme native. Une proposition d'animation peut etre ajoutee plus
tard dans un calque/tileset explicitement marque comme tel.

## Installation

Extraire l'archive dans un dossier temporaire puis lancer :

```sh
python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run
python INSTALLER.py /chemin/PMDO/MODS/mon_mod
```

L'installateur fusionne l'index des tilesets, ne remplace pas une carte editee
et copie aussi le script sous le namespace `glacier_cliff_aurora`. Pour une
ouverture directe en projet separe, le dossier contient deja `Mod.xml` et un
`Content/Tile/index.idx` autonome.

## Marqueurs

- `entrance` et `entrance_sud` : arrivee praticable au sud ;
- `arena_seuil` : point de raccord au nord de l'arene.

Ces marqueurs ne choisissent pas un donjon absent du projet utilisateur. Il
faut les relier au quest concerné pour une transition narrative.

## Validation et limites

Les tests de structure, de provenance, de references de tuiles et de
connectivite des collisions sont fournis dans `verification.json`. Le vrai
chargeur natif PMDO 0.8.12 a aussi deserialise cette carte en mode headless :
`Width=72`, `Height=54`, `TexSize=3`, `5` calques — PASS.

Ce test ne lance pas l'editeur graphique, le GPU, les deplacements ou les
animations affichees. Le PNG de preview est une reconstruction de controle,
pas une nouvelle texture canonique. La transition vers un donjon doit encore
etre liee au quest utilisateur via `arena_seuil`.
