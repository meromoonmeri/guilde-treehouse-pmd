# Ponts suspendus — inspiration PMD

Création originale, et non extraction de Bourg-Trésor. Palette chaude, bois et cordes en pixel art. Les salles existantes ne sont pas modifiées.

- `ponts_jour.png`, `ponts_nuit.png` : atlas RGBA transparents de 384 × 256 px.
- Cellules **64 × 64 px**, 6 colonnes, 4 lignes, marge/espacement zéro. Alignement compatible avec la grille 8 px du kit, mais importer ce tileset avec des cellules de 64 px.
- Colonnes : ancrage ouest, centre horizontal, ancrage est, ancrage nord, centre vertical, ancrage sud.
- Lignes : quatre phases, 180 ms chacune (boucle 720 ms). Léger déplacement transversal de 1 px ; les ancrages sont animés aussi. Ce n'est pas une simulation physique.
- `ponts_*.tsj` : ouvrir comme tilesets externes dans Tiled. Seules les six tuiles de la première ligne sont à placer : elles portent les animations.
- `exemple_*.tmj` : exemples d'assemblage horizontal et vertical, sans décor de falaises.
- `../../apercu_ponts.html` : aperçu autonome hors ligne avec animation, palette et longueur réglables.
- `planche.png` : planche légendée, **pas** un atlas à importer.

## Placement

Poser un ancrage sur chaque rebord de falaise et répéter le centre entre les deux. Pas de rotation des tuiles : utiliser l'orientation dédiée. Les jonctions des cordes sont alignées à chaque phase. Synchroniser les animations si votre moteur lance chaque instance avec une phase aléatoire.

Prévoir une bande de passage centrale (coordonnées transversales 20 à 44 px) et gérer les collisions dans le moteur. Aucune collision, intersection, diagonale ou tuile de falaise n'est fournie. Les falaises de l'aperçu sont des schémas de démonstration, pas des assets du pack.

Reconstruction : `python source/build_bridges.py` (Pillow requis).
