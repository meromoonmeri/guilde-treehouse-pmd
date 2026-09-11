# Nouvelles références — jour/nuit sans structures

Les images ajoutées dans les commits `6cf427c` et `bc3afc6` ont été traitées par la méthode du projet : **dessin au générateur**, normalisation au plus proche voisin, séparation en calques RGBA, variantes d’ambiance et exports éditables.

[Ouvrir l’aperçu des six décors](../apercu_falaise.html) · [Ouvrir le rêve du test de personnalité](../apercu_reve.html)

| Décor | Format natif | Référence fournie | GIF |
|---|---|---|---|
| [Cap du large](littoral/README.md) | 512 × 320 | `anothercliff reference to made.jpg` + référence de nuit du poste Bekipan | [Jour/nuit](../previews/littoral_jour_nuit.gif) |
| [Plateaux fleuris](plateaux/README.md) | 504 × 504 | `2cwdrrs469f61.gif` | [Jour/nuit](../previews/plateaux_jour_nuit.gif) |
| [Étang de la forêt](etang/README.md) | 456 × 624 | `pondourpmdàrefaire.png` | [Jour/nuit](../previews/etang_jour_nuit.gif) |
| [Cascades célestes](cascades/README.md) | 592 × 448 | `232024.png` | [Jour/nuit](../previews/cascades_jour_nuit.gif) |

## Contenu

Chaque décor existe en **jour et nuit**, avec six emplacements de calques :

1. Arrière-plan / ciel et lointains.
2. Astres nocturnes, quand le ciel est visible.
3. Eau.
4. Reflets et cascades en overlay animé.
5. Terrain, roches et végétation naturels.
6. Emplacement de structures, **vide**.

La maison-poste, son visage/toit, les panneaux, clôtures, poteaux, souches décoratives, plateforme artificielle et chaîne de pas de l’étang ont été retirés. Les fleurs, arbres, roseaux et formations rocheuses naturelles restent là où ils constituent le paysage. Le massif des cascades est une formation naturelle, pas un bâtiment ajouté.

Le cap du large possède un **nouveau fond de nuit généré**, pleine lune et reflet marin compris. Les trois autres nuits sont des palettes appliquées aux mêmes géométries ; les astres sont ajoutés séparément lorsque le cadrage montre du ciel. Les glyphes de lune ne sont pas étirés pour remplir le cadre.

Les arrière-plans peints peuvent contenir leurs nuages : ils ne sont pas tous découpés nuage par nuage. Les cartes sont des compositions graphiques fixes avec effets, pas des terrains procéduraux ou des cartes de navigation PMDO.

## Fichiers et animation

Dans chaque sous-dossier : `calques/`, `compositions/`, `bases/`, `animations/`, `aseprite/`, `tiled/`, `kit.json` et `controle_qualite.json`.

- PNG RGBA natifs, sans légende.
- Deux Aseprite et deux cartes Tiled avec les mêmes compositions.
- Boucle de **24 images à 250 ms**, soit 6 s. Les petits cycles de cascades ont trois phases, répétées dans cette boucle ; les reflets marins ont 24 phases. Les étoiles scintillent, avec lune fixe.
- Le jour des plateaux fleuris est volontairement fixe ; les astres animent sa nuit.
- Les GIF montrent six secondes de jour puis six secondes de nuit. Leur légende est extérieure au dessin de jeu, et ils sont réduits pour GitHub.

Conserver les atlas avec les cartes Tiled. Les compositions sont validées par lecture et recomposition, pas par une ouverture dans les interfaces des éditeurs. Aucune collision, transition ou intégration `.rsground` native n’est annoncée.

## Reconstruire

```bash
python source/prepare_paysages_nouveaux.py
python source/rebuild_paysages_nouveaux.py
python source/build_preview_falaise.py
python source/verify_paysages_nouveaux.py
python source/export_nouveaux_gifs.py
```

Les natives retenues et les masques sont dans `source/paysages_nouveaux/`. La préparation ne rappelle pas le générateur. Voir la provenance pour les recadrages et limites des calques.
