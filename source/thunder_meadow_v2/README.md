# Thunder Meadow V2 — arène du boss (guide généré)

Le guide `generation/terrain_guide.png` a été produit par le générateur d'images, avec la carte de `5394.png` comme référence de DA et un ciel magenta. Il montre une falaise qui monte du sud vers le nord jusqu'à l'arène, un chemin d'arrivée sinueux depuis le bord bas, des bordures de falaise et des îlots latéraux, et une chaîne de montagnes au loin.

Traitement : réduction BOX à 456×336, puis chaque pixel est ramené à la couleur la plus proche de la palette de 5394.png (hors couleurs des nuages). Aucune couleur inventée (contrôlé). Le dessin du terrain reste généré : **ce n'est pas un pixel-perfect canonique**.

Calques : `00_nuages` (palette flash canonique, 6 niveaux) · `01_eclairs` (frames canoniques, derrière les montagnes) · `02_montagnes` · `03_terrain` · `04_details` (rochers bleus).
La timeline est la même que pour V1 : 40 frames, 7,7 s. Les éclairs sont replacés dans le ciel, au-dessus de la chaîne. Collisions 8 px indicatives : sol jaune relié au chemin d'arrivée.
Limites : rien n'a été testé en jeu. Le chemin beige du guide devient un jaune moucheté de brun, faute de beige dans la palette.
