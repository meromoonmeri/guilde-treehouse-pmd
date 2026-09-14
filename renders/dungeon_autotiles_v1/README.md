# PMDO — audit DTEF et premier lot de tilesets

Galerie autonome : **`apercu_dungeon_autotiles_v1.html`** à la racine. Elle affiche la carte de raccords animée, les gabarits animés, les variantes visuelles0/1/2 et chaque PNG/frame téléchargeable.

**Premier lot expérimental, pas un import PMDO validé.** L’audit et les tests portent sur les fichiers et le comportement de l’importeur reproduit en Python ; aucun moteur PMDO/GPU n’a été lancé.

## Six prototypes
| Dossier | Nature | Géométrie et animations de départ |
|---|---|---|
| `foret_mousse` | Variante chromatique | Apple Woods |
| `aquatique_lagon` | Variante chromatique | Beach Cave |
| `sakura_printemps` | Variante chromatique | Apple Woods |
| `foret_lucioles` | Matières générées, reprojetées dans les tuiles | Apple Woods |
| `aquatique_corail` | Matières générées, reprojetées dans les tuiles | Beach Cave |
| `sakura_lunaire` | Matières générées, reprojetées dans les tuiles | Apple Woods |

Les trois recherches inédites utilisent réellement les trois images du générateur dans `generation/`, puis des échantillons ramenés en24×24 et intégrés **uniquement à l’intérieur des tuiles statiques opaques**. La bordure de4px est conservée après recoloration pour ne pas casser les raccords. Les fichiers `materiau_0/1/2.png` documentent les échantillons ; l’échantillon aquatique est une piste de matière, pas une nouvelle séquence d’eau intégrée.

Ce sont donc des **prototypes de nouvelles matières sur des géométries natives**, pas six jeux de47 formes entièrement redessinées. Les recherches générées restent perfectibles artistiquement. « Lucioles » et « sakura » désignent ici le thème : aucun système de particules volantes ou de pétales tombants n’est livré. Les animations conservées viennent des couches sources ; les matières ajoutées restent statiques.

## Ce que le code de PMDO confirme
Le format demandé est **DTEF — Dungeon Tile Exchange Format**, et non « EDTF ».

1. **Texture et logique sont distinctes.** Les `.tile` stockent des images découpées ; `Data/AutoTile/*.json` définit les voisins, variantes, couches et `TileFrame` (`Sheet`, `TexLoc`). Un PNG seul ne définit donc pas un autotile.
2. **AutoTileAdjacent comporte47 configurations** : voisins cardinaux bas/gauche/haut/droite (bits0–3), puis diagonales bas-gauche/haut-gauche/haut-droite/bas-droite (bits4–7). Une diagonale n’est considérée que si ses deux cardinaux sont présents. Les256 combinaisons brutes se réduisent à47 configurations valides.
3. Le gabarit DTEF contient **6colonnes ×8lignes par type** ;47 positions utiles et une case vide. Son ordre exact est extrait du tableau `FieldDtefMapping`, pas inventé. La case vide est colonne5/ligne2 en coordonnées zéro.
4. Pour les trois types ensemble, l’ordre est **Wall / Secondary / Floor**. Avec les sources24×24 inspectées, le PNG mesure **432×192**. L’importeur déduit la taille de tuile de la hauteur divisée par8 ;24px n’est donc pas une constante universelle pour tous les assets PMDO.
5. `tileset_0.png` est obligatoire ; `tileset_1.png` et `tileset_2.png` ajoutent des **variantes visuelles**, pas des frames. Ici les variantes aléatoires originales sont préservées, y compris les cases absentes.
6. Les images animées suivent `tileset_<variante>_frame<couche>_<index>.<duree>.png`. Par exemple `tileset_0_frame0_0.17.png`. Les indices des frames commencent à0 ; la durée est en **frames de jeu**, pas en millisecondes. La couche correspond à une superposition indépendante, pas à une phase globale commune à tout le tileset.
7. L’importeur trie les couches et frames numériquement ; il retient la durée de la frame0 pour chaque couche. Des durées variables au sein d’une même couche ne sont donc pas préservées par cette implémentation. Les frames transparentes peuvent être ignorées ; ce cas est testé dans le lot.
8. D’autres classes existent (AdjacentLite, Blob, Random, Stacked). Le présent lot cible **Adjacent et son import DTEF**, pas tous les modèles d’autotiling du moteur.

### Le piège corrigé pendant l’audit
Dans Beach Cave, le numéro de couche *local à une tuile* ne désigne pas toujours la même cadence. Exporter ces couches directement sous un même index DTEF créait des noms en concurrence pour une même paire couche/frame. L’importeur aurait gardé l’un des fichiers et ignoré l’autre.

L’export regroupe désormais les séquences par **type, index local, nombre de frames et durée**, puis leur attribue des indices DTEF globaux distincts. Les pixels, l’ordre et la durée de chaque séquence restent inchangés. Ce contrôle est important pour tous les futurs tilesets.

## Animation
- **Apple Woods** : deux couches de12 frames, durées17 et9. Boucle commune de1836 frames de jeu.
- **Beach Cave** : séquences de15 frames, durées4 et18 ; plusieurs groupes globaux sont nécessaires selon les cases. Boucle commune de540 frames de jeu.
- Les variantes conservent toutes les frames correspondantes. Elles ne prétendent pas être de nouvelles animations dessinées par les auteurs originaux.
- La galerie avance à60 frames logiques/s et compose chaque couche à sa propre cadence, en continu. Elle permet pause, pas-à-pas et saisie d’une frame logique.
- Les `extrait.webp` de `apercus/` sont seulement des extraits de2s : **pas des boucles complètes**. Utiliser les fichiers DTEF et la galerie pour vérifier le vrai cycle commun.

## Import sur une copie de test PMDO
Le code vérifié cherche les sous-dossiers de **`RAW/TileDtef/`** lors de la conversion `autotile`.

L’archive `PMDO_DTEF_premier_lot.zip` contient :

```text
RAW/TileDtef/foret_mousse/tileset_0.png
RAW/TileDtef/foret_mousse/tileset_1.png
RAW/TileDtef/foret_mousse/tileset_2.png
RAW/TileDtef/foret_mousse/tileset_0_frame0_0.17.png
...
RAW/TileDtef/sakura_lunaire/...
```

Sur **une installation de test**, après extraction, la syntaxe confirmée dans `PMDC/Program.cs` est :

```bash
./PMDO -raw "/chemin/vers/RAW/" -convert autotile
```

Adapter le nom de l’exécutable à la plateforme. Cette commande n’a pas été exécutée ici. Elle convertit des ressources et réindexe les autotiles ; ne pas la lancer à l’aveugle sur un jeu de production. Employer des noms de dossiers uniques pour éviter les remplacements d’assets existants.

L’importeur crée les feuilles compilées et les entrées mur/secondaire/sol d’après les noms des dossiers. Dans la version inspectée, `tileset.dtef.xml` est déclaré mais **n’est pas lu par `ImportDtef`** ; il n’est pas nécessaire à cette route PMDO. La compatibilité avec les autres outils DTEF/SkyTemple, qui peuvent attendre d’autres métadonnées, n’est pas revendiquée.

Après import réel, il reste à vérifier dans l’éditeur :47 raccords, diagonales, tuiles isolées, variations, opacité des couches, séquences complètes, ombres et résultat en donjon. Le lot ne configure pas le terrain/collision, les règles de génération d’un étage ni les spawns.

## Sources réellement inspectées
- [RogueCollab/RogueEssence — DtefImportHelper.cs](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence/Dev/DtefImportHelper.cs), import, mapping, variantes et animations.
- [AutoTileAdjacent.cs](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence/Dungeon/Tiles/AutoTileAdjacent.cs), calcul des voisins et47 champs.
- [GraphicsManager.cs](https://github.com/RogueCollab/RogueEssence/blob/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b/RogueEssence/Content/GraphicsManager.cs), conversion de `TileDtef/`.
- `TileLayer.cs`, `TileFrame.cs`, `FrameTick.cs`, `TileSheet.cs`, éditeur de feuilles et `PMDC/Program.cs`, copies locales avec versions et SHA256 dans `source/dungeon_autotiles_v1/references/`.
- [audinowho/DumpAsset](https://github.com/audinowho/DumpAsset/tree/3e767571f9dd94270b848b3a73de9bec2553a2eb), `AppleWoods.tile`, `BeachCave.tile` et six entrées `Data/AutoTile`. Données déclarées en version0.8.12.0 ; cela ne constitue pas une validation d’exécution sur toutes les versions PMDO.

Les copies DTEF natives de référence sont dans `references_dtef/`. Les images sont décodées depuis les `.tile`, avec traitement de l’alpha prémultiplié, puis replacées à leurs coordonnées24×24 d’après les JSON. Les échantillons générés ne sont pas attribués aux auteurs des assets canoniques. Les ressources restent soumises aux droits de leurs auteurs/contributeurs et ayants droit ; publication dans un dépôt ne vaut pas licence universelle.

## Vérification et fichiers
`verification.json` : **6 thèmes,204 feuilles DTEF,2829 copies natives de tuiles/frames vérifiées,47 masques**, alpha préservé, toutes les frames exportées, noms non ambigus et aucune frame d’animation transparente perdue par l’importeur. Le build protège les bordures4px après recoloration. Galerie testée en DOM simulé, pas dans un navigateur/GPU réel.

Scripts : `source/dungeon_autotiles_v1/{fetch_sources,export_references,build,gallery,verify}.py`, `test_viewer.cjs`. Dépendances Pillow/numpy ; `gh` uniquement pour les téléchargements de référence. Les trois générations sont archivées et réutilisées, pas régénérées par le build.

**Limite essentielle :** conformité structurelle et tests de pixels ne remplacent pas l’import/validation en jeu. Ce lot constitue une base concrète pour les prochaines itérations graphiques et l’essai PMDO.
