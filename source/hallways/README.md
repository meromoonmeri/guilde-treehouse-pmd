# Couloirs et paliers — reconstruction PMD v2

Cette architecture **remplace entièrement** les murets plats du premier kit. Les objets, les tuiles de parquet, les spirales et les douze salles ne sont pas redessinés.

## Sources

- `definitions.json` : neuf nouveaux plans à pans coupés, coordonnées du sol, orientations des sorties et placements d’exemple. Les extrémités font 96 px ; leurs axes partagent une phase modulo 32.
- `provenance.json` : contexte des trois références visuelles et empreintes de 684 fichiers à préserver, au départ de la révision `3f4fb69`.
- `../build_hallways.py` : matériau mural noueux vertical, panneaux et retours, jonctions, découpes, contacts et reflets. Le grain du mur n’est pas dérivé du parquet.
- L’écorce s’appuie sur un prélèvement du chant de `source/natives/05.png`, documenté dans le constructeur. Les feuillages sont repris dans `sprites/individuels/` ; les originaux restent intacts.

Aucune nouvelle génération d’image n’intervient dans cette reconstruction. Le rendu est déterministe à partir de ces sources.

## Ordre des plans

Fond extérieur évidé → soubassement → feuillage arrière → parquet → panneaux du fond → murs de retour → contacts → reflets → spirales → ombres des objets → objets/tentures → écorce/racines avant → feuillage avant.

Le fond sombre est transparent sous le sol. Une composition sans ce fond est également exportée. Les murs ont leurs propres PNG : masquer les murs ne doit ni retirer ni modifier le parquet. Les feuillages évitent le centre des accès et les bouts de raccord, afin de ne pas imposer deux demi-plantes incompatibles à la jonction.

Les sprites de murs/plantes sont enregistrés comme *tile objects* Tiled. Les autres plans architecturaux utilisent des tuiles de contour découpées et dédupliquées. Il ne s’agit pas d’un système de Wang complet ni d’une intégration au moteur.

## Reconstruction

```bash
python source/build_hallways.py
python source/verify_hallways.py
python source/build_tilesheets_preview.py
```

Le constructeur général `source/build_tilesheets.py` appelle aussi cette version. Les anciens PNG de calques des modules et les anciennes planches de murets sont supprimés de manière ciblée, pour qu’une reconstruction ou un import par dossier ne mélange pas les deux versions.

Les contrôles relisent les PNG, Aseprite et Tiled, vérifient la séparation des plans, le fond évidé, les raccords des panneaux, la continuité du sol et le dégagement des 21 accès. Aseprite/Tiled n’ont pas été ouverts manuellement et aucune transition de moteur n’a été installée.
