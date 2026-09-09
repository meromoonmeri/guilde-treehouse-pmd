# Diagnostic — « Loading rsground file: TEST120 » puis plus rien

Analyse du log fourni et de `meromoonmeri/mypmdproject`. Il y a **trois problèmes
indépendants** dans ce log, et un seul est réellement bloquant.

---

## 1. `TEST120.rsground` est un fichier vide — c'est la cause du blocage

Dans `meromoonmeri/mypmdproject`, le fichier fait **3 octets** :

```
$ od -c TEST120.rsground
0000000 357 273 277        <-- EF BB BF, uniquement un BOM UTF-8
0000003
```

C'est un BOM UTF-8 et rien d'autre : zéro contenu. GitHub l'a d'ailleurs compté
comme « 1 insertion » lors du commit *Add files via upload*.

Le log s'arrête donc exactement là où il faut :

```
[2026/09/09 19:00:07.359] Loading rsground file: TEST120
```

Dans `RogueEssence/Data/DataManager.cs` :

```csharp
DiagManager.Instance.LogInfo(String.Format("Loading rsground file: {0}", name));
mapData = LoadEntryData<GroundMap>(name, GROUND_FOLDER, ".rsground");
mapData.AssetName = name;                        // <-- NullReferenceException ici
DiagManager.Instance.LogInfo("Completed file load.");   // jamais atteint
```

La ligne `Completed file load.` **est absente du log**, ce qui confirme que
l'échec se produit pendant/juste après la désérialisation. Le désérialiseur reçoit
une chaîne vide, retourne `null`, et `mapData.AssetName` lève une NRE — d'où le
`NREProbe` déjà présent dans le mod.

**Correction** : le fichier doit contenir une vraie carte. Un `.rsground` valide
est un JSON `{"Version": ..., "Object": {...}}` d'au moins quelques centaines de
Ko (les cartes de Halcyon vont de 180 Ko à 40 Mo). Il faut réexporter TEST120
depuis l'éditeur PMDO et **vérifier la taille du fichier avant de le commit**.

> Cause probable de l'upload vide : glisser-déposer sur l'interface web GitHub
> pendant que l'éditeur avait encore le fichier ouvert / en cours d'écriture.

---

## 2. `EndOfStreamException` dans `loadDevConfig` — bénin, à ignorer

```
System.IO.EndOfStreamException: Unable to read beyond the end of the stream.
   at System.IO.BinaryReader.Read7BitEncodedInt()
   at System.IO.BinaryReader.ReadString()
   at RogueEssence.Dev.Views.DevForm.loadDevConfig()
```

Ce n'est **pas** lié à TEST120. Le code lit le fichier `devConfig` :

```csharp
while (reader.BaseStream.Position < reader.BaseStream.Length)
{
    string key = reader.ReadString();
    string val = reader.ReadString();   // <-- si le fichier est tronqué, EOF ici
    devConfig[key] = val;
}
```

Une clé a été écrite sans sa valeur : le `devConfig` a été tronqué (fermeture
brutale de l'éditeur pendant `saveConfig()`). L'exception est capturée et loguée,
puis le jeu continue — on voit bien la suite du log s'exécuter normalement.

**Correction** : supprimer le fichier `devConfig` à côté de l'exécutable du jeu.
Il sera recréé proprement. Cela ne débloquera pas TEST120.

---

## 3. Le `.rsground` de *ce* dépôt n'était pas chargeable non plus — corrigé

`tileset_pmd/pmd/Data/Ground/luminous_spring_pmdo.rsground` était généré par
`build_pmdo_zone.py` dans un format « inspiré de » PMDO, mais pas le format réel.
Comparé aux vrais fichiers de `Palikadude/Halcyon`, il y avait 13 écarts, tous
maintenant corrigés par `fix_rsground.py` :

| # | Champ | Avant (invalide) | Après (format RogueEssence) |
|---|---|---|---|
| 1 | racine | `{"Object": ...}` | `{"Version": ..., "Object": ...}` |
| 2 | `$type` | `RogueEssence.Dungeon.GroundScene` | `RogueEssence.Ground.GroundMap, RogueEssence` |
| 3 | `Name` | `"luminous_spring_pmdo"` | `{"DefaultText": ..., "LocalTexts": {}}` |
| 4 | `obstacles` | `int[64][64]` | `GroundWall[64][64]` avec `Bounds`/`Tags` |
| 5 | `rand` | `0` | `ReRandom` polymorphe avec `$type` |
| 6 | `Status` | `[]` | `{}` (Dictionary) |
| 7 | `Background` | `""` | objet `MapBG` |
| 8 | `BlankBG` | `true` | objet `AutoTile` |
| 9 | `EdgeView` | `false` | `1` (enum `ScrollEdge.Clamp`) |
| 10 | `ActiveChar` | `{"X":32,"Y":43}` | `null` (c'est un `GroundChar`) |
| 11 | `Decorations`/`Entities` | `[]` | 1 `AnimLayer` + 1 `EntityLayer` |
| 12 | cellules | `{"Layers":[...]}` | `AutoTileset`+`Associates`+`NeighborCode`, `FrameLength` |
| 13 | `TexSize` | `8` | `1` (`TileSize = TexSize * 8`) |

Le point 11 est important : `GroundMap.OnDeserializedMethod()` appelle
`ReloadEntLayer(0)` et `GetEntryPoint()` lit `Entities[0].Markers` — des listes
vides provoquent une exception au chargement, exactement comme pour TEST120.

Le point 13 était un contresens sur l'unité : `TexSize` s'exprime en blocs de
8 px, donc des cellules d'art de 8 px valent `TexSize = 1`. Avec `8`, la carte
faisait 4096 px de large au lieu de 512 et la grille de collision était
64× trop grande.

### Index manquants, également générés

Sans eux, même un `.rsground` valide s'affiche entièrement en texture d'erreur :

- `pmd/Content/Tile/index.idx` — `TileGuide` binaire lu par
  `GraphicsManager.LoadTileIndices()`. Sans lui `GetPosition()` renvoie `0` et
  aucune cellule n'est trouvée. 9 sheets / 124 cellules indexées.
- `pmd/Data/Ground/index.idx` — `Dictionary<string, EntrySummary>` lu par
  `DataManager.GetIndex()`, sinon la carte n'apparaît pas dans la liste de
  l'éditeur.

---

## Vérifier

```bash
python3 tileset_pmd/fix_rsground.py      # régénère rsground + les 2 index
python3 tileset_pmd/verify_rsground.py   # échoue si un des 13 écarts revient
```

`verify_rsground.py` contrôle aussi que chaque `TexLoc` référencé existe
réellement dans le `.tile` correspondant, et que chaque offset de l'index pointe
bien sur un en-tête PNG. Il est appelé automatiquement à la fin de
`build_pmdo_zone.py`, qui échoue désormais si la sortie n'est pas chargeable.

## Ce qui reste à faire de ton côté

1. Réexporter `TEST120.rsground` depuis l'éditeur et vérifier qu'il ne fait pas
   3 octets avant de le pousser.
2. Supprimer le `devConfig` tronqué à côté de l'exécutable.
3. Le message `[NREPROBE] build 2026-08-04-K charge (main.lua)` est bien présent
   en première ligne : la copie du mod chargée par le jeu est donc bien celle du
   dépôt. Ce point-là est bon.
