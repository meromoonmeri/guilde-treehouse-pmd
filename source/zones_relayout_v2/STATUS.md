# Suite demandée — lot glacé et BG

Trois assets,19calques. Nouveau terrain : arène de glace768×480. BG nocturne456×240 : nuages redisposés. BG aurore264×216 : préparation5layers à composition native inchangée. Ne pas annoncer trois nouveaux terrains.

Sources et limites détaillées dans `exports/zones_relayout_v2/README.md`. Guide généré pour la composition de l’arène seulement ; tous les pixels des19calques portent leurs coordonnées source. Les originaux9ec9a081 et tous les lots précédents restent intacts.

Corrections avant livraison : le premier ciel réparé par simple voisin le plus proche clonait des teintes de nuage et laissait des formes visibles ; remplacé, sous les nuages hauts, par échantillonnage du halo natif selon le rayon. Déplacement du récif abandonné faute d’horizon natif caché disponible ; lune/reflet/récif conservés. Les nuages hauts sont découpés par composantes entières, pas tronqués arbitrairement ày82. Aiguilles lointaines : régions connectées à la teinte native des pointes, pas des fragments d’ombre des glaces proches.

Reproduction : `.venv/bin/python source/zones_relayout_v2/build.py` puis `.venv/bin/python source/zones_relayout_v2/package.py`. Le package exécute les8tests dédiés avant rapport/ZIP.104tests de régressionPASS au total. Pas d’import moteur, collision, alpha animé ou parallax validé.
