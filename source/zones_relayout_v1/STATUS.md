# Production après « lance toi ! »

Deux premières reconstructions réalisées et inspectées : forêt/grotte blanche et passage rocheux bleu. Générateur uniquement pour composition, reconstruction avec coordonnées de provenance pour chaque pixel. Méthode et limites dans `exports/zones_relayout_v1/README.md`.

Corrections visuelles : premiers patches de sol rocheux contenaient des fragments de paroi et donnaient une mosaïque répétitive ; remplacés par4petits prélèvements de sol réellement dégagé (y208..224). Premier raccord de buissons au pied de falaise découpé en diagonale donnait une coupe droite : remplacé par des bandes végétales natives80px chevauchées32px. Ne pas revenir à ces premiers rendus.

Aucun retouchage/recoloration des pixels canoniques. Les masques servent à séparer les matériaux et occulter les modules, pas à inventer un intérieur de grotte caché. Le coude du guide rocheux n’est pas reproduit : il manque des retours de paroi dans la référence, le candidat reste un passage élargi droit. Panoramas aurore/mer nocturne et autres relayouts restent ouverts.

Reproduction des PNG/galerie/manifeste : `.venv/bin/python source/zones_relayout_v1/build.py`. Tests : `PYTHONPATH=source/pmd_character_pipeline .venv/bin/python -m unittest source.zones_relayout_v1.test_build`.96tests de régressionPASS au total ; vérification pixel≠validation artistique ou moteur.
