# Audit des textures et animations PMD Sky & Manuel d'adoption PMDO

**Date de réalisation :** 25 septembre 2026  
**Sources auditées :**
- Galerie Project Pokémon : [PMD Explorers of Sky Gallery](https://projectpokemon.org/home/gallery/category/12-pok%C3%A9mon-mystery-dungeon-explorers-of-sky/)
- Dépôt de portage NDS → PMDO : [`meromoonmeri/PMD-SKY-PMDO-PORT`](https://github.com/meromoonmeri/PMD-SKY-PMDO-PORT) (commit `d62110a`, 465 Grounds, 569 Tilesets)
- Outil d'extraction local développé : [`tools/sky_texture_extractor.py`](tools/sky_texture_extractor.py)

---

## 1. Audit complet du site Project Pokémon (Explorers of Sky)

La galerie Project Pokémon référence l'ensemble des graphismes de fond et d'environnements extraits de la ROM NDS de *Pokémon Mystery Dungeon: Explorers of Sky*.

### 1.1 Organisation des albums

| ID Album | Intitulé de l'album | Nb d'images | Format | Rôle exact |
|---|---|---|---|---|
| **909** | **Dungeon Tilesets** | 144 images | PNG indexé statique (`tilesetXXX.dpc.png`) | Tilesets de donjons procéduraux (mappa / DTEF). Destinés aux étages générés aléatoirement, **pas aux Ground Maps fixes**. |
| **908** | **(Animated) Map Backgrounds (GIF)** | 42 images | GIF animé | Cartes fixes avec tuiles et palettes animées (eau, cascades, lave, torches). Cycle complet visualisable. |
| **879** | **Animated Map Backgrounds** | 40 images | APNG (Animated PNG) | Rips animés haute fidélité par @MegaMinerd (eau, reflets, ciel). |
| **878** | **Map Backgrounds** | 338 images | PNG statique | Fonds de scènes statiques, intérieurs et paysages sans tuiles animées. |
| **837** | **Promo Images** | 6 images | JPEG | Illustrations promotionnelles et visuels de boîte (hors-moteur). |
| **840** | **Rescue Team Menu Backgrounds** | 2 images | PNG | Reliques d'écrans de menus issus de Rouge/Bleu (non utilisés). |

---

### 1.2 Décodage complet de la nomenclature Chunsoft NDS

Les noms de fichiers NDS de Chunsoft obéissent à un système de codage standardisé :  
`[Préfixe][Groupe (2 chiffres)][Panneau / Plan (P + 2 chiffres)][Variante (Lettre)]`

#### Les préfixes et leur statut PMDO :

| Préfixe | Type NDS | Statut dans PMDO | Description & Rôle |
|---|---|---|---|
| **`D`** | **Dungeon Ground** | **✅ MAP JOUABLE (Ground)** | Cartes fixes de donjons : entrées (`entrance`), carrefours de repos (`ledge`, `gem`, `shore`), salles de boss (`pit`, `peak`), transitions d'étages. Exploration directe par le joueur avec collisions. |
| **`T`** | **Town / Hub Ground** | **✅ MAP JOUABLE (Ground)** | Lieux de vie et villages : Bourg-Trésor (`T00P01`), Falaise Sharpedo (`T01P02A`), Étang Barbicha, carrefours, extérieur de la Guilde. Cartes jouables complètes. |
| **`S`** | **Special Episode Ground** | **✅ MAP JOUABLE (Ground) / BG** | Lieux des 5 Épisodes Spéciaux d'Explorateurs du Ciel (Igglybuff, Armaldo, Massko/Noctunoir). Jouables ou cinématiques selon le marqueur. |
| **`V`** | **Vignette / Cutscene BG** | **ℹ️ FOND CINÉMATIQUE (BG)** | Fonds d'événements scénarisés (souvenirs, rêves, révélations narratives). Destinés au calque `Background` ou scènes de dialogue, **sans grille de collision standard**. |
| **`P`** | **Panorama / Picture** | **ℹ️ FOND / DÉCOR LOINTAIN** | Grandes fresques d'arrière-plan, vues plongeantes de falaise, ciels étoilés, écrans de titre ou de chapitres. |
| **`tileset*.dpc`** | **Dungeon Procedural Chunk** | **⚙️ TILESET PROCÉDURAL** | Dédié aux étages aléatoires du moteur de donjon (DTEF). Ne possède pas de layout de Ground préétabli. |

#### Correspondance des cartes emblématiques auditées :

- **`D06P11A`** : *Waterfall Cave* (Grotte Cascade) — 552×360 px (69×45 tuiles 8px / 23×15 chunks 24px)
- **`D14P11A`** : *Steam Cave* (Grotte Vapeur) — 456×384 px (57×48 tuiles 8px / 19×16 chunks 24px) — 6 frames d'animation lave/vapeur
- **`D17P33A`** : *Brine Cave* (Grotte Saumâtre) — 456×504 px (57×63 tuiles 8px / 19×21 chunks 24px) — 12 frames d'animation d'eau
- **`D25P11A`** : Grande cascade / rivière — 648×504 px (81×63 tuiles 8px) — 30 frames d'animation
- **`T00P01`** : *Treasure Town* (Bourg-Trésor) — 960×720 px (120×90 tuiles 8px / 40×30 chunks 24px) — 6 frames d'animation
- **`T01P02A`** : *Whiscash Pond* (Étang Barbicha) — 552×504 px (69×63 tuiles 8px) — 4 frames d'animation

> **Règle fondamentale des dimensions :**  
> Toutes les cartes NDS sont des multiples stricts de **24 px** (un chunk de 3×3 tuiles) et donc de **8 px** (la tuile de base). Aucun resampling ou taille bâtarde n'existe dans les données canoniques.

---

## 2. Audit approfondi du dépôt `meromoonmeri/PMD-SKY-PMDO-PORT`

Le dépôt `meromoonmeri/PMD-SKY-PMDO-PORT` (commit `d62110a`) constitue la conversion automatisée officielle et vérifiée des 458 cartes MAP_BG de la ROM vers le format natif PMDO RogueEssence.

### 2.1 Anatomie des fichiers sources NDS

Dans la ROM NDS, une carte MAP_BG est composée de 4 types de fichiers :
1. **`.bpl`** : Palettes de 16 couleurs RGBA (la première couleur étant transparente).
2. **`.bpc`** : Cellules graphiques de 8×8 px en 4bpp, regroupées en chunks de 24×24 px (3×3 tuiles).
3. **`.bma`** : Matrice d'assemblage du décor (couches) et matrice de **collision** (bits d'obstacles).
4. **`.bpa`** (1 à 8 slots) : Données d'animation temporelle. Chaque slot remplace un jeu de tuiles de la VRAM frame par frame (eau en mouvement, lave bouillonnante, torches scintillantes).

---

### 2.2 Comment `PMD-SKY-PMDO-PORT` gère l'animation

Dans le script `tools/convert_nds_map.py` de ce repo :

1. **Compilation de la planche `.tile` unique (déduplication 8×8 RGBA) :**
   Toutes les frames d'animation sont rendues via `skytemple-files` (`bma.to_pil`). Chaque tuile de 8×8 px de chaque frame est découpée et comparée. Les tuiles identiques sont dédupliquées par leur contenu binaire RGBA. La planche binaire `.tile` stocke ainsi uniquement l'ensemble des tuiles uniques (statiques et animées confondues).

2. **Structure des cellules animées dans le `.rsground` :**
   Dans le fichier JSON `.rsground`, chaque cellule de la grille `Layers[0].Tiles[x][y]` dispose d'une liste de frames :
   ```json
   {
     "AutoTileset": "",
     "Associates": [],
     "Layers": [
       {
         "Frames": [
           {"Sheet": "D17p33a_Base", "TexLoc": {"X": 44, "Y": 0}},
           {"Sheet": "D17p33a_Base", "TexLoc": {"X": 51, "Y": 40}}
         ],
         "FrameLength": 10
       }
     ],
     "NeighborCode": -1
   }
   ```
   - **`FrameLength: 10`** : Cadence standard pour les tuiles animées (10 ticks RogueEssence à 60 FPS = **166.7 ms** par frame, idéal pour l'eau et les cascades).
   - **`FrameLength: 60`** : Attribué aux tuiles statiques (1 seule frame).

3. **Traitement des collisions :**
   - **Maps de jeu (`bma_obj.collision` présente) :** Les collisions sont extraites bit à bit depuis le BMA (`Tags: 1` = obstacle, `Tags: 0` = marchable).
   - **Maps cinématiques / Arènes procédurales (`bma_obj.collision` absente) :** `Tags = 0` partout (`collision_source=NONE`). **Aucune fausse collision n'est inventée.**

---

## 3. Comment adopter cette méthode dans notre pipeline PMDO 0.8.12

Pour enrichir ou créer nos nouvelles zones PMD en réutilisant ces textures et animations (selon les règles de [`METHODE_PRODUCTION_MAPS_PMD.md`](METHODE_PRODUCTION_MAPS_PMD.md)) :

### 3.1 Deux modes d'adoption possibles

#### Mode 1 — Réutilisation directe d'un Ground canonique Sky
Si nous devons intégrer tel quel un lieu de Sky (par exemple l'entrée de *Steam Cave* ou *Brine Cave*) :
1. Récupérer directement `output/Grounds/<map>.rsground` et `output/Tiles/<sheet>.tile` depuis `PMD-SKY-PMDO-PORT`.
2. Conserver les collisions BMA exactes et les 2114 tuiles animées natives.

#### Mode 2 — Extraction multi-calques pour nouvelles compositions hybrides
Lorsque nous créons de **nouvelles zones** (ex. nouvelles falaises, nouvelles entrées de donjons, cascades hybrides Métano/Sky) :
1. **Extraction des zones animées par phase :**  
   Utiliser [`tools/sky_texture_extractor.py`](tools/sky_texture_extractor.py) pour séparer automatiquement :
   - `01_sol_parois_statiques.png` (la roche et le sol statiques)
   - `02_animation_phase_01.png` à `02_animation_phase_N.png` (l'eau, la lave ou les effets découpés sur fond transparent).
2. **Recomposition en modules natifs 8 px :**
   - Ne jamais déformer ou rééchantillonner les tuiles extraites.
   - Assembler le terrain sur grille stricte de 8 px (par exemple 4 phases d'animation d'eau bouclées à 10 ticks = 166 ms ou 200 ms).
3. **Application du filtre Nuit Abyss (`tools/tile_night.py`) :**  
   Pour les variantes nocturnes d'un biome Sky, appliquer la matrice colorimétrique Abyss sur les tuiles natives extraites de jour afin de conserver un raccord parfait avec les zones Métano Nuit.

---

## 4. Boîte à outils développée : `tools/sky_texture_extractor.py`

Un script d'audit et d'extraction opérationnel a été ajouté au dépôt dans [`tools/sky_texture_extractor.py`](tools/sky_texture_extractor.py).

### Commandes disponibles :

```bash
# 1. Auditer une ressource Sky (dimensions, tuiles 8px, statut jouable, détection des tuiles animées)
python3 tools/sky_texture_extractor.py large.D14P11A.gif.de6fb5fd180b164fe8a67715f1d7ee5c.gif

# 2. Auditer et extraire les calques transparents séparés (base + phases animées)
python3 tools/sky_texture_extractor.py large.D14P11A.gif.de6fb5fd180b164fe8a67715f1d7ee5c.gif --extract renders/steam_cave_extracted/

# 3. Sortie au format JSON pour script automatisé
python3 tools/sky_texture_extractor.py large.D17P33A.gif.188f8399cf4c18292d9ecdd2454bcd10.gif --json
```

### Exemple de résultat d'audit (`D14P11A` — Steam Cave) :
- **Dimensions :** 456×384 px (57×48 cellules de 8 px)
- **Classification :** Dungeon Ground Map (Carte de donjon jouable)
- **Animation :** 6 phases
- **Tuiles animées :** 601 tuiles (21.97% de la surface de la carte)
- **Export généré :** `01_sol_parois_statiques.png` + 6 fichiers `02_animation_phase_01.png` à `06.png` transparents.

---

## 5. Synthèse des règles à appliquer pour les futures zones

1. **Vérifier le préfixe** : Utiliser en priorité les cartes `D` (donjons) et `T` (villes) pour le terrain explorable ; réserver `V` et `P` pour les fonds et panoramas lointains.
2. **Respecter la cadence d'animation** : Paramétrer `FrameLength: 10` sous PMDO pour les calques d'eau/lave animés (équivalent à ~166–200 ms).
3. **Conserver la grille 8 px / 24 px** : Toute nouvelle carte doit avoir une largeur et une hauteur strictement divisibles par 8 (et de préférence par 24 pour respecter les chunks originaux).
4. **Isoler les calques d'effets** : Séparer toujours le sol statique des tuiles animées pour permettre la désérialisation propre et l'édition dans l'éditeur PMDO Dev.
