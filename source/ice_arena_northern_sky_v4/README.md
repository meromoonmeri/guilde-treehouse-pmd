# Ciel nordique V4 — extension générée et terrain verrouillé

[Livraison, images et limites](../../renders/ice_arena_northern_sky_v4/README.md).

## Contrat

- Terrain : `renders/ice_arena_aurora_coherent_v3/layers/IceAuroraCoherentV3_Terrain.png`, commit `6184e2b578f5d60f479f49b406ea6ad189a3466b`, copie byte-identique.
- Aurores de référence : les deux extrémités du fond natif, commit `f10176369e707128d97a4590d5c8a78895433fe5`. Les références noires données au générateur sont dérivées des anciens PNG de rubans, sans modifier ces derniers.
- Le générateur produit UNE planche à DEUX poses panoramiques. Ce ne sont pas 64 captures ni 64 frames générées indépendamment. Brut conservé, sortie 1072 × 992, séparateur involontaire exclu.
- Les deux poses générées sont ajustées en nearest à 512 × 240, puis projetées sur une palette commune de 64 couleurs, sans dithering ajouté. Seules ces images générées sont redimensionnées/quantifiées.
- Le noir est retiré comme matte lumineuse : alpha = maximum RGB, couleurs déprémultipliées ; petits résidus noirs de valeur ≤10 supprimés sur les poses sources.
- 64 intercalaires par mélange cosinus des deux images lumineuses, aux mêmes coordonnées. Aucune translation, déformation de colonnes ou rotation ajoutée. Boucle A→B→A de 6,4 s, **rythme nouveau et non canonique**.
- Étoiles : petites composantes du fichier validé Guilde/Sharpedo, RGB et échelle conservés, positions/alpha nouveaux. Les motifs faibles sont exclus ; crête d’alpha normalisée à 255, puis modulée à 58–100 % à des phases/fréquences différentes.
- Nuages : six blocs entiers via `source/ciels_valides.py`, son traitement nocturne validé, alpha ×0,30, décalage vertical de 80 px. Dérive −2 px/s, wrap de la bande de 1440 px. Pas de wrap des aurores.
- Ciel de base : couleur nocturne (9,15,47) du pixel (0,0) de la source approuvée, sans étirement du bruit de l’image source.

L’atelier et la recette moteur suivent le temps continu des nuages. Le WebP bouclé fixe leurs positions pour ne pas inventer un raccord à 6,4 s ; un extrait 8 s non bouclé montre leur mouvement. La période commune de tous les effets est de 24 minutes, non exportée comme énorme vidéo.

## Reproduction

```bash
python3 -m venv .venv  # si nécessaire
.venv/bin/pip install -r source/ice_arena_northern_sky_v4/requirements.txt
.venv/bin/python source/ice_arena_northern_sky_v4/build.py
node source/ice_arena_northern_sky_v4/test_viewer.cjs
.venv/bin/python source/ice_arena_northern_sky_v4/verify.py
```

Le build ne réexécute pas le générateur : il repart du brut conservé. Il écrit les PNG individuels, l’ORA, deux WebP, cinq conteneurs BG PMDO, la recette, le manifeste, le calendrier et le lecteur HTML à images relatives.

23 assertions fichiers/pixels/calculs passent ; les 15 tests de lecteur sont un **DOM simulé**, pas un navigateur graphique. Aucun test moteur, GPU ou collision revendiqué. La cohérence mathématique du fondu ne prouve ni la canonicité ni une simulation physique de l’aurore. La proposition artistique reste à valider.

`generation.json` conserve références, SHA256, commits et résumé de la consigne. Les anciennes versions ne sont jamais écrasées.
