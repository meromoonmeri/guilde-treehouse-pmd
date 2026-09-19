# Sprites de Pond (Mares & Étangs) PMD Métano Town / Treasure Town pour Falaises

Ensemble de sprites et tilesets natifs créés spécialement pour aménager des pièces d'eau, mares et étangs sur des promontoires, falaises et terrasses rocheuses dans le style authentique de **Bourg-Trésor / Métano Town (PMD Explorers / PMDO)**.

Tous les assets respectent rigoureusement les normes du projet et du moteur PMDO :
- Grille native stricte de **8 × 8 px**.
- Dimensions strictement divisibles par 8.
- Format RGBA **straight alpha** (aucun halo noir ni prémultiplication).
- Palette canonique et pixels natifs extraits sans redimensionnement arbitraire ni filtre flou.
- Noms de fichiers uniques avec préfixe `METANO_CLIFF_POND_*` (compatibilité avec le chargeur de tilesets PMDO).
- Cadence d'animation native de **4 frames à 10 ticks par phase** (~167 ms à 60 Hz).

---

## 1. Contenu du Pack

### A. Les 5 Modules d'Étangs Préfabriqués

| Dossier / Fichier | Dimensions (px) | Grille (tuiles 8px) | Description & Usage falaise |
|---|---|---|---|
| `01_promontoire/` | 80 × 64 | 10 × 8 | **Petite mare de promontoire** : idéale pour les saillies étroites, promontoires et terrasses de falaise avec rebord sud plongeant dans le vide. |
| `02_alcove/` | 144 × 112 | 18 × 14 | **Étang d'alcôve de paroi** : adossé directement à une haute paroi de falaise nord (avec ombre portée sur l'eau) et traversé par 3 pierres de gué. |
| `03_cascade/` | 208 × 160 | 26 × 20 | **Grand bassin scénique** : alimenté par une cascade supérieure avec remous d'écume, grand rocher insulaire, et déversoir sud vers le vide. |
| `04_cuvette_rocheuse/` | 112 × 88 | 14 × 11 | **Cuvette rocheuse pure (100% minérale)** : bassin creusé dans la roche brute sans herbe, pour hauteurs rocailleuses, grottes et pics escarpés. |
| `05_deversoir/` | 64 × 96 | 8 × 12 | **Déversoir & chute de falaise** : module de bord de falaise pour faire déborder un étang en cascade verticale vers le niveau inférieur. |

Chaque module contient :
- `*_SCENE.png` : Rendu complet prêt à l'emploi.
- `*_SOL.png` / `*_FALAISE.png` / `*_ROCHE.png` : Calque de terrain statique (base).
- `*_EAU_F1..F4.png` : Calque de surface d'eau transparent (4 frames d'animation).
- `*_CASCADE_F1..F4.png` : Calque des chutes et écume animées (si applicable).
- `*_OBJETS.png` : Pierres de gué, rochers émergés, nénuphars.
- `*_ANIMATION.gif` : Aperçu animé en boucle à 167 ms.
- `*_SCENE.tile` : Fichier binaire natif PMDO 0.8.12.
- `*_SCENE.tsj` : Tileset JSON Tiled avec métadonnées d'animation.

---

### B. Tileset Modulaire Complet : `METANO_POND_CLIFF_TILESET`

- **Fichier image :** `METANO_POND_CLIFF_TILESET.png` (192 × 192 px — 24 × 24 tuiles = 576 tuiles).
- **Atlas animé 4 phases :** `METANO_POND_CLIFF_TILESET_ANIM_4F.png` (192 × 768 px).
- **Format natif PMDO :** `METANO_POND_CLIFF_TILESET.tile`.
- **Format Tiled :** `METANO_POND_CLIFF_TILESET.tsj` (avec 128 définitions d'animation d'eau à 167 ms).

#### Organisation des tuiles :
1. **Lignes 0 à 3, Colonnes 0 à 7 :** Paroi de falaise plongeant dans l'eau (ombre portée, roche immergée au pied, coins).
2. **Lignes 0 à 3, Colonnes 8 à 15 :** Berges rocheuses de falaise (rebords sud, berges ouest/est, coins rocheux).
3. **Lignes 4 à 7, Colonnes 0 à 15 :** Berges herbeuses Métano complètes (N, S, E, O, coins intérieurs et extérieurs).
4. **Lignes 8 à 15, Colonnes 0 à 15 :** Eau de mare animée (eau profonde, eau peu profonde translucide, reflets, clapotis).
5. **Lignes 16 à 23, Colonnes 0 à 7 :** Cascades, déversoirs (seuil en pierre, chutes verticales, écume).
6. **Lignes 16 à 23, Colonnes 8 à 15 :** Pierres de gué (pas japonais), rochers naturels, nénuphars et touffes de berge.
7. **Colonnes 16 à 23, Lignes 0 à 23 :** Raccords de terrain (herbe pure, haut de falaise, pied de falaise).

---

## 2. Guide d'Importation dans PMDO Dev

### Méthode 1 : Via l'outil "PNG to Tileset"
1. Ouvrez PMDO Dev et lancez l'éditeur de terrain.
2. Cliquez sur **Import PNG to Tileset**.
3. Sélectionnez le fichier PNG désiré (par exemple `METANO_POND_CLIFF_TILESET.png` ou l'un des prefabs `*_SCENE.png`).
4. Réglez impérativement la taille de tuile sur **8 px**.
5. Validez l'importation. Les tuiles s'insèrent directement dans la palette de l'éditeur sans aucun redimensionnement.

### Méthode 2 : Import par Calques (Multi-Layer)
Pour bénéficier des animations d'eau synchronisées :
- **Calque 1 (Ground / Base) :** Placez le fichier `*_SOL.png` ou `*_FALAISE.png`.
- **Calque 2 (River / Eau animée) :** Placez les frames `*_EAU_F1.png` à `F4.png` avec durée de 10 ticks (166 ms).
- **Calque 3 (Cascades animées) :** Si présent, placez `*_CASCADE_F1.png` à `F4.png`.
- **Calque 4 (Objects Under / Objects) :** Placez le calque `*_OBJETS.png` (pierres de gué et rochers) afin que les Pokémon puissent marcher dessus ou contourner l'eau.

---

## 3. Visualisation Interactive

Ouvrez le fichier **`apercu_pond_metano_cliffs.html`** à la racine du dépôt dans votre navigateur web pour :
- Tester les animations à 60 Hz avec lecture / pause / frame par frame.
- Zoomer à 1× (natif), 2×, 3× ou 4× pixel-art.
- Activer la grille 8 px d'un clic.
- Afficher / masquer les calques de chaque étang indépendamment.
- Visualiser la scène d'intégration sur terrasse de falaise.
