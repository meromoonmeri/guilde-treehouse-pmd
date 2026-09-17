# Ponts dorés — nouvelle version générée pour PMDO

Remplace artistiquement la première proposition `sprites/ponts/`, conservée pour comparaison. Les deux orientations ont été passées au **générateur d'image**, puis nettoyées et découpées par script. Référence visuelle : bois jaune lumineux, veinures olive/ocre et clous carrés de l'image fournie dans la conversation. Le fichier joint annoncé n'était pas présent dans le système de fichiers : la couleur a été décrite au générateur depuis l'image visible, avec l'ancienne planche comme entrée. Les sorties originales sont conservées dans `source/ponts_generes/`.

## Contenu

- `tilesheet_jour.png`, `tilesheet_nuit.png` : **480 × 320 px**, transparence réelle, palette limitée à 48 couleurs, sans grille ni légendes.
- Six colonnes de modules de **80 × 80 px** : ouest, centre horizontal, est, nord, centre vertical, sud.
- Quatre lignes de phases : repos, +1 px, repos, −1 px. Les poteaux d'ancrage restent fixes ; les centres oscillent. Ce n'est pas une animation extraite du jeu.
- `Ponts_Dores_{jour|nuit}_{1..4}.png` : une phase par planche, **480 × 80 px**.
- `Ponts_Dores_{jour|nuit}_{1..4}.tile` : **8 ressources natives RogueEssence**, tuiles de **8 × 8 px**, 60 colonnes × 10 lignes. Format à index d'offsets et PNG internes ; alpha prémultiplié équivalent à l'alpha droit car les pixels sont tous opaques ou transparents.
- `stamps_*.json` : coordonnées et structures d'animation des cellules de chaque module. **Manifest auxiliaire, pas un format de carte importable directement dans PMDO.**
- `tilesheet_*.tsj` : tilesets **Tiled**, grille 8 px, animations 180 ms par phase. Sélectionner les rectangles de 10 × 10 cellules dans la première rangée de modules.
- `assemblage.gif`, `planche.png`, `../../apercu_ponts_pmdo.html` : présentation, pas des textures à importer.

## Ce qui a été vérifié dans town02

Dépôt consulté : `meromoonmeri/town02`, commit `1efd098f92a0abcc892f40410db8249ecc9c9bb1`.

1. `Content/Tile/Metano_Town_Cliffs.tile` : en-tête binaire lu, **tileSize = 8**, **2169 entrées**.
2. `dev/tools/png2tileset.py` : format natif `.tile`, index global, alpha prémultiplié et animation `Layers/Frames/Sheet/TexLoc/FrameLength` examinés. Le pas d'une ground vaut **8 × TexSize** ; 24 px est la grille de donjon, pas celle à supposer pour les ressources Metano.
3. `Data/Script/halcyon/ground/WaterfallVillageCapital/init.lua` : script consulté, sans configuration de grille.
4. `Data/Ground/WaterfallVillageCapital.rsground` existe, mais son blob Git est un pointeur LFS vers **233 727 831 octets**, SHA-256 `afc5081f7348b2afed306953bf5e66a358e442cb00f93fa139ec239cf94c98ee`. Le téléchargement LFS a échoué dans cet environnement. **Le contenu de cette carte, son TexSize, son rendu et ses collisions n'ont donc pas été vérifiés.**

La compatibilité du découpage avec les ressources Metano est contrôlée, pas l'intégration finale dans WaterfallVillageCapital. Aucun fichier de town02 n'est modifié.

## Utilisation PMDO

1. Copier les huit fichiers `.tile` dans `Content/Tile/` du mod. Ne pas remplacer une ressource existante : les noms `Ponts_Dores_*` sont indépendants.
2. **Régénérer `Content/Tile/index.idx` avec les outils du dépôt**, notamment `dev/tools/rebuild_tile_index.py` cité par son convertisseur, ou le mécanisme d'import/réindexation de l'éditeur. Ne pas écraser l'index avec un index partiel ne contenant que les ponts.
3. Dans la ground cible, vérifier `TexSize`. Ces ressources sont prévues pour **TexSize = 1, soit 8 px**. Ne pas changer le TexSize d'une carte existante juste pour les ponts : si la carte cible diffère, il faut adapter l'import.
4. Chaque module fait 10 × 10 cellules moteur. Poser un ancrage puis autant de centres que nécessaire puis l'ancrage opposé. Utiliser les coordonnées indiquées par `stamps_*.json`. Les centres se répètent dans leur orientation sans rotation.
5. Pour animer une cellule : ajouter quatre Frames, les quatre noms de planches de la même palette, **les mêmes TexLoc X/Y** dans chaque planche. `FrameLength = 11` ticks, soit environ 183 ms à 60 Hz (contre 180 ms dans le GIF/Tiled). Garder toutes les cellules synchronisées.
6. Régler le calque, les collisions et le chevauchement avec les rebords dans l'éditeur. Les ponts sont fournis sur un calque composé unique ; la séparation rambardes/sol pour l'occlusion des personnages n'est pas fournie.

## Reconstruction et contrôles

```sh
python source/build_bridges_pmdo.py
python source/verify_bridges_pmdo.py
```

Pillow requis. La reconstruction réutilise les images générées sauvegardées : elle ne relance pas le générateur. Le vérificateur décode les huit `.tile`, les compare aux PNG, contrôle les raccords aux quatre phases et toutes les références d'animation. Pas de validation par lancement du moteur PMDO.
