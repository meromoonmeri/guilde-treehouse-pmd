# Sources de la V5

Voir [la notice illustrée](../../renders/ice_arena_northern_sky_v5/README.md) pour les transformations, l’animation, les assets et les limites.

- `build.py` : construction reproductible depuis les bruts conservés ; Pillow, NumPy, SciPy, OpenCV épinglés dans `requirements.txt`. Aucun nouveau tirage du générateur n’est nécessaire pour reconstruire les fichiers.
- `references/` : terrain V4 sur magenta, détail du défaut et aurore V4 A sur noir. Les références sont dérivées d’images déjà générées ; pas de prétention à de nouvelles tuiles natives.
- `generation.json` : **trois appels**, six poses sur **une** planche, deux passes d’entrée. Entrées/sorties avec SHA256 et commit de référence V4 complet. **Les prompts sont résumés, pas archivés mot à mot.**
- `viewer.html` : modèle du véritable aperçu HTML ; le constructeur remplace `__DATA__` par les chemins relatifs.
- `verify.py` : relecture indépendante des 448 frames WebP, des PNG, de l’ORA, des références météo et des empreintes. Six tests vérifient que les milieux de transition ne sont pas de simples fondus.
- `test_browser.py` : **vrai Chromium headless**, rendu, animation effective, boutons, boucle des contrôles, calques, nuages, zoom, mobile, ressources et erreurs JavaScript. Ce n’est pas un test du moteur PMDO.

## Tests navigateur

Le constructeur n’a pas besoin de Playwright. Pour ce test optionnel :

```bash
.venv/bin/pip install playwright==1.63.0
.venv/bin/python -m playwright install chromium
# Serveur statique ouvert dans un autre terminal
.venv/bin/python -m http.server 8768 --bind 0.0.0.0 --directory renders/ice_arena_northern_sky_v5
.venv/bin/python source/ice_arena_northern_sky_v5/test_browser.py http://127.0.0.1:8768
```

Dans l’environnement de cette livraison, le CDN Playwright a refusé la connexion TLS. Le test a finalement été exécuté avec **Chromium153.0.8010.0**, paquet npm `@sparticuz/chromium@153.0.0`, rendu logiciel. Le binaire et ses bibliothèques sont temporaires, hors Git. `test_browser.py` accepte la configuration locale facultative `.cache/browser/launch.json` (`executable_path`, `args`) ; sinon il utilise le Chromium Playwright normal.

## Empreintes

`renders/ice_arena_northern_sky_v5/files.sha256.json` couvre les fichiers de cette source et de l’export, sauf l’inventaire lui-même et le rapport de vérification qui contrôle cet inventaire. Les bruts, références météo et fichiers V4 utilisés ont aussi leurs empreintes dans `generation.json` / `manifest.json`. Le test indépendant vérifie les anciennes livraisons contre `6887214060eaa9005dabcf771572504051ceacdd`.

Une reconstruction avec d’autres versions de bibliothèques ou une autre architecture peut produire des différences de calcul/encodage : conserver les sorties contrôlées et l’environnement épinglé. Le format BG, la provenance et les tests numériques **ne certifient pas** le caractère natif de l’art généré, les raccords artistiques en jeu, la mémoire GPU ou les collisions.
