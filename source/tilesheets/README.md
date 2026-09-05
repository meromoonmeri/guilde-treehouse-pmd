# Source graphique des nouvelles tilesheets

- `objets_source.png` : proposition générative retenue, 16 objets disposés en 4 × 4 cellules. C’est une source de travail, **pas l’atlas à importer** : elle contient encore son fond magenta et des traits de grille.
- `provenance.json` : prompt utilisé, images de la guilde données au générateur, description des références utilisateur et empreintes des salles à préserver.
- `../build_tilesheets.py` : extraction, suppression du magenta, nettoyage des franges, tailles natives, palettes resserrées, correction des montants du premier fanion et variantes. Il fabrique aussi les ombres séparées.

Le parquet et les motifs spiralés sont construits au pixel de façon déterministe. Les murs, couloirs et paliers ont été remplacés par la **nouvelle architecture à 13 plans** de `source/build_hallways.py`, dont les sources et règles sont dans `source/hallways/`. Le constructeur général appelle cette nouvelle version et ne recrée plus les murets refusés.

Les quatre références utilisateur servent à l’interprétation graphique : bannières, lianes, paillasses, tapis, provisions et spirale claire sur le sol. Aucun sprite original du jeu n’a été copié dans le kit.

Les fichiers de jeu à importer sont dans `tilesheets/`. Les intérieurs antérieurs, leur banque de décoration et leurs panoramas restent inchangés.
