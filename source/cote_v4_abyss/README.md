# Correction en cours — référence Métano nuit d’Abyss to Ascension

Source retrouvée dans `meromoonmeri/new-era-abyss-to-ascension-V4`, commit
`55860b9a5eb48697a3cea3a8bdfce5f0529d6141`.
Les six fichiers Base / Cliffs / Fringe, jour et `_Night`, sont conservés
sans modification dans `natifs/`. Les blobs Git et SHA-256 sont enregistrés
dans `provenance.json`. La documentation du dépôt source est reproduite
séparément dans `metano_nuit_reference.md` ; ses affirmations de tests
concernent ce dépôt, pas notre validation. Elle explique que ces variantes
nocturnes ont été produites par conversion colorimétrique. Nous reprenons
leurs pixels existants, sans appliquer notre propre filtre supplémentaire.

## Échantillon, pas nouveau pack final

`sample.py` reconstruit uniquement le haut balcon en jour/nuit, à partir
des masques déjà approuvés. Herbe, face, couronne et pied séparés ; placements
de cellules natives 8 px avec masque de découpe, sans rotation, étirement,
recoloration, ni anciens pixels/ombres générés. La transparence du terrain
reste identique et les contacts W/E/S sont conservés.

Sorties : `sprites/cote_v4_abyss_echantillon/`.
- `COMPARATIF_NATIF_1X.png` : terrain sec jour/nuit à échelle native.
- `REFERENCES_4X_NE_PAS_IMPORTER.png` : détails des sources, agrandis uniquement pour lecture.
- `placements.json` : coordonnées source/destination et masque de chaque cellule.
- `verification.json` : comparaison de chaque pixel posé aux fichiers jour/nuit.

**À terminer :** retours latéraux, raccords et modelé des grands volumes.
Le remplissage répétitif sert ici à étalonner la matière et les couleurs ;
la fidélité des pixels ne valide pas la construction artistique de la falaise.
Les fichiers Fringe sont récupérés mais pas encore utilisés par cet échantillon.
Aucun rsground révisé ni nouveau ZIP n’est livré à ce stade. L’ancien pack
`cotes_v2_0812_pmdo.zip` n’est pas modifié. Aucun test moteur effectué.

Reproduction : `.venv/bin/python source/cote_v4_abyss/sample.py`

Conserver les attributions et conditions des sources Métano / Palika / Halcyon.
