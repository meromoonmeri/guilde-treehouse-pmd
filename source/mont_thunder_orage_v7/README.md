# Mont Thunder V7 — falaise générée et brume électrostatique en contrebas

- **Terrain** (`05_terrain`) : guide généré `generation/falaise_guide.png`. Une falaise de roche gris-noir porte un sommet plat ; un chemin droit bordé de pierres monte du sud au nord. Bordures verticales avec pics et corniches, mesas sombres au fond. Réduit en BOX à 304×456, quantifié au pas de 8.
- **Brume** (`02_brume`) : guide généré `generation/brume_guide.png`, opaque, bande de 608 px qui se répète en X et en Y et défile à −4 px/s sous la falaise.
- **Étincelles** (`03_brume_etincelles`) : les traits cyan du guide, retirés de la brume. 257 éclats répartis en 4 groupes qui clignotent en décalé (8 frames × 90 ms) et suivent la brume.
- **Éclairs bleus** (`04_eclairs`) : timeline V6. Chaque impact est replacé dans la brume en contrebas, là où il est le plus visible.
- **Ciel et nuages** (`00_ciel`, `01_nuages`) : repris de la V6.
- **Limites** : le terrain et la brume sont générés (non canoniques) ; les vides latéraux sont étroits, donc la brume est surtout visible sur les côtés ; collisions indicatives, rien n'a été testé en jeu.
