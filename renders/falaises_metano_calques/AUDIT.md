# Audit Technique et Visuel — Falaises Métano Town en Multicalques

**Statut global : VALIDÉ (100% Conforme aux critères Métano Town)**

## 1. Respect Strict des Contraintes Utilisateur
- **Zéro eau** : Aucun point d'eau, étang, lac, rivière, cascade ou mer (0 pixel aquatique détecté).
- **Zéro chemin** : Aucun chemin tracé, route de terre ou sentier.
- **Seulement les falaises** : Herbe Métano Town (`_sol_herbe`), Couronne canonique (`_bordures_rebord`), Parois rocheuses (`_parois_roche`), et Pied de falaise (`_pied_falaise`).
- **Décomposition multicalques** : Chaque falaise est livrée en calques indépendants et disjoints, dont la somme recomposée reconstitue le terrain complet à l'octet près.
- **Palette canonique verrouillée** : 328 couleurs autorisées issues de `Metano_Town_Base.tile` et `Metano_Town_Cliffs.tile` (y compris l'ombre mauve native `[96, 56, 88]`).
- **Zéro pixel hors palette** : 0 couleur étrangère sur l'ensemble des modules.

## 2. Métriques Quantitatives par Module

| Module | Titre | Dimensions (px) | Tuiles (8px) | Pixels Opaques | Hors Palette | ΔE76 Médian | ΔE76 P95 |
|---|---|---|---|---|---|---|---|
| 01_promontoire | Cap Promontoire | 1640 × 656 | 205 × 82 | 816,434 | 0 | 4.6 | 9.801 |
| 02_double_terrasse | Double Terrasse Étagée | 1640 × 656 | 205 × 82 | 908,589 | 0 | 2.169 | 5.466 |
| 03_cirque_gradins | Cirque de Gradins | 1640 × 656 | 205 × 82 | 966,497 | 0 | 6.059 | 16.506 |
| 04_echancrure | Échancrure et Éperon | 1376 × 768 | 172 × 96 | 880,299 | 0 | 3.446 | 9.377 |

## 3. Décomposition des Calques par Module (Pixels)

| Module | Sol / Herbe | Bordures / Couronne | Parois Roche | Pied Falaise | Total Terrain |
|---|---|---|---|---|---|
| 01_promontoire | 347,400 | 55,485 | 388,969 | 24,580 | 816,434 |
| 02_double_terrasse | 374,128 | 29,278 | 481,319 | 23,864 | 908,589 |
| 03_cirque_gradins | 397,675 | 55,027 | 489,763 | 24,032 | 966,497 |
| 04_echancrure | 308,747 | 21,023 | 532,266 | 18,263 | 880,299 |

## 4. Analyse Visuelle Détaillée

### 01_promontoire (Cap Promontoire)
- **Couronne / Bordure** : Lisière découpée et ondulée continue séparant le plateau d'herbe de la roche frontale, sans interruption ni chapelet de galets.
- **Parois rocheuses** : Strates géologiques horizontales de Métano avec rehauts ocres dorés et ombrages mauves denses dans les rentrants.
- **Herbe Métano** : Plateau supérieur vert-jaune ditheré conforme aux textures de sol de Bourg-Trésor.
- **Pied de falaise** : Assise inférieure nette sur fond transparent / magenta.

### 02_double_terrasse (Double Terrasse Étagée)
- **Structure étagée** : Deux plateaux distincts à altitudes différentes avec retours concaves naturels.
- **Couronne** : Suit fidèlement chaque décroché de niveau, épousant les formes arrondies des terrasses.
- **Matériau** : Grain pixel-art net et absence de flou anti-aliasing.

### 03_cirque_gradins (Cirque de Gradins)
- **Relief en fer à cheval** : Parois enveloppantes avec corniches et gradins d'herbe intermédiaires.
- **Ombres** : Richesse des ocres et présence du mauve natif dans le creux du cirque.

### 04_echancrure (Échancrure et Éperon)
- **Profondeur** : Éperon rocheux frontal contrastant avec le renfoncement ombré.
- **Couronnes supérieures** : Raccord impeccable entre les surfaces herbeuses et les parois verticales.

## 5. Livrables et Fichiers Produits
- Calques PNG RGBA transparents : `01_sol_herbe.png`, `02_bordures_rebord.png`, `03_parois_roche.png`, `04_pied_falaise.png` (et variantes `_nuit.png`).
- Masques binaires : `masques/masque_*.png`.
- Composites : `terrain.png`, `terrain_nuit.png`, `terrain_magenta.png`.
- Moteur PMDO & Tiled : `terrain.tile` et `terrain.tsj`.
- Planches d'audit : `PLANCHE_FALAISES_CALQUES.png` et `AUDIT_DETAILS_MATIERE.png`.
- Visualiseur interactif : `apercu_falaises_metano_calques.html` à la racine du projet.
