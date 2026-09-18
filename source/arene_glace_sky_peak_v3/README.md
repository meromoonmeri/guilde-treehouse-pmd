# Construction de l’arène V3

Depuis la racine (Pillow et NumPy) :

```sh
.venv/bin/python source/arene_glace_sky_peak_v3/build.py
.venv/bin/python source/arene_glace_sky_peak_v3/verify.py
.venv/bin/python source/arene_glace_sky_peak_v3/publish.py
node source/arene_glace_sky_peak_v3/test_viewer.cjs
```

Les quatre bruts sont conservés. Trois plans finaux générés : arène de roche/glace, frise montagneuse, forêt profonde. L’ancien bandeau forestier reste un essai. Détourage magenta, normalisation nearest uniforme, pas de recoloration ajoutée. Nouveau terrain placé à(0,270), mer de sapins à(0,213), montagnes à(0,160), canevas960×896. Les pixels visibles du terrain sont partagés sans chevauchement en quatre masques ; aucun sol caché n’est reconstitué.

Ciel/étoiles/lune/aurore reprennent V2 : copie exacte de leur emprise960×720, extension du canevas vers le bas. Les32PNG d’aurore sont **référencés dans V2**, pas dupliqués. Quatre poses de composition PNG, WebP32phases, ORA dix plans, dix PNG de calques. Le WebP peut être recalculé à partir des sources épinglées sans modèle génératif.

Résultats : [`verification.json`](verification.json), **17contrôles d’assets** ; [`viewer_checks.json`](viewer_checks.json), **13tests de logique UI en DOM simulé**, pas navigateur réel. Pas de Ground ni de test moteur pour l’arène.

[Livrable](../../renders/arene_glace_sky_peak_v3/README.md).
