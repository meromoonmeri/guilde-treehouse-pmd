# Source graphique des nouvelles tilesheets

- `objets_source.png` : proposition générative retenue, 16 objets disposés en 4 × 4 cellules. C’est une source de travail, **pas l’atlas à importer** : elle contient encore son fond magenta et des traits de grille.
- `provenance.json` : prompt utilisé, images de la guilde données au générateur, description des références utilisateur et empreintes des salles à préserver.
- `../build_tilesheets.py` : extraction, suppression du magenta, nettoyage des franges, tailles natives, palettes resserrées, correction des montants du premier fanion et variantes. Il fabrique aussi les ombres séparées.

Le parquet, les motifs spiralés et les pièces de murs sont construits au pixel, de façon déterministe, avec une palette rapprochée du bois de la guilde. Les deux variantes d’éclairage gardent la même géométrie. Les couloirs et paliers sont assemblés depuis ces tuiles réutilisables, non par découpage d’images de salles générées.

Les quatre références utilisateur servent à l’interprétation graphique : bannières, lianes, paillasses, tapis, provisions et spirale claire sur le sol. Aucun sprite original du jeu n’a été copié dans le kit.

Les fichiers de jeu à importer sont dans `tilesheets/`. Les intérieurs antérieurs, leur banque de décoration et leurs panoramas restent inchangés.
