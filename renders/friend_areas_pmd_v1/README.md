# FA1 — Friend Areas Rescue Team : Forêt Énergique & Forêt Champignon

**Date de production : 22 septembre 2026 · Cible moteur : PMDO 0.8.12 (RogueEssence).**

Ce lot adapte fidèlement deux Friend Areas emblématiques de Pokémon Donjon Mystère : Équipe de Secours Rouge (GBA) en véritables cartes de terrain PMDO multicalques sur grille 8 px, prêtes pour l'édition et le jeu.

---

## 1. Cartes réalisées

| Zone | Dimensions | Grille 8 px | Calques sémantiques | Spawn initial | Palette |
|---|---|---|---|---|---|
| **Forêt Énergique** (`energetic_forest`) | 480 × 336 px | 60 × 42 tuiles | 5 calques (Jour & Nuit) | [240, 296] | 91 couleurs natives GBA 5-bit |
| **Forêt Champignon** (`mushroom_forest`) | 456 × 336 px | 57 × 42 tuiles | 5 calques (Jour & Nuit) | [228, 296] | 93 couleurs natives GBA 5-bit |

---

## 2. Décomposition en 5 calques sémantiques

### Forêt Énergique (480 × 336)
1. **01 - Sol clairière continu** : Sol herbeux chaleureux et sentiers de terre, 100% opaque. La matière de sol est reconstituée sous tous les arbres, buissons et obstacles par transformée de distance, éliminant tout trou transparent.
2. **02 - Buissons denses** : Massifs végétaux ombragés et buissons d'arrière-plan.
3. **03 - Végétation basse** : Pousses ensoleillées, petites herbes et arbustes de premier plan.
4. **04 - Troncs et racines** : Grands fûts d'arbres anciens, racines noueuses et souches.
5. **05 - Canopée avant-plan** : Branches maîtresses et voûte foliacée surplombant la clairière.

### Forêt Champignon (456 × 336)
1. **01 - Sol tapis de mousse continu** : Tapis végétal menthe/cyan lumineux, 100% opaque, inpeint sous tous les pieds de champignons et souches.
2. **02 - Troncs et souches** : Arbres tordus bleu-indigo, mottes moussues et écorces ombragées.
3. **03 - Grands champignons** : Chapeaux violets/pourpres caractéristiques et points blancs contrastés.
4. **04 - Petits champignons** : Sporophores et grappes de champignons lumineux disséminés sur le parvis.
5. **05 - Canopée avant-plan** : Branches hautes et retombées végétales créant l'immersion sous voûte.

---

## 3. Contrat technique et artistique

- **Pixels natifs 1×** : Aucun redimensionnement, aucun rééchantillonnage flou. Les pixels proviennent strictement des rips de cartouche GBA authentiques (`Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest.png` et `Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Mushroom Forest.png`).
- **Palettes 5-bit GBA préservées** : Toutes les composantes R, G, B des calques diurnes sont des multiples exacts de 8 (`val % 8 == 0`), garantissant l'absence de dérive colorimétrique.
- **Sol 100% continu et praticable** : L'arrivée sud est libre et validée par érosion morphologique 17×17 px (plus de 22 500 px praticables en Forêt Énergique, plus de 15 500 px en Forêt Champignon).
- **Ambiances Jour & Nuit** : Chaque calque dispose de sa variante nocturne calculée selon le filtre canonique Abyss du dépôt (`source/cote_v4_abyss/night.py`), avec opacité 100% du sol maintenue.
- **Aucun Pokémon cuit** : Les cartes sont livrées sans aucune entité ou PNJ figé, laissant l'éditeur libre pour le placement dynamique.

---

## 4. Livrables disponibles

- `renders/friend_areas_pmd_v1/FA1_friend_areas_duo.png` : Planche comparative côte à côte des deux zones.
- `renders/friend_areas_pmd_v1/FA1_<area>_carte_jour.png` & `carte_nuit.png` : Rendu complet 1×.
- `renders/friend_areas_pmd_v1/FA1_<area>_calques.png` : Planche de décomposition des calques.
- `renders/friend_areas_pmd_v1/FA1_<area>_viewport.png` & `_320x240.png` : Simulation du cadrage caméra PMDO 320×240.
- `renders/friend_areas_pmd_v1/FA1_<area>_ambiances.webp` : Prévisualisation animée de la transition jour/nuit.
- `renders/friend_areas_pmd_v1/FA1_<area>_calques.zip` : Archive complète des PNG transparents alignés et du manifeste JSON.
- `renders/friend_areas_pmd_v1/FA1_<area>_PMDO.zip` : Pack mod PMDO autonome avec fichiers `.rsground`, banques `.tile` 8 px et script `INSTALLER.py`.

---

## 5. Commandes de reproduction et validation

```sh
# Reconstruire tous les calques, rendus et packs :
python3 source/friend_areas_pmd_v1/work.py --build

# Exécuter les contrôles d'intégrité, de palettes et d'érosion :
python3 source/friend_areas_pmd_v1/work.py --verify

# Sérialiser les Ground PMDO, banques de tuiles et tester l'installeur :
python3 source/friend_areas_pmd_v1/work.py --pmdo
```

---

## 6. Limites documentées

- Tests effectués par scripts de contrôle d'image, de sérialisation et d'installation ; le binaire exécutable PMDO n'a pas été lancé avec GPU.
- Les collisions physiques restent libres (ébauche d'édition `Released=false`) ; les warps et événements narratifs doivent être placés dans l'éditeur Ground de PMDO.
