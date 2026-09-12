# Côte V2 — cartes Ground natives pour PMDO

Deux bases **éditables**, sans bâtiments, arbres ni objets ajoutés :

| Carte dans `Data/Ground/` | Pixels | Grille native |
|---|---:|---:|
| `cote_v2_promontoire.rsground` | 1312 × 816 | 164 × 102 cases de 8 px |
| `cote_v2_terrasse.rsground` | 1200 × 896 | 150 × 112 cases de 8 px |

Ce sont des sérialisations `RogueEssence.Ground.GroundMap`, pas des fichiers Tiled renommés. Les `.tile` et `.dir` nécessaires sont fournis dans l'archive générée. **Ne pas importer les `.rsground` avec « PNG to Tileset ».**

## Installation recommandée

1. Fermer PMDO et sauvegarder ton mod.
2. Extraire **tout** `cote_metano_v2_pmdo.zip` dans un dossier temporaire.
3. Avec Python 3, depuis ce dossier :

   ```sh
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod" --dry-run
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod"
   ```

   Sous Windows, `py` peut remplacer `python`. La cible est le dossier contenant **`Mod.xml`**, pas le dossier de cette archive, ni la racine du jeu. Aucune bibliothèque Python supplémentaire n'est nécessaire pour installer.

   L'installateur copie les nouvelles cartes et les ressources, **fusionne** l'index natif des tilesets avec les entrées existantes et sauvegarde l'ancien index s'il change. Les cartes déjà modifiées sont protégées : toute différence arrête l'installation **avant la copie**. Il ne modifie ni `Mod.xml`, ni les données du jeu de base.

   Les scripts vides sont fournis à l'emplacement historique `Data/Script/ground/`. Si `Mod.xml` contient `Namespace`, l'installateur crée aussi les copies `Data/Script/<Namespace>/ground/` pour les versions récentes. Si ce champ manque sur une version récente, préciser `--namespace nom_lua_du_mod` (le nom de son dossier de scripts). Aucune animation ne dépend de ces scripts.

4. Relancer PMDO en mode développement, avec **ton mod activé**.
5. Dans l'éditeur **Ground**, ouvrir `cote_v2_promontoire` ou `cote_v2_terrasse` (ou leur fichier dans `Data/Ground/`, selon la version de l'interface).
6. Ajouter tes structures sur les calques prévus et enregistrer dans ton mod.

### Sans Python

Fusionner les dossiers `Data/` et `Content/` de l'archive avec ceux du mod, sans remplacer de fichiers déjà édités. Pour les versions récentes, placer aussi chaque dossier de script sous `Data/Script/<Namespace>/ground/`.

Puis **reconstruire l'index complet des tilesets du mod** avec les outils développeur de ta version de PMDO et recharger les graphismes/redémarrer. Aucun `index.idx` partiel n'est livré : le copier sur un index existant ferait disparaître ses autres entrées. Si les textures apparaissent noires ou manquantes, vérifier en premier l'activation du mod, `Content/Tile/`, l'index et `Content/BG/`.

## Calques et ajout de structures

Dans chaque Ground :

- `Background` → `LayeredBG` : **ciel** puis **nuages**. Ce sont deux couches d'arrière-plan natives, modifiables dans les propriétés du fond, pas deux calques de peinture ordinaires.
- `00 Mer - cycle palette 8 phases` : tuiles animées.
- `01 Terrain - falaises et herbe` : terrain découpé en tuiles natives de **8 × 8 px**, sans redimensionnement.
- `02 Vos sols et chemins` : vide, derrière les personnages.
- `03 Vos structures - base` : vide, derrière les personnages.
- `04 Vos structures - avant-plan` : vide, **Top = 4**, devant les personnages.
- `Vos decorations` : calque de décorations vide, ordre Normal.
- `Vos objets et personnages` : entités vides, sauf un marqueur `entrance` sur le plateau.

Peindre la base de tes maisons sur `03`, les parties devant le joueur sur `04`, et ajouter portes/interactions dans les entités. Le tileset terrain conserve l'agencement de l'image pour pouvoir sélectionner des blocs entiers. La mer utilise un atlas compact de tuiles dédupliquées.

Importer tes propres PNG de structures à leur taille native. Ces cartes utilisent **TexSize = 1**, donc une case de carte fait **8 px** : ne pas redimensionner les images en 24 px pour tenter de changer l'échelle. Une structure de 96 px doit rester large de 96 px, soit 12 cases de cette carte.

**Collisions et gameplay non préparés :** toutes les cases de collision sont libres (`Tags = 0`), y compris ciel, mer et parois. Dessiner les obstacles et accès après l'ajout de tes structures ; le marqueur d'entrée n'est pas une zone de collision. Aucun personnage, événement, transition ni musique n'est imposé. Ce sont des bases d'édition, pas encore des niveaux jouables finalisés.

## Animations réellement configurées

- Nuages : `MapBG`, `RepeatX = true`, `RepeatY = false`, déplacement **−12 px/s**, bande de **2200 × 344 px**, origine **(0, 8)**. Défilement continu, sans aller-retour. `Parallax = (1, 1)` garde l'alignement du fond avec les coordonnées de la carte pendant les mouvements de caméra.
- Ciel : fond statique indépendant ; seuls les nuages se déplacent.
- Mer : les **8 rendus issus du véritable cycle de palette V2** sont encodés dans les `TileLayer.Frames`. PMDO affiche les phases par permutation de textures RGBA ; il ne modifie pas une palette GPU en direct. Les formes, les pixels transparents et la couleur de fond restent identiques aux sources V2.
- Le moteur attend un nombre entier de frames à 60 Hz : `FrameLength = 10`, donc **166,67 ms/phase et 1,333 s/boucle**, au lieu des 160 ms / 1,28 s de l'aperçu HTML. Ce léger ajustement est volontaire et explicite.

## Validation et limites

`verification.json` rapporte la relecture indépendante des fichiers binaires, les adresses des tuiles, l'existence de toutes les ressources référencées et la reconstruction des pixels des deux cartes. Résultat : **0 différence** sur le terrain, le ciel, les nuages à l'origine, les huit phases de mer et la composition initiale. Le wrap, les calques vides et la fusion d'index sont également testés.

**PMDO n'est pas installé dans l'environnement de fabrication : aucune ouverture réelle dans le moteur ni désérialisation .NET n'a été testée.** Le schéma est basé sur une vraie Ground Halcyon et le code source RogueEssence ci-dessous. La compatibilité avec ta version exacte reste à confirmer à l'ouverture. Si une erreur survient, conserver le message/log avec le numéro de version de PMDO.

Le terrain conserve le visuel V2 : la terrasse est une correction **générée**, inspirée de Métano, pas une reconstruction certifiée avec les tuiles canoniques. L'intégration native ne change pas cette provenance.

## Sources techniques et crédits

- Halcyon / Palika et contributeurs, commit `da6c2130d641507447e6386a5e47a296e8cb4c71` : [`Data/Ground/post_office.rsground`](https://github.com/Palikadude/Halcyon/blob/da6c2130d641507447e6386a5e47a296e8cb4c71/Data/Ground/post_office.rsground), conteneur `Version = 0.7.15.1`. Aucun PNJ, objet ou script de cette carte n'a été repris.
- Le binaire `Content/BG/Chapter_1.dir` du même dépôt a servi de contrôle du format DirSheet, pas de ressource graphique livrée.
- [RogueEssence, commit `8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b`](https://github.com/RogueCollab/RogueEssence/tree/8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b) : `GroundMap.cs`, `MapBG.cs`, `LayeredBG.cs`, `TileLayer.cs`, `DirSheet.cs`, `TileSheet.cs`, `BaseSheet.cs`, `TileIndex.cs`, `ImportHelper.cs`, `Serializer.cs`, `UpgradeConverters.cs`, `Sprites.cs`, `LuaEngine.cs`, `PathMod.cs`.
- Visuels : sources V2 du dépôt ; références Métano / Halcyon et feuille marine Pelipper fournie précédemment. La disponibilité publique des références n'implique pas une licence de redistribution sans restrictions.

## Reproduction dans le dépôt

Depuis la racine, avec Pillow et numpy (ici `.venv/bin/python`) :

```sh
.venv/bin/python source/pmdo_cote/package.py
```

Ce script reconstruit les binaires, exécute les validations, puis produit `~/cote_metano_v2_pmdo.zip`. Les fichiers intermédiaires sont placés dans `~/.cache/cote_pmdo_pack/`. Pour choisir l'emplacement final : `--output /chemin/pack.zip`.

Les sources et tests restent dans Git ; le ZIP natif est livré séparément pour ne pas ajouter aux nombreux gros packs graphiques déjà présents. **Ne pas copier les sources de fabrication dans les dossiers Data/Content du mod.**
