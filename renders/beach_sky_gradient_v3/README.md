# Beach — trois ciels sans lune

Dix cartes Beach existantes + plage de référence. Ciels également visibles en sélection individuelle, dans un bandeau supplémentaire de 112 px ; terrain 512×512 inchangé. Les anciens ateliers V1/V2 restent disponibles sans modification.

- **Jour** : dégradé bleu → cyan clair, motifs de 8 pixels extraits de `Habitat_SharpedoBluff_Day_Rock_and_Sky.tile` (EoSO). Pixels et couleurs conservés à 1×, répétition horizontale, trois dernières lignes prolongées depuis y=108 pour éviter les nuages cuits du bas de la référence.
- **Nuit** : indigo → bleu, motifs extraits de `GuildOutsideNight.tile`. Les 70 premières lignes de la banque correspondent exactement au GIF `IMG_4900.gif` fourni dans le dépôt. Étoiles séparées, pas de lune.
- **Crépuscule** : violet/lavande → corail, d’après `IMG_4888.jpeg`. **Dégradé reconstitué à partir de cette référence JPEG, pas une extraction native certifiée.** Échantillons, dimensions et SHA256 documentés dans `provenance.json`. Aucun faux label « trois sprites natifs ».

Les petits nuages générés V1 sont conservés jour/nuit ; variante chromatique rose-or au crépuscule. Overlay 512×112, 8 px/s, 64 secondes : boucle exacte, y compris au franchissement du bord. Étoiles fixes indépendantes. Eau et écume conservent toutes leurs frames et leur boucle de 3,2 s ; ni rivage ni rochers retouchés. **Au crépuscule le terrain de jour reste inchangé**, seule l’ambiance du ciel est nouvelle.

## Utilisation
Ouvrir l’atelier du dépôt en HTTP (`python source/cafe_spinda_revisite_v6/serve.py`) ; il restaure si besoin les exports Beach archivés. Le pack `BeachSkyV3_fonds.zip` contient uniquement les fonds/nuages/étoiles PNG, documentation et provenance, pas une copie du réseau entier. Les fonds et overlays sont divisibles par 8 ; importer comme assets Ground/overlays appropriés, sans généraliser cette grille aux DTEF.

Reconstruction : `.venv/bin/python source/beach_sky_gradient_v3/build.py`.

Les contrôles protègent les fichiers antérieurs, vérifient les 11 sélections et les dépendances d’animation, et testent la périodicité des nuages. Aucune collision/transition PMDO ni exécution moteur n’est revendiquée.
