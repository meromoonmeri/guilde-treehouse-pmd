# Crooked Cavern verdoyante V1 — arrivée sud, bouche de grotte au nord

Une seule map, 512×640 (1 px = 1 px, comme les entrées sud–nord V3), livrée en calques alignés jour + nuit,
ORA éditable, galerie `apercu_crooked_verdoyant_v1.html` (racine du dépôt).

## Ce que c'est — et ce que ce n'est pas

- **Terrain généré** : la scène (parois Crooked ocre stratifiées, bouche de grotte, herbe, chemin de terre,
  arbres, rochers, fougères) est un **dessin généré d'après les références canoniques** auditées dans
  `source/crooked_verdoyant_v1/AUDIT.md` (Crooked Cavern entrance, Vast Steppe entrance, Relic Forest Base).
  Ces pixels **ne sont pas des pixels natifs certifiés** et ne doivent pas être présentés comme tels.
  Méthode identique à `renders/arene_glace_generee_v2` (génération complète + sous-couche sol générée, normalisation
  NEAREST, calques par masques, recomposition exacte).
- **Pourquoi généré** : aucune paroi Crooked modulaire n'existe nativement (la feuille Base est la scène 320×240 elle-même,
  chaque tuile unique) ; une bouche Crooked entourée de verdure ne peut pas être assemblée en tuiles natives sans
  répéter/miroiter des fragments (interdit). La palette ocre native est conservée (pas de recoloration grise comme
  dans `crooked_verdure_v1`).
- **Complément natif certifié** (`complement_natif/`) : rochers Crooked (feuilles Objects + Shadows, translation seule)
  et arbres Vast Steppe (tronc + canopée, mêmes modules que `source/zones_south_north_v3`) posés aux emplacements des
  objets générés → variante « objets natifs » (`composition_objets_natifs_jour.png` / `_nuit.png`). La vérification
  reconstruit ces deux calques depuis les feuilles sources et exige l'identité pixel à pixel.

## Fichiers

| Chemin | Contenu |
|---|---|
| `bruts/scene_complete_brut.png`, `bruts/sol_complet_brut.png` | Générations brutes 928×1152 (SHA-256 dans `manifest.json`) ; `*_512x640.png` = normalisées NEAREST |
| `calques/CrookedVerdoyantV1_01_sol_complet.png` | Sous-couche sol complète opaque (herbe + lisière + chemin jusqu'au bord nord) — sous tout le reste |
| `calques/..._02_herbe_visible` … `..._09_arbres` | 8 calques visibles : herbe, lisière de forêt, chemin, parois Crooked, entrée (ouverture + sol du débouché), rochers, végétation basse, arbres. **Partition exacte** de la scène : leur empilement = `composition_jour.png` pixel pour pixel |
| `masques/` | Masques L (255 = calque) de chaque calque visible |
| `nuit/` | Chaque calque passé au filtre Abyss exact (`source/cote_v4_abyss/night.py`) ; `composition_nuit.png` = night(composition_jour) |
| `complement_natif/` | `..._10_rochers_natifs_crooked.png`, `..._11_arbres_natifs_steppe.png` (pixels natifs, translation seule) + compositions variante natifs jour/nuit |
| `CrookedVerdoyantV1_editable.ora` | Pile complète (calques natifs présents mais masqués par défaut) |
| `manifest.json`, `verification.json` | Provenance, ordre des calques, placements natifs, résultats des contrôles |
| `review/` | Planches de contrôle 1× (jour/nuit, généré vs natifs, masques couleur, planche des calques) |

Ordre d'empilement (bas → haut) : 01 sol complet · 02 herbe visible · 03 lisière · 04 chemin · 05 parois · 06 entrée ·
07 rochers · 08 végétation basse · 09 arbres · (10 rochers natifs · 11 arbres natifs, variante).

## Repères de jeu (à confirmer en éditeur)

- Arrivée : bord sud, chemin centré (x ≈ 232–290 à y = 639, largeur ≥ 44 px sur tout le tracé).
- Objectif : bouche de grotte au nord, calque `06_entree_grotte`, bbox (209, 96) → (303, 216) ; le chemin
  touche le sol du débouché à y = 216 (`verification.json : path_connects_south_edge_to_cave = true`).
- Nuit : filtre Abyss exact appliqué calque par calque (aucune feuille `_Night` native n'existe pour Crooked).

## Reproduction / contrôle

```
.venv/bin/python source/crooked_verdoyant_v1/build.py    # calques, masques, nuit, ORA, galerie, manifeste
.venv/bin/python source/crooked_verdoyant_v1/verify.py   # verification.json (all_pass attendu)
```

**Non testé** : PMDO runtime, collisions, warps, import dans l'éditeur. Art à examiner à 1× (galerie, bouton ×2).
