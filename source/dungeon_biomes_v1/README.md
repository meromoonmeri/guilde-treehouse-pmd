# Production du lot donjons 1

Livraison et limites : `renders/dungeon_biomes_v1/README.md`. Dix compositions au générateur, 42 calques visibles, 616 états d’animation/référence. Les six autres duos restent en attente. L’audit couvre les onze références dès maintenant.

```sh
.venv/bin/python source/dungeon_biomes_v1/build.py
.venv/bin/python source/dungeon_biomes_v1/verify.py
.venv/bin/python source/dungeon_biomes_v1/serve.py --port 8011
```

Dépendances de build : Pillow, NumPy, SciPy ; police DejaVu Sans système. Le build extrait `native_sources.zip` dans `.cache/`, puis lit les bruts WebP lossless depuis le commit indiqué dans `raws/archive.json`. Aucun appel IA ou réseau n’est nécessaire pour rebâtir. Garder l’historique Git complet. `archive.py --restore` matérialise les bruts si nécessaire ; ce n’est pas requis pour le build.

- `red.py` : lecture BPC/BMA/BPA/BPL, assertions pour les indices de palettes. Le code natif de référence est inclus dans `native_sources.zip`. Les données de collision BMA ne sont pas importées comme collisions PMDO.
- `audit.json` : pins des deux dépôts, onze correspondances, métadonnées et SHA de chaque source incluse. Comparaison des207blobs H entre les deux arbres Git :207identiques.
- `audit.py` : régénération de cet audit à partir du cache des arbres publics épinglés et des fichiers sources. `--bootstrap` réhydrate ce cache depuis l’archive locale et les deux arbres GitHub épinglés via `gh api` ; nécessite une connexion GitHub. Ce rafraîchissement n’est pas requis pour les tests hors ligne.
- `build.py` : détourage magenta, normalisation uniquement des créations, segmentation de surfaces visibles, textures natives à1×, frames, aperçus, ZIP déterministe.
- `assemble.py` : utilitaire autonome inclus dans le ZIP pour reconstruire les dix PNG complets transparents et dix PNG composés à un tick choisi.
- `verify.py` : pixels, cadences, archives, provenance par pixel de la lave, recompositions et préservation Beach. Pas d’émulateur/PMDO ni d’approbation artistique.
- `serve.py` : racine PNG direct, WebP/ZIP directs, accès aux membres du pack sous `/dungeon-pack/…`, archives des générations et anciennes URL via les handlers existants.

Pour rester dans le budget du dépôt sans supprimer les anciennes livraisons, cinq anciens bruts supplémentaires (quatre Casino et l’étude Arcanin) sont conservés bit à bit dans l’historique Git et lus par `source/casino_network_v1/archive.py`. Les indices SHA ont été étendus, lecteurs/serveur/tests vérifiés. Aucun ancien rendu/ZIP ni fichier Beach n’a été modifié. Les dix nouveaux bruts sont archivés de la même façon au commit93ec3994. Les aperçus seulement sont compressés/quantifiés ; les PNG d’import sont sans perte.
