# Export multicalque — méthode duo PMD

Chaque dossier de zone contient une pile duo explicite dans `zone.json` : fond, sol, entrée, décors, layout, puis eau animée lorsque la zone possède de l'eau.

Pour les zones aquatiques, `05_eau_palette_cycling.gif` est un calque indépendant. Il doit être masqué dans la version sèche et joué en boucle dans la version humide. Les animations issues du port PMD Sky sont conservées séparément, sans les fondre dans le fond.

Le modèle canonique moteur complet est `source/build_zones_multicalques.py`. Il produit PNG RGBA, Aseprite, Tiled et phases d'eau/cascades natives dans `sprites/zones_guidees/01_cirque/multicalques/` et `02_terrasses/multicalques/`.
