# winter_forest_native_v2 — sources

- `build.py` : layouts des six cartes (grille 21×23 de modules 24 px), adjacence officielle 47 cas sur l’atlas 2×3 complet, copies natives Frosty Forest, calques Snow/Forest/Terrain/WalkIntent, ORA, placements, planche, `provenance.json`.
- `weather.py` : panneaux de ciel séparés (V5 boréal recadré ; ciel/nuages validés), 96 phases de poudre et de flocons dessinées pour ce lot, aperçus statiques et animés (192 poses V5 d’aurore conservées).
- `verify.py` : 111 contrôles indépendants (voir notice du rendu).
- `viewer.html` : copie de `renders/winter_forest_native_v2/index.html` ; `test_viewer.cjs` : DOM simulé.
- `references/` : feuilles Frosty Forest et 19 PNG d’animation (vides pour ces types), listing amont, commit `03c80dad`.

Notice complète : `renders/winter_forest_native_v2/README.md`. Aucun pixel de terrain généré ni retouché ; pas de validation PMDO ; pas de navigateur réel disponible pour ce lot.
