# Mont Thunder — sommet orageux V6

- **Terrain** (`03_terrain`) : même dessin que la V5 (planche 112438, élargie de 64 px, chemin droit), recoloré en roche gris/noir. Les 52 couleurs sont remplacées une à une en suivant leur luminosité, donc la texture et l'ordre des teintes sont conservés. Il est descendu de 40 px pour agrandir le ciel : canevas 304×336.
- **Ciel** (`00_ciel`) : guide généré `generation/ciel_guide.png`, bandes horizontales de nuit orageuse, arrondies au pas de 8.
- **Nuages** (`01_nuages`) : guide généré `generation/nuages_guide.png` (fond magenta, raccord gauche-droite), réduit en BOX sur une bande de 608 px, quantifié en 10 couleurs. Défilement RepeatX de −6 px/s et flash sur 5 niveaux (éclaircissement bleuté).
- **Éclairs** (`02_eclairs`) : formes canoniques de la planche 5394 (croissance en 6 et 4 frames), recolorées en 3 bleus. Chaque impact est suivi d'un « rebond » de l'arc (2 réapparitions). Timeline : 60 frames, 9,3 s. Le ciel et les nuages s'éclaircissent pendant les impacts.
- **Limites** : le ciel et les nuages viennent du générateur (pas canoniques) ; les éclairs sont petits (taille native de la planche) ; collisions de la V5 décalées de 5 rangées. Rien n'a été testé en jeu.
