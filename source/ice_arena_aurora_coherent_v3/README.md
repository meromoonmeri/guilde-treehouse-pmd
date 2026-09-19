# Correction générée des falaises — V3

[Livraison et limites](../../renders/ice_arena_aurora_coherent_v3/README.md).

Cette étape répond à la demande de passer la V1 au générateur afin d'éviter un relief composé de groupes de falaises greffés. Le terrain est une **proposition générée**, pas une reconstruction native certifiée. La génération ne fait pas partie de `build.py` : les deux sorties brutes sont conservées, ainsi que le guide et la provenance dans `generation.json`.

`build.py` détoure le magenta, conserve une copie détourée en résolution originale, ajuste uniquement le nouveau terrain au canevas, puis réutilise les composants animés de `exports/ice_arena_aurora_native_v2` sans les modifier. Il vérifie leurs SHA256 contre l'inventaire publié de V2. Aucun composant du ciel n'est régénéré, étiré ou recoloré.

L'ajustement de la sortie générateur 864 × 1232 vers le terrain final est décrit explicitement dans le manifeste : recadrage du haut vide à y87, resize nearest vers 512 × 576, placement en (0,144). Le rapport d'aspect du **terrain généré** est modifié ; celui du fond natif ne l'est jamais. La silhouette et les surfaces du nouveau terrain ne sont donc pas revendiquées identiques à V1.

Produits : sept calques PNG, ORA à phase zéro, deux poses PNG, WebP de la composition, atelier, trois assets BG à noms inédits et recette de placement sans modification d'un Ground.

```bash
.venv/bin/python source/ice_arena_aurora_coherent_v3/build.py
node source/ice_arena_aurora_coherent_v3/test_viewer.cjs
```

Le build réalise 21 contrôles de pixels/fichiers ; les 15 tests JavaScript utilisent un DOM/canvas simulé. Aucun essai GPU, collision ou parcours en jeu n'est exécuté ici. Le terrain n'est pas approuvé par défaut et ne doit pas être présenté comme des tuiles PMD natives.
