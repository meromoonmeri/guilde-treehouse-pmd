# Gardevoir — Eat, petite bouchée raffinée

Premier candidat d’action réellement manquante adapté à l’identité/morphologie de Gardevoir. Vue de face,8étapes, cellule32×40, durées16/8/8/8/12/8/8/20ticks. Baie portée délicatement près du visage, pause aux paupières fermées, main abaissée puis repos natif. Pas de nouvelle mâchoire humaine ni de robe qui change à chaque image.

- `gardevoir_eat_candidate/` : pack sources XML + triples, hérité intégralement du candidat V1, avec Eat ajouté sans remplacement d’action existante.
- `review/Gardevoir_Eat_front.gif` : aperçu nearest, timings GIF arrondis à10ms ; ticks XML exacts.
- `review/Gardevoir_Eat_frames.png` : étapes de la gestuelle.
- `verification.json` : précontrôle technique du pack, provenance, gestes et limites.
- Crédits Gardevoir base/Cutscene inchangés dans les fichiers voisins ; conserver les attributions/licences originales. Eat associe un corps/visage/repères natifs à un bras/baie générés puis nettoyés. Ce n’est pas une ressource native ou approuvée SpriteCollab.

Génération4×2 recadrée selon ses dimensions réelles ; continuité de main corrigée, visages générés à grands yeux non utilisés ; paupières retouchées au pixel. Le repère rouge de main est animé. Voir `source/guild_scene_animations_v2/CHOREOGRAPHY.md` pour la règle appliquée à tous les membres et les pistes non encore produites.

**État : précontrôle technique PASS, candidat artistique. Sept directions restantes. PMDO non testé.** Les autres animations manquantes et membres ne sont pas terminés. Aucun pack actif du jeu remplacé.

Reconstruction : `.venv/bin/python source/guild_scene_animations_v2/build.py`.
Galerie : `apercu_gardevoir_eat_v2.html` à la racine.
