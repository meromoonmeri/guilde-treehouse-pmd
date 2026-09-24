# État des lieux — reprise de la création de maps (22 septembre 2026)

Relecture complète de `README.md`, `AGENTS.md`, `MANUEL_METHODE_PMDO.md`, des README de `renders/`, `exports/`, `sprites/`, `source/`, des scripts et des deux `.rsground` déposés à la racine. Ce document résume ce qui existe, ce qui est utilisable pour des maps **aux textures canoniques**, et ce qui reste ouvert. Il ne déclare rien de validé en jeu.

## 1. Ce que l’utilisateur construit réellement (fichiers `.rsground` de la racine)

| Carte | Nom interne | Taille | Calques | Feuilles utilisées |
|---|---|---|---|---|
| `cliffdaytest.rsground` | `CliffReverietownnordest` | 123×99 cellules = **984×792 px**, TexSize 1 | 6 calques de tuiles, 3 spawners | `00_ciel`, `v2_promontoire_jour_03`, **`Metano_Town_Cliffs`**, **`Metano_Town_Objects`**, **`Metano_Town_Animation_Tileset`**, `INVERSEPATHWAY`, `CLIFF MIROR-Photoroom`, `13_avancee_basse_gauche_terrain`, `01_long_cap_jour_02`, `CanyonCamp`, `Metano_Inn_Objects`, `Metano_Town_Trimmed`, `Metano_Town_Animated`, `Altere_Pond_Objects(_Under)`, `P01P01A_layer1` |
| `cliffnordouesttest1.rsground` | *(sans nom)* | 138×98 cellules = **1104×784 px**, TexSize 1 | 4 calques | `00_ciel`, `v2_promontoire_jour_03`, `Metano_Altere_Transition_Base`, `terrain`, `terrain (2/3/4)`, `INVERSEPATHWAY`, `Metano_Town_Animation_Tileset` |

Lecture : un village de falaises « Reverie Town » (versants nord-est / nord-ouest) construit dans l’éditeur PMDO avec les tuiles **Métano** (Halcyon) pour les objets, l’herbe et les faces, complété par des feuilles maison (`CLIFF MIROR-Photoroom`, `INVERSEPATHWAY` = falaises retournées à la main faute de modules natifs dans l’autre sens) et par des PNG de ce dépôt importés via « PNG to Tileset ». Rendu partiel des couches disponibles : `banque_canonique/cartes_natives/cliffdaytest*.png`. Les feuilles maison ne sont pas dans le dépôt : pour reproduire ces deux cartes à l’identique il faudrait les `.tile` correspondants du dossier `Content/Tile` du mod.

## 2. Textures canoniques disponibles dans le dépôt (banque centralisée)

`banque_canonique/` — construit par `tools/banque_canonique.py` ; navigation : `banque_canonique/index.html`, tableau : `banque_canonique/INVENTAIRE.md`.

- **89 feuilles `.tile` dédoublonnées → atlas PNG 1:1 en alpha droit** (`banque_canonique/atlas/`). Aucun pixel recoloré, tourné, retourné ou redimensionné.
- **Halcyon (commit 1522c7a8)** : Métano Town (Base 1512×1512, Cliffs, Fringe, Objects, Animation_Tileset, River_Animation_1–4, Sparkles, et versions `_Night` d’Abyss V4), Altere Pond (Base, Cliffs, Fringe, Objects/Over/Under, River, River_Animations, Shadows), Vast Steppe (Base, Cliffs, Fringe, Objects, Objects_Under, Flower_Animations), Crooked Cavern (Base, Objects, Shadows), Relic Forest / Illuminant Riverbed (bases Ground), intérieurs (Café Métano, Spinda Café, Guild Second Floor, Ledian Dojo).
- **Explorers of Sky Origins** : Brine Cave Entrance (tuiles 24 px, TexSize 3), Drenched Bluff (Background + Details).
- **Donjons PMDO (DumpAsset 3e767571)** : autotiles 24 px de Treeshroud Forest 1, Southern Jungle, Murky Forest, Southern Cavern 1, Crystal Cave 1, Vast Ice Mountain, Dark Crater, Quicksand Cave, Sealed Ruin, Steam Cave, Sky Peak 4th Pass, Apple Woods, Beach Cave, avec leurs couches animées (gabarits DTEF 47 cases dans `renders/donjons_dtef_v2/references_dtef/`).
- **9 cartes natives rendues** depuis leurs `.rsground` (phase 0) pour étudier la construction canonique : Vast Steppe entrance 512×512, Altere Pond 928×768, Crooked Cavern 320×240, Drenched Bluff 528×408, Brine Cave 648×504, Café Métano, Spinda Café, Guild Second Floor, Ledian Dojo — composition et **chaque calque séparé** (`banque_canonique/cartes_natives/`).
- **50 références PNG canoniques** déposées par l’utilisateur à la racine (maps PMD Sky / Rescue Team, Spriters Resource) : inventoriées avec vignettes (`banque_canonique/references_png/`). Ce sont des captures aplaties : pixels canoniques, mais sans calques ni phases d’animation (sauf les GIF).
- Feuilles **construites par ce dépôt** (copies vérifiées ou assemblages : `Metano_Canonique_8px`, `Zones_Guidees_Canon_8px`, `Extension_Metano`, `Falaises_Metano_Modules`, ponts, maisons, cascades/rivière Métano) : listées à part, à ne pas confondre avec les natives.

## 3. Outils

| Outil | Rôle |
|---|---|
| `tools/pmdo_tiles.py decode / inventory` | lit les `.tile` (format audité : int32 tileSize, int32 count, enregistrements x,y,offset int64, PNG prémultipliés) et écrit des atlas 1:1 en alpha droit |
| `tools/pmdo_tiles.py render carte.rsground --sheets …` | rend une carte Ground (toutes phases, TexSize 1 ou 3), composition + calques séparés, liste les feuilles absentes |
| `tools/banque_canonique.py` | reconstruit toute la banque + inventaire + galerie |
| `source/pmdo_cote/build.py`, `INSTALLER.py` | **écriture** de vrais `.tile` / `.dir` / `.rsground` / `index.idx` PMDO 0.8.12 (banques de tuiles dédoublonnées, prémultiplication, installateur qui préserve l’index existant) |
| `source/cote_v4_abyss/night.py` | filtre nuit exact d’Abyss (vérifié sur les feuilles `_Night`) |
| `source/donjons_dtef_v2/*.py`, `source/dungeon_autotiles_v1/*.py` | export DTEF 47 cases, couches animées, import `./PMDO -raw … -convert autotile` documenté |
| `source/zones_south_north_v3/`, `source/zones_relayout_v*/` | relayouts « pixels natifs » avec traçabilité NPZ `source_xy` par pixel |
| `source/pmdo_runtime/verify_ground_runtime.py` | chargement des Ground par le vrai moteur (sans GPU) — moteur non présent dans ce bac à sable, à réinstaller si besoin |
| `.venv/` | Python 3.11 + Pillow 12, NumPy 2.4, SciPy 1.17 (reconstruite ; ignorée par Git) |

## 4. Règles en vigueur pour les maps « textures canoniques » (synthèse d’AGENTS.md / MANUEL)

1. Pixels de jour **natifs** : pas de recoloration, rotation, miroir, agrandissement ni repeint. La nuit = filtre Abyss exact, une seule fois.
2. **Modules complets** (sommet, face, pied, retours, couronnes) étalonnés à la source, pas une mosaïque de fragments 8 px ; l’échelle se vérifie à 1× contre un témoin natif.
3. Grille 8 px, dimensions divisibles, noms de fichiers **uniques** (l’importeur « PNG to Tileset » nomme par basename et écrase les homonymes), import documenté en 8 px.
4. Livraison en **calques séparés** : sol / chemins / parois / bordures / berges / eau (4 phases natives) / objets / ombres / avant-plan (`Top`), origine commune, versions sèches sans eau ni chemin quand pertinent.
5. Une entrée de donjon : arrivée **sud**, objectif/grotte au **nord**, parvis dégagé, seuil lisible à la taille du personnage ; collisions et warps restent à dessiner dans l’éditeur.
6. Provenance conservée (dépôt, commit, SHA-256), contrôles de recomposition exacte ; « 0 différence de pixel » prouve l’origine, pas la qualité des raccords — inspection visuelle à 1× obligatoire, et aucun test moteur revendiqué s’il n’a pas eu lieu.

## 5. Chantiers ouverts (d’après les suivis existants)

- **Reverie Town** (fichiers de l’utilisateur) : les faces Métano n’existent nativement qu’orientées sud avec retours arrondis gauche/droite (feuille `Metano_Town_Cliffs`, 1512×544) ; Altere Pond apporte une deuxième matière ocre avec escalier et cascade ; Vast Steppe une rampe herbeuse. Il n’existe pas dans les feuilles natives de kit complet « toutes orientations » : c’est le manque que comblaient les miroirs maison.
- **Programme des 23 références PMD Sky** (`exports/zones_south_north_v3/FULL_PROGRAMME_STATUS.json`) : 2 entrées sud→nord livrées (forêt/grotte, passage rocheux bleu), 1 fond nuit réagencé, aurore préparée ; **18 layouts encore à produire** (arène plage, entrée aride, route glacée, chambre, jungle aux cascades, lac cristal, caverne sombre, clairière tropicale, couloir violet, salle dorée, arène de glace, grotte à deux issues, roches/évents, jardin secret, grotte étoilée, souterrain dallé, bassin chauffant, aurore).
- **Donjons** : 10 biomes DTEF natifs (V2) + variantes texture-bombing (V2/V3) + 4 designs générés (V4) ; import moteur jamais exécuté.
- Arène de glace / aurores : V16 livrée (méthode « rendus générés »), non validée.

## 6. Prochaine étape proposée

Choisir le chantier (Reverie Town / entrées sud→nord / zones Halcyon / donjons), le format (PNG calques 8 px pour l’importeur, pack natif `.rsground`+`.tile`, ou les deux) et jour seul ou jour+nuit. Chaque map suivra : plan de layout sur grille 8 px → assemblage avec modules natifs complets → calques séparés + composition → contrôles (provenance, recomposition, contacts, chemin sud→nord) → aperçu HTML + PNG + pack.

## 7. Mise à jour du 24 septembre 2026 — Jardin secret v1

Premier layout agrandi construit avec les **textures de sa propre référence** (`secretgarden.png`) : `renders/jardin_secret_v1/` (816×1152, 8 calques jour/nuit), galerie `apercu_jardin_secret_v1.html`. Le moteur `source/jardin_secret_v1/quilt.py` peut servir aux 17 autres références PMD Sky du programme (`FULL_PROGRAMME_STATUS.json`), en adaptant la segmentation et les caractéristiques de guidage à chacune.

## 8. Mise à jour du 24 septembre 2026 — Jardin secret v2 (méthode spriter magenta)

`renders/jardin_secret_v2/` + `apercu_jardin_secret_v2.html` : chemin droit, feuillage immersif, arbres à l'échelle Halcyon, fleurs animées sur calques propres, hokora de Celebi sur la souche. Calques générés sur magenta et assemblés (rayon natif). all_pass, PMDO non testé.
