# Falaises côtières nues — trois calques et deux animations

## Résultat de cette passe

Deux nouveaux terrains ont été produits par le **générateur d’images**, à partir des layouts côtiers précédents et des références graphiques Métano. Bâtiments, arbres, panneaux, clôtures, objets, campement, grottes et chemins ont été retirés. Les zones sont des interprétations des silhouettes, pas des reproductions géométriques exactes.

**Important : le terrain est généré. Ses pixels ne sont PAS une copie vérifiée des tuiles canoniques Métano.** Les contrôles d’export ci-dessous ne changent pas ce statut. Ce lot répond à la génération de falaises nues, à leur isolation et aux calques animés ; il ne certifie pas l’équivalence graphique/structurelle au jeu original.

## Voir les animations

Ouvrir **`apercu_falaises_cotieres_nues.html`** à la racine : fichier autonome avec choix de zone, visibilité des trois calques, pause, avance temporelle, zoom 100 % / 200 % et export PNG des calques visibles. Le damier de transparence n’entre pas dans les PNG.

`APERCU_NE_PAS_IMPORTER.png` est seulement une planche réduite.

## PNG séparés

Dans `01_promontoire/` et `02_terrasse/` :

- `COTE01_02_TERRAIN_GENERE.png` / `COTE02_02_TERRAIN_GENERE.png` : **herbe + falaises**, fond transparent. Pas de structure ni d’arbre. Herbe et roche restent ensemble dans ce calque ; elles ne sont pas faussement séparées par couleur.
- `COTE01_00_CIEL_01.png` à `08.png` (idem COTE02) : **8 phases du ciel**, positions 0, 2, 4, 6, 8, 6, 4, 2 px, 600 ms par phase.
- `COTE01_01_MER_01.png` à `05.png` (idem COTE02) : **5 phases de mer**, 150 ms par phase.
- `COTE01_COMPOSITION_FIXE.png` / `COTE02_COMPOSITION_FIXE.png` : première composition de contrôle, pas un fichier animé.

Ordre de superposition : **ciel → mer → terrain**. Chaque calque d’une zone possède exactement les mêmes dimensions et l’origine (0,0).

- Promontoire : **1312 × 816 px**.
- Terrasse : **1200 × 896 px**.

Aucun sprite d’export n’a été redimensionné. Le promontoire généré a été **translaté de 256 px vers le bas**, avec rognage au bord inférieur du canevas, pour laisser place au ciel et replacer le plateau dans la composition côtière. Cette opération ne change pas la taille de ses pixels ; elle ne constitue pas pour autant un étalonnage à la taille d’un Pokémon en jeu.

## Origine des fonds animés

La mer et le ciel proviennent de la planche **`IMG_4890.png` fournie par l’utilisateur dans le commit `3bc185b`**, copiée sous `source/falaises_cotieres_nues/reference_ciel_mer.png`. Il s’agit de la planche *Pelipper Post Office*, créditant Nintendo, Game Freak, Chunsoft et l’extraction par **Jaxster**.

- Ciel : rectangle (544,8)–(1264,216), répété horizontalement et déplacé doucement.
- Mer lointaine : cinq bandes de 48 × 128 px.
- Mer proche : cinq bandes de 48 × 168 px, répétées après la bande lointaine.

Les rectangles exacts sont consignés dans `manifest.json`. **Ce ne sont pas les animations de rivière de Métano.** L’ordre de lecture et les cadences sont proposés pour ce lot ; ils n’ont pas été récupérés depuis les métadonnées du jeu. Le ciel oscille lentement, il ne s’agit pas d’un cycle météorologique ni d’un défilement infini de nuages.

Les sources générées à fond magenta restent dans `source/falaises_cotieres_nues/`. Seul le fond magenta a été supprimé ; les pixels visibles conservés n’ont pas été recolorés.

## Pour PMDO

Les dimensions sont divisibles par **8** et les noms de feuilles sont uniques. Pour tester via PNG to Tileset, importer les fichiers de calques avec une taille de cellule de 8 px, sans changer leur taille. Ne pas importer la planche d’aperçu, ni les images sources à fond magenta.

**Importer les PNG ne configure pas automatiquement les animations.** Les séquences de frames de ciel et de mer doivent être configurées dans le moteur ; les noms, l’ordre et les durées sont fournis dans le manifeste. Les deux séquences sont indépendantes. Ce lot ne contient pas de Ground map PMDO ni d’animation Aseprite prête à l’emploi.

Aucun test dans l’installation PMDO de l’utilisateur n’a été exécuté. Les raccords des fonds répétés et l’échelle du terrain généré restent à valider en jeu. Respecter les conditions des ressources et les crédits originaux.

## Contrôles et reconstruction

```sh
.venv/bin/python source/build_falaises_cotieres_nues.py
.venv/bin/python source/verify_falaises_cotieres_nues.py
```

Dépendances : Pillow et numpy. Le build réutilise les sorties du générateur conservées, sans rappeler le service de génération.

`verification.json` contrôle :
- les dimensions et l’alignement de tous les calques ;
- l’identité des pixels générés conservés après suppression du magenta et placement ;
- la recomposition des fonds depuis les rectangles de la planche fournie ;
- l’identité du rendu fixe avec la superposition des trois calques ;
- cinq phases de mer distinctes et cinq positions de ciel réparties sur huit frames ;
- des noms d’export uniques.

Le JavaScript a été contrôlé syntaxiquement avec Node. Ces vérifications ne constituent ni un test interactif navigateur/moteur, ni une certification de tuiles Métano canoniques.
