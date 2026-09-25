# Steam Cave — Nouveau Layout d'Entrée & Fumerolles Natives (V1)

Ce dossier présente une nouvelle proposition de layout pour l'entrée extérieure de **Steam Cave** (Grotte Vapeur), légèrement différente de la référence originale mais reconstruite à 100% avec les **mêmes textures et tuiles natives**.

---

## 1. Références canoniques & Spécifications

- **Référence principale :** `Steam_Cave_entrance_TDS.png` (504×440 px, Pokémon Mystery Dungeon Sky).
- **Référence d'animation :** `large.D14P11A.gif` (456×384 px, 6 frames d'animation vapeur/fumerolles).
- **Filtre nuit certifié :** `tools/tile_night.py` (transformation colorimétrique New Era Abyss blob `438383f4`).
- **Dimensions finales :** **504 × 432 px** (63 × 54 tuiles de 8 px / 21 × 18 chunks de 24 px). Dimensions strictement conformes et divisibles.

---

## 2. Principes du nouveau layout par rapport à la référence

| Caractéristique | Référence originale (`Steam_Cave_entrance_TDS.png`) | Nouveau layout proposé (`steam_cave_nouveau_layout_v1`) |
|---|---|---|
| **Symétrie** | Centrée et quasi-symétrique. | **Asymétrique et organique** : relief escarpé plus dense à l'ouest, gorge naturelle. |
| **Porche de la grotte** | Plein centre (X=252, Y=128). | **Décalé au nord-centre/est** (X=288, Y=80) sous un auvent rocheux proéminent. |
| **Progression du sentier** | Couloir rectiligne vertical sud → nord. | **Progression en baïonnette** : arrivée sud-ouest, franchissement de terrasse, contournement des fumerolles, ascension vers le porche. |
| **Éléments géothermiques** | Statiques dans l'image de base. | **Bassin hydrothermal actif et fumerolles animées** en 6 phases natives (166.7 ms / 10 ticks PMDO). |
| **Belvédère** | Pas de point de vue dégagé. | **Corniche rocheuse en belvédère** à l'est, ouvrant sur la perspective volcanique. |

---

## 3. Décomposition des 12 calques transparents

Tous les calques sont au format PNG RGBA 504×432 px et disponibles en versions **Jour** (`calques_jour/`) et **Nuit Abyss** (`calques_nuit/`) :

1. `01_falaises_arriere_plan.png` : Massif supérieur de la montagne volcanique et ciel de brume.
2. `02_sol_terrasses_volcaniques.png` : Plaque de sol intégrale reconstituée sous le relief pour permettre l'édition.
3. `03_parois_falaises.png` : Parois rocheuses étagées, corniches et promontoires découpés.
4. `04_porche_grotte.png` : Seuil de la caverne avec auvent de basalte et pénombre d'entrée.
5. `05_chemins_et_dalles.png` : Sentier d'approche en dalles volcaniques et marches d'accès.
6. `06_bassin_fumerolles.png` : Bassin rocheux et évents de soufre.
7. `07_vapeur_phase_01.png` à `phase_06.png` : 6 calques transparents de volutes de vapeur animées (boucle de 1000 ms, 167 ms par phase).

---

## 4. Livrables inclus

- **`COMPOSITION_JOUR.png`** & **`COMPOSITION_NUIT.png`** : Compositions complètes prêtes à l'emploi.
- **`ANIMATION_COMPLETE_JOUR.webp`** & **`ANIMATION_COMPLETE_NUIT.webp`** : Animations complètes 6 frames en boucle.
- **`GUIDE_CORRIDOR_CIRCULATION.png`** : Tracé du chemin d'accès vérifiant une largeur marchable minimale de 32 px (4 tuiles 8px).
- **`manifest.json`** : Métadonnées complètes pour le chargeur PMDO.
- **`steam_cave_nouveau_layout_v1_calques.zip`** : Archive autonome contenant l'ensemble des calques, sprites et manifests.
- **`apercu_steam_cave_nouveau_layout_v1.html`** : Galerie interactive à la racine du dépôt pour visualiser le rendu sans lancer le moteur.
