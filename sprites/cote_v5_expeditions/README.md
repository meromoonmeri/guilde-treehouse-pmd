# Métano Expéditions — mod d’édition PMDO 0.8.12

## Contenu prêt à ouvrir

**40 Ground avec toutes leurs ressources :**

- **7 nouvelles falaises** × jour/nuit = 14 Ground ;
- **3 nouvelles entrées de donjon** × jour/nuit = 6 Ground ;
- les **20 Ground du dernier pack Métano/Abyss**, conservés sans modification.

Les anciens lots modulaires et les premiers essais ne sont pas ajoutés : ils restent dans leurs archives distinctes. Ici « 40 Ground » signifie vingt lieux avec deux ambiances, pas quarante lieux différents.

## Installation conseillée — projet séparé

1. Fermer PMDO.
2. Extraire `mod_metano_expeditions_pmdo_0812.zip`.
3. Copier **le dossier entier `metano_expeditions`** dans le dossier `MODS` de PMDO. Ne pas fusionner son contenu avec un autre projet.
4. Dans ce dossier, lancer **`OUVRIR_EDITEUR.bat`** sous Windows. Sous Linux : `bash OUVRIR_EDITEUR.sh`.
5. Dans l’éditeur Ground, ouvrir les fichiers du dossier `Data/Ground/` du projet. Les nouveaux commencent par **`v50812_`** ; les vingt précédents par `v40812_`.

Les lanceurs sélectionnent le projet avec `-dev -quest metano_expeditions`. Le lanceur Windows est fourni mais n’a pas été exécuté ici. On peut aussi sélectionner manuellement **Metano Expeditions - Atelier 0.8.12** en mode développeur.

**Aucun PNG à réimporter, aucun tileset à redimensionner.** Le mod comprend son `Mod.xml`, son index natif complet, huit banques de tuiles, douze fonds et les scripts dans son namespace. C’est un projet de cartes pour l’éditeur, **pas une aventure jouable complète avec scénario**.

## Les nouvelles cartes

Chaque identifiant possède les suffixes `_jour` et `_nuit`.

| Identifiant après `v50812_` | Lieu | Type |
|---|---|---|
| 01_crete_sillage | La crête du Sillage | Crête à deux grands renflements |
| 02_caps_relies | Les caps reliés | Deux caps reliés par un col |
| 03_eventail_strates | L’éventail des strates | Trois terrasses superposées |
| 04_lagune_occident | La lagune d’Occident | Baie ouverte à l’ouest |
| 05_cote_quatre_pointes | La côte aux quatre pointes | Côte découpée et sinueuse |
| 06_sommet_balcon | Le sommet au balcon | Plateau haut et terrasse inférieure |
| 07_cap_chenal | Le cap du Chenal | Faille marine ouverte au sud |
| 08_antre_crochu | L’antre Crochu | Grotte au fond d’un vestibule |
| 09_grotte_marees | La grotte des Marées | Grotte sur une corniche asymétrique |
| 10_defile_brume | Le défilé de Brume | Passage ouvert entre deux épaules |

Les nouveaux layouts sont définis explicitement par des contours organiques. Ils interprètent le guide de composition et les études ; ils ne sont pas les silhouettes exactes de l’image générée. Les dix nouvelles cartes sont en 1168×912 px, grille 146×114 cellules de 8 px. Les masses rejoignent les bords ouest, est et sud ; les baies restent ouvertes.

## Nos entrées : layouts étudiés, textures Métano uniquement

Crooked Cavern apporte l’idée du vestibule central enveloppé de parois. Brine Cave inspire la corniche maritime asymétrique et l’accès reculé. Drenched Bluff inspire le corridor ouvert. **Aucune de leurs textures n’est placée dans nos cartes.**

Les deux grottes emploient le même encadrement natif de Métano Town, à son échelle réelle, dans deux compositions différentes : ce ne sont pas deux sprites d’ouverture redessinés. Le défilé utilise des retours Métano pour encadrer un passage ouvert. Il ne possède pas une fausse porte noire.

Source de l’encadrement : `Metano_Town_Cliffs`, rectangle `(840,416)-(912,544)`. Les pixels d’herbe du prélèvement sont exclus pour ne pas créer une plaque verte flottante sur la paroi. Aucun pixel conservé n’est repeint ou agrandi. Le détail d’entrée reste sur son propre calque.

### Arrivées et seuils

| Carte | Marqueur `entrance` (X,Y) | Marqueur `donjon_seuil` (X,Y) |
|---|---:|---:|
| Antre Crochu | 576,704 | 576,496 |
| Grotte des Marées | 576,720 | 816,568 |
| Défilé de Brume | 576,752 | 576,208 |

Les coordonnées désignent le coin du collider 16×16. Le dégagement et un chemin entre l’arrivée et le seuil sont vérifiés sur la grille pour les trois entrées. Cela reste un test de géométrie, pas un essai de marche dans le moteur graphique.

**Les destinations de donjon ne sont pas configurées : leurs identifiants n’ont pas été fournis.** Les marqueurs ne déclenchent pas une téléportation à eux seuls. `RACCORDEMENT_DONJONS.json` recense les trois raccords à définir ; c’est une fiche de configuration, pas un script exécuté. Il faudra créer/lier les événements dans le projet contenant tes donjons et tester aussi le retour. Nous ne copions pas les scripts narratifs de Palika/EoSO.

## Calques, collisions et animation

Les nouveaux Ground possèdent dix calques de tuiles :

1. Mer animée ;
2. Herbe Métano ;
3. Faces ;
4. Retours ;
5. Couronnes ;
6. Pieds ;
7. Accès de donjon ;
8. Vos sols/chemins — vide ;
9. Vos structures/base — vide ;
10. Vos structures/avant-plan — vide (`Top=4`).

Ciel, astres et nuages sont des fonds indépendants. Mer : huit phases, dix frames moteur par phase. Nuages Guilde/Sharpedo : wrap de 1440 px, −4 px/s. Nuit : **filtre exact d’Abyss V4**, une seule application, sans ombres générées supplémentaires.

Sur les nouvelles cartes, les cellules non entièrement herbeuses et les éléments d’accès sont bloqués. Les arrivées sont libres. Les terrasses séparées peuvent nécessiter tes propres escaliers, rampes ou transitions pour devenir toutes accessibles ; les collisions sont une base à revoir après ajout de structures. Les vingt anciens Ground gardent leurs collisions libres d’origine afin de ne pas modifier ces cartes silencieusement.

## Installation dans un projet existant — facultatif

Ne jamais écraser le `Mod.xml` ou l’`index.idx` de ton projet avec ceux du pack. Fermer PMDO et utiliser Python 3 :

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET"
```

L’installateur fusionne les en-têtes des tilesets, conserve les ressources étrangères, sauvegarde l’index et refuse les fichiers différents déjà présents. Son fonctionnement a été testé dans un projet temporaire, y compris après modification d’une carte.

## Contrôles effectués

- Provenance : reconstruction des six calques depuis les rectangles Métano enregistrés, sans pixels colorés du générateur.
- Filtre : référence Abyss inchangée et comparaisons des feuilles nocturnes.
- Fichiers : reconstruction des 120 nouveaux calques depuis les `.tile`, fonds, frames d’eau, index, marqueurs et collisions.
- Accès : trois chemins avec dégagement 16×16 entre arrivée et seuil.
- Conservation : anciens Ground et ressources byte-à-byte identiques au ZIP Métano/Abyss.
- **Moteur réel PMDO 0.8.12 : 40 Ground désérialisés avec succès**, dimensions, grille, nombre de calques et marqueurs contrôlés.

Ce dernier test emploie le binaire installé depuis RUNTIMEPMDO, sans affichage. **Le rendu GPU, les animations affichées, les déplacements et les lanceurs graphiques ne sont pas validés ici : l’éditeur graphique plante toujours dans cet environnement.** Nous ne présentons pas la désérialisation comme un test de jeu complet.

Rapports inclus : `verification.json`, `access_verification.json`, `runtime_verification.json` et `runtime_results.tsv`. L’aperçu autonome permet de voir les nouveaux et anciens lieux, jour/nuit, calques, grille, zoom natif et exports PNG sans perte. Les motifs des grandes parois sont prolongés par répétition de panneaux natifs ; les raccords restent à apprécier visuellement à 1×.

## Reproduction et manuel

Le mod inclut `MANUEL_METHODE_PMDO.md`, ainsi que cet ajout spécifique aux entrées. Dans le dépôt :

```sh
.venv/bin/python source/cote_v5_expeditions/layouts.py
.venv/bin/python source/cote_v5_expeditions/terrain.py
.venv/bin/python source/cote_v5_expeditions/build.py
.venv/bin/python source/cote_v5_expeditions/make_project.py
.venv/bin/python source/cote_v5_expeditions/verify.py
.venv/bin/python source/cote_v5_expeditions/runtime_test.py
.venv/bin/python source/cote_v5_expeditions/package.py
node source/cote_dix_zones/test_viewer.cjs apercu_metano_expeditions.html
```

Le test moteur suppose l’installation de cache décrite dans `source/pmdo_runtime/README.md`. Les PNG de travail sont régénérables ; ils ne sont pas tous versionnés. Le ZIP et l’aperçu contiennent les ressources finales.

Attributions : Métano / Palika / Halcyon, layouts d’étude Palika et Minemaker0430 / Explorers of Sky Origins, filtre Abyss V4, fonds Guilde/Sharpedo. Les sources publiques ne constituent pas une licence de redistribution sans restrictions ; respecter leurs conditions.
