# PMDO installé depuis RUNTIMEPMDO — tests natifs

## Provenance vérifiée

- Dépôt : `meromoonmeri/RUNTIMEPMDO`.
- Commit : `61c005e1dc9fd4eee6e6e7fcde77364de33d291e`.
- Archive : `pmdc-linux-x64.zip`, **77 503 089 octets**.
- SHA-256 : `c64f72afd27b96d5a870f71e44d05ee1e952909e86b9a53d0479163763c61577`.
- Ce hash correspond au champ `digest` de l’asset officiel PMDC v0.8.12, ID `406230348`.
- Version observée dans le journal du vrai exécutable : **0.8.12.0**, .NET **8.0.26**.

Le ZIP est téléchargé comme blob Git par l’API GitHub : cela évite l’hôte des releases qui échouait. Les fichiers `PMDO/PMDO` directement présents dans le dépôt sont des pointeurs LFS ; c’est bien l’archive complète qui a été utilisée.

Installation locale, ignorée par Git : `.cache/pmdo-runtime/engine/PMDO/`.

## Ressources de base

L’archive du moteur ne contient pas le jeu complet. Le premier lancement signalait `Base/PathParams.xml` absent. Les ressources ont été récupérées dans `audinowho/DumpAsset`, commit `3e767571f9dd94270b848b3a73de9bec2553a2eb`, par l’API tarball, puis extraites dans l’installation de cache. Le manque des ressources de base est résolu.

Ne pas archiver dans le dépôt de création les centaines de Mo de ressources, les exécutables, les dépendances ni les guides générés par le test.

## Tests exécutés

| Test | Résultat |
|---|---|
| CRC du ZIP et hash comparé à la release officielle | PASS |
| `./PMDO -help` | PASS, code 0 |
| `./PMDO -dev` avant ressources | Échec : Base/PathParams.xml absent |
| `./PMDO -dev` après ressources | Crash natif, code 139 |
| `-dev` avec chemin des bibliothèques embarquées et SDL offscreen | Crash natif, code 139 |
| `./PMDO -guide` | Lecture des données et génération de trois guides ; arrêt au timeout pendant les rencontres, pas un test complet |
| Chargeur Ground réel, sans affichage | **PASS : 20 cartes**, code 0 |

Le crash graphique n’est pas encore diagnostiqué. L’absence d’un environnement d’affichage fonctionnel est à traiter, mais ne suffit pas à prouver la cause exacte du crash. Aucun rendu de carte, déplacement ou animation n’a été validé par ce test.

## Test du vrai chargeur des cartes

`verify_ground_runtime.py` utilise uniquement la copie de cache. Il extrait le pack livré dans les MODS de cette copie et ajoute temporairement `test_ground_load.lua` au script de démarrage. Le script appelle réellement :

```lua
DataManager.Instance:GetGround(assetName)
```

Ce n’est plus le lecteur Python de JSON : le chargeur, le binder et les callbacks de désérialisation sont ceux du binaire PMDO 0.8.12. Les vingt cartes du pack `cotes_metano_abyss_0812_pmdo.zip` ont été chargées.

Assertions : carte non nulle, dimensions attendues, `TexSize=1`, neuf calques, présence d’un calque d’entités. Le hook initialise `GraphicsManager.DungeonTexSize=3`, valeur nécessaire à la reconstruction de la grille de collision normalement initialisée avec les graphismes. **Il n’initialise pas de GPU et ne charge pas les textures dans le moteur graphique.** Il quitte ensuite le processus, avant la génération du guide.

Le fichier `Data/Script/origin/main.lua` original est restauré après l’essai, y compris si la commande échoue. Le test ne modifie ni l’archive livrée ni les scripts du projet utilisateur.

```sh
python source/pmdo_runtime/verify_ground_runtime.py
```

Résultats : `ground_load_results.tsv`. Contexte et limites : `runtime_status.json`.

## Portée

Cette validation concerne le **dernier pack de vingt Ground déjà livré**, pas les sept nouvelles falaises et trois entrées encore en préparation. Elle apporte une preuve de désérialisation native ; elle ne remplace pas le test visuel dans l’éditeur. Les anciens rapports `native_runtime_tested: false` sont les rapports historiques de construction, antérieurs à cet essai : ce rapport est leur complément, pas une certification rétroactive de rendu.
