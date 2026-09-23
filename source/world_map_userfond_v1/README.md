# Continents placés sur le fond commité par l'utilisateur

Le fond utilisé est exactement `source/user_committed_map_background.png`, extrait du fichier GitHub `image.png` du dernier commit utilisateur. Il n'est pas régénéré ni repeint.

## Sorties

- `layers/00_fond_committe_image.png` : fond utilisateur seul ;
- `layers/01_continents_iles_lieux.png` : 9 continents, îles, îles flottantes, faille spatiale et lieux ;
- `WorldMap_UserFond_9Continents.png` : assemblage final.

Le foreground est l'ancienne composition générée à 9 continents, réduite à la taille exacte du fond commité puis détourée. La livraison conserve donc deux calques assemblables.
