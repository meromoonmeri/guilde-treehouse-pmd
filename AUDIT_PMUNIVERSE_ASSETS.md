# Audit exhaustif des assets graphiques de PMUniverse

**Date d’audit : 13 septembre 2026 (Europe/Paris)**

**Organisation examinée :** [`github.com/PMUniverse`](https://github.com/PMUniverse)

**Périmètre :** tous les dépôts publics retournés par l’API GitHub, chaque arbre Git récursif, les archives du dépôt et les *release assets*.

## Résultat en bref

- **6 dépôts publics** ont été trouvés et audités, à leur commit de branche par défaut indiqué ci-dessous.
- Les six appels d’arbre récursif ont répondu `truncated: false`. Il ne manque donc pas de sous-répertoire dans cet inventaire.
- Les six endpoints GitHub Releases ont été parcourus : **0 release, 0 fichier de release**.
- **2 241 fichiers** pertinents ont été catalogués, totalisant **134 714 831 octets**. Chaque ligne est livrée avec son chemin, sa taille, son SHA-1 de blob Git, son SHA-256 vérifié sur clone local, et deux URL figées au commit.
- Le seul véritable corpus d’images de jeu est dans **PMU-Client** : 11 conteneurs de tiles, 751 conteneurs de sprites, 751 portraits, 550 PNG directs, 4 sources Paint.NET, 2 ICO et 5 fontes. `Installer` ne contient que trois visuels d’interface. Les trois autres dépôts de code n’ont aucun asset graphique.
- Les fichiers PMUniverse examinés ont été récupérés dans un cache ignoré uniquement afin d’en vérifier les octets et les formats. **Aucun pixel PMUniverse, tileset, sprite ou portrait n’a été copié dans le kit livré ni versionné dans ce dépôt.**

Les données détaillées, exploitables sans interprétation manuelle, sont dans [`audit_pmuniverse_assets/`](audit_pmuniverse_assets/README.md).

## Couverture par dépôt

| Dépôt | Branche / commit audité | Date du commit | Licence déclarée du dépôt | Blobs dans l’arbre | Résultat assets |
|---|---|---:|---|---:|---|
| [`Installer`](https://github.com/PMUniverse/Installer) | `master` / `e25e2256d572a04dea2abc47bece7d9097f61ea5` | 2014-11-28 | GPL-3.0 | 87 | 2 PNG + 1 ICO ; 15 `.resx` analysés |
| [`Updater`](https://github.com/PMUniverse/Updater) | `master` / `0c8ace1fb1bf5fb7711aed225172637946cf8471` | 2014-11-27 | GPL-3.0 | 131 | aucun asset graphique |
| [`Scripts`](https://github.com/PMUniverse/Scripts) | `develop` / `d095d6eccbe54ea4fbba8bec2f50de3adbc14f9a` | 2015-09-21 | AGPL-3.0 | 25 | aucun asset graphique |
| [`framework`](https://github.com/PMUniverse/framework) | `master` / `d2ee83796eb8e365d31b0f9107f088bfc9c59103` | 2015-03-18 | GPL-3.0 | 154 | aucun asset graphique |
| [`PMU-Client`](https://github.com/PMUniverse/PMU-Client) | `master` / `c25c01f9879369647cd5a19731b2e4e5acd33e67` | 2014-07-09 | MIT | 2 659 | corpus graphique principal, fontes et données de cartes |
| [`PMU-Server`](https://github.com/PMUniverse/PMU-Server) | `master` / `8fb424a520e559e94cff4973def8172cf29d90a2` | 2014-07-09 | MIT | 496 | 5 `.resx` et une archive SQL ; aucun tileset/sprite/image direct |

Les branches, commits et tailles ne sont pas déduits du nom des dépôts : ils proviennent de l’API, puis les clones locaux ont été contrôlés au même `HEAD`. Les fichiers non graphiques (code, DLL, solution, configuration, etc.) ne gonflent pas le catalogue.

## Décompte exact des fichiers catalogués

| Scope | Nombre de fichiers externes | Octets | Contenu |
|---|---:|---:|---|
| `direct_visual` | 559 | 5 831 428 | 552 PNG, 3 ICO, 4 sources Paint.NET `.pdn` |
| `visual_container` | 1 513 | 33 156 543 | 11 `.tile`, 751 `.sprite`, 751 `.portrait` |
| `typography` | 5 | 1 995 000 | TTF dans `PMU-Client/resources/Fonts/` |
| `map_data` | 140 | 42 084 480 | cartes sérialisées `resources/MapData/*.dat` |
| `resource_descriptor` | 23 | 135 072 | descripteurs `.resx` .NET contrôlés pour les ressources indirectes |
| `archive_review` | 1 | 51 512 308 | `PMU-Server/Content_Data.zip` inspecté |
| **Total** | **2 241** | **134 714 831** | inventaire CSV/JSON complet |

Les 2 072 fichiers des deux premières lignes sont les fichiers de dessin ou conteneurs de dessin. Les `.dat` sont conservés dans le catalogue car ils décrivent les cartes et leurs indices de tuiles ; ils ne constituent pas un tilesheet réutilisable. Les `.resx` et l’archive ont été inclus pour éviter de rater de l’art masqué dans une ressource compilée.

## PMU-Client : assets récupérés et formats

### 1. Tilesets

Les 11 fichiers `resources/GFX/Tiles/TilesN.tile` font **19 790 810 octets**. L’analyse de leurs index et des payloads a vérifié **52 486 flux PNG intégrés**, tous en **32 × 32 px**. Le format est un conteneur PMU indexé : chaque entrée validée pointe vers un PNG interne. Ce n’est pas un PNG atlas directement chargeable dans Tiled/Aseprite.

| Conteneur | Octets | PNG 32 × 32 internes |
|---|---:|---:|
| `Tiles0.tile` | 1 065 508 | 2 716 |
| `Tiles1.tile` | 1 971 737 | 6 118 |
| `Tiles2.tile` | 432 973 | 1 897 |
| `Tiles3.tile` | 766 704 | 3 717 |
| `Tiles4.tile` | 2 139 016 | 4 018 |
| `Tiles5.tile` | 2 254 378 | 7 210 |
| `Tiles6.tile` | 2 264 159 | 4 368 |
| `Tiles7.tile` | 3 746 120 | 8 008 |
| `Tiles8.tile` | 2 402 285 | 7 322 |
| `Tiles9.tile` | 2 419 507 | 6 174 |
| `Tiles10.tile` | 328 423 | 938 |
| **Total** | **19 790 810** | **52 486** |

Les chemins, SHA-1 Git et SHA-256 de chacun sont dans `inventory.csv`. L’analyse a validé les offsets et tailles des payloads contre le bout du fichier : elle ne se contente pas de chercher l’extension `.tile`.

### 2. Sprites et portraits

- `resources/GFX/Sprites/` contient **751 `.sprite`**, 11 952 321 octets. Ils comportent ensemble **12 676 flux PNG** internes (animations/formes et feuilles de frames). Les dimensions constatées vont de 32 × 64 à 1 216 × 64, avec aussi quelques formats non 64 px de haut.
- `resources/GFX/Mugshots/` contient **751 `.portrait`**, 1 413 412 octets. Ils comportent **749 bandes PNG** internes, hautes de 40 px et larges de 40 à 680 px. Les deux conteneurs sans PNG sont `Portrait653.portrait` et `Portrait654.portrait`.
- Le code du client (`Client/Graphics/SpriteSheet.cs`, `Mugshot.cs`, `GraphicsManager.cs`) lit ces fichiers via `BinaryReader`, métadonnées de formes puis flux PNG. Le catalogue les nomme donc justement *conteneurs PMU* et non faussement « fichiers PNG ».

Au total, les trois formats conteneurs renferment **65 911 flux PNG** (52 486 tuiles + 12 676 sprites + 749 portraits), sans compter les PNG autonomes.

### 3. PNG, UI et sources éditables

Les **550 PNG directs** de `PMU-Client` (5 615 838 octets) ont tous été lus jusqu’à leur en-tête `IHDR` pour relever dimensions et famille. La ventilation est :

| Famille | Fichiers | Octets | Observation |
|---|---:|---:|---|
| `resources/GFX/Status/` | 196 | 187 875 | tous les PNG font 384 × 32 |
| `resources/GFX/Spells/` | 191 | 519 895 | animations / feuilles de sorts, dimensions variées |
| `resources/GFX/Items/Items.png` | 1 | 232 111 | atlas vertical 192 × 5 856 |
| `resources/GFX/Updater/` | 2 | 1 041 | icônes 16 × 16 |
| `resources/Skins/Main Theme/` | 89 | 2 552 448 | interface du thème principal |
| `resources/Skins/Terra's Theme/` | 68 | 1 808 771 | interface du thème Terra |
| `resources/Help/Controls/` | 2 | 313 381 | schémas 500 × 500 et 606 × 191 |
| autre (`Controls/Scrollbar`) | 1 | 316 | curseur 7 × 12 |

Les 4 `.pdn` sont des sources Paint.NET pour boutons de fenêtre dans les deux skins. Les 2 ICO sont `pmuicon.ico` (même contenu aux deux emplacements). Les 5 TTF (`Courier New`, `FSEX300`, `PMU`, `tahoma`, `unown`) sont également indexés mais ne doivent pas être considérés automatiquement comme redistribuables.

En ajoutant les 2 PNG de l’installer, il y a **66 463 flux PNG/fichiers PNG** repérés dans les ressources graphiques : 65 911 internes aux conteneurs et 552 PNG autonomes. Les ICO et `.pdn` ne sont pas artificiellement comptés comme PNG.

### 4. Cartes sérialisées

Les 140 fichiers de `PMU-Client/resources/MapData/` totalisent 42 084 480 octets. Ils sont catalogués comme données de carte reliées aux tuiles, non comme images. Une conversion éventuelle devrait reprendre le format et vérifier les droits des assets référencés ; elle n’a pas été effectuée ici.

## Ressources indirectes et archive serveur

### `.resx`

Les 23 fichiers `.resx` ont été lus. Ils ne cachent pas une deuxième banque de tiles/sprites : les descripteurs de `Installer/Properties/Resources.resx` renvoient aux deux PNG et à l’ICO déjà comptés ; le descripteur client renvoie à `pmuicon.ico`. Les autres sont du boilerplate de formulaire ou du texte. Ils restent dans le manifest afin que cette conclusion soit contrôlable.

### `PMU-Server/Content_Data.zip`

Cette archive n’a pas été ignorée malgré son extension non graphique :

- blob Git : `76a34aff1fcbe96d00b4ad1dc361cb013d6508ed` ;
- SHA-256 des octets obtenus : `e26e411e364fb992042fd1d85df01c40b1458c363b9623d8864df35d3d3914a5` ;
- taille compressée suivie dans Git : 51 512 308 octets ;
- répertoire central : **4 fichiers seulement** — `LoadTableBackup.bat`, `pmu_data.sql`, `pmu_players.sql`, `pmu_schemas.sql` ;
- aucune entrée PNG, tileset, sprite, portrait ou archive secondaire ; 1 155 686 469 octets décompressés, majoritairement `pmu_data.sql`.

Le SQL contient notamment des structures de données `map_data`, `map_tiles` et `rdungeon_tile`, mais pas de paquet graphique stocké comme fichier dans l’archive. Il est donc signalé comme données de jeu/serveur, pas confondu avec un dossier d’art.

## Releases GitHub

Chaque endpoint `/repos/PMUniverse/<repo>/releases?per_page=100` a été parcouru jusqu’à la dernière page. Résultat : **zéro release et zéro asset de release** pour `Installer`, `Updater`, `Scripts`, `framework`, `PMU-Client` et `PMU-Server`. Le registre `release_assets` de `manifest.json` conserve ce résultat par dépôt.

## Provenance et droits : décision de non-vendoring

Il serait incorrect de lire la licence MIT de `PMU-Client`/`PMU-Server` comme une autorisation certaine pour toutes les images :

1. Le dépôt client contient [`Asset Credits.txt`](https://github.com/PMUniverse/PMU-Client/blob/c25c01f9879369647cd5a19731b2e4e5acd33e67/Asset%20Credits.txt). Il distingue explicitement des **« Sprite Rips and Arrangements »**, des sprites custom et des contributions PMU / The Spriters Resource / DeviantArt, sans attribution fichier-par-fichier ni licence de redistribution de chaque pixel.
2. Les visuels sont manifestement liés à Pokémon et une partie est déclarée comme rip. La licence du code ne supprime ni les droits de l’œuvre originale ni les conditions de ses contributeurs.
3. `Installer` est GPL-3.0, mais aucun fichier d’attribution/autorisation distinct pour ses trois visuels n’est présent dans l’arbre. Les TTF et DLL tiers nécessitent aussi leur propre vérification.

**Conséquence appliquée :** le présent dépôt ne redistribue pas le corpus PMUniverse. Il conserve un manifeste reproductible de provenance, les liens de récupération exacts et les hachages. Tout usage effectif devra être précédé d’une clarification auprès des détenteurs des droits ou de l’application des conditions pertinentes. Cela respecte aussi la règle du kit existant : ses visuels finaux restent générés indépendamment, non découpés depuis une référence externe.

## Vérification / récupération contrôlée

Le script [`source/audit_pmuniverse_assets.py`](source/audit_pmuniverse_assets.py) refait l’énumération API et échoue volontairement si un arbre Git est tronqué. Avec les six clones sous `.cache/pmuniverse-audit/clones/`, il vérifie que chaque clone est exactement au commit audité, calcule les SHA-256 de chaque fichier du catalogue, inspecte le ZIP sans l’extraire, et relève les PNG internes des conteneurs PMU.

```bash
python3 source/audit_pmuniverse_assets.py \
  --audit-date 2026-09-13 \
  --checkout-root .cache/pmuniverse-audit/clones \
  --out audit_pmuniverse_assets
```

Les instructions complètes et la définition des catégories sont dans [`audit_pmuniverse_assets/README.md`](audit_pmuniverse_assets/README.md). Les clones restent sous `.cache/` (ignoré) ; seuls les métadonnées, rapports et hachages vérifiables sont versionnés.
