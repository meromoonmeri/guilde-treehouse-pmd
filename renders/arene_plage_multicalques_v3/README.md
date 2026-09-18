# Arène de Plage Multicalques V3 — Eau animée canonique PMD Port et décomposition stricte par éléments

[Livrable animé WebP (30 images @ 130 ms)](animation/ANIMATION_WRAP.webp) · [Aperçu autonome animé](../../apercu_arene_plage_multicalques_v3.html)

Arène côtière ouverte conçue pour Pokémon Donjon Mystère / PMDO, basée sur les références `arenapmdskybeach.png` (commit `9ec9a081`) et l'animation d'eau canonique du Port de PMD Ciel (`large.D25P11A.gif`).

## Architecture stricte : chaque élément a son propre calque

Conformément à la méthodologie approuvée du dépôt, **aucun regroupement d'éléments disparates** n'est fait. La scène est décomposée en **14 calques autonomes** alignés sur le canvas canonique **648 × 504** (divisible par 8) :

| Ordre | ID Calque | Fichier Jour | Fichier Nuit | Description |
|---|---|---|---|---|
| 00 | `00_ciel_pmd` | [`ArenePlageV3_00_ciel_pmd_jour.png`](calques/ArenePlageV3_00_ciel_pmd_jour.png) | [`ArenePlageV3_00_ciel_pmd_nuit.png`](calques/ArenePlageV3_00_ciel_pmd_nuit.png) | Ciel lointain PMD Sky |
| 00b | `00b_etoiles` | [`ArenePlageV3_00b_etoiles.png`](calques/ArenePlageV3_00b_etoiles.png) | [`ArenePlageV3_00b_etoiles.png`](calques/ArenePlageV3_00b_etoiles.png) | Étoiles nocturnes isolées |
| 01 | `01_nuages_wrap` | [`ArenePlageV3_01_nuages_wrap_jour.png`](calques/ArenePlageV3_01_nuages_wrap_jour.png) | [`ArenePlageV3_01_nuages_wrap_nuit.png`](calques/ArenePlageV3_01_nuages_wrap_nuit.png) | Nuages défilants en boucle continue sans coupure (30 frames) |
| 02 | `02_eau_mer_port` | [`ArenePlageV3_02_eau_mer_port_jour.png`](calques/ArenePlageV3_02_eau_mer_port_jour.png) | [`ArenePlageV3_02_eau_mer_port_nuit.png`](calques/ArenePlageV3_02_eau_mer_port_nuit.png) | Eau de mer animée canonique du Port (30 images @ 130 ms, cycle 3,90 s) |
| 03 | `03_ecume_rivage` | [`ArenePlageV3_03_ecume_rivage_jour.png`](calques/ArenePlageV3_03_ecume_rivage_jour.png) | [`ArenePlageV3_03_ecume_rivage_nuit.png`](calques/ArenePlageV3_03_ecume_rivage_nuit.png) | Écume et déferlante le long du rivage |
| 04 | `04_sol_sable_complet` | [`ArenePlageV3_04_sol_sable_complet_jour.png`](calques/ArenePlageV3_04_sol_sable_complet_jour.png) | [`ArenePlageV3_04_sol_sable_complet_nuit.png`](calques/ArenePlageV3_04_sol_sable_complet_nuit.png) | Sous-sol continu de sable recouvrant toute l'arène sous les massifs rocheux |
| 05 | `05_sol_sable_visible` | [`ArenePlageV3_05_sol_sable_visible_jour.png`](calques/ArenePlageV3_05_sol_sable_visible_jour.png) | [`ArenePlageV3_05_sol_sable_visible_nuit.png`](calques/ArenePlageV3_05_sol_sable_visible_nuit.png) | Arène de sable centrale dégagée |
| 06 | `06_acces_sud` | [`ArenePlageV3_06_acces_sud_jour.png`](calques/ArenePlageV3_06_acces_sud_jour.png) | [`ArenePlageV3_06_acces_sud_nuit.png`](calques/ArenePlageV3_06_acces_sud_nuit.png) | Approche et sentier d'accès sud praticable |
| 07 | `07_falaises_rouges_arriere` | [`ArenePlageV3_07_falaises_rouges_arriere_jour.png`](calques/ArenePlageV3_07_falaises_rouges_arriere_jour.png) | [`ArenePlageV3_07_falaises_rouges_arriere_nuit.png`](calques/ArenePlageV3_07_falaises_rouges_arriere_nuit.png) | Arche et falaises rouges d'arrière-plan |
| 08 | `08_falaises_rouges_gauche` | [`ArenePlageV3_08_falaises_rouges_gauche_jour.png`](calques/ArenePlageV3_08_falaises_rouges_gauche_jour.png) | [`ArenePlageV3_08_falaises_rouges_gauche_nuit.png`](calques/ArenePlageV3_08_falaises_rouges_gauche_nuit.png) | Grand massif rocheux sur le flanc ouest |
| 09 | `09_falaises_rouges_droite` | [`ArenePlageV3_09_falaises_rouges_droite_jour.png`](calques/ArenePlageV3_09_falaises_rouges_droite_jour.png) | [`ArenePlageV3_09_falaises_rouges_droite_nuit.png`](calques/ArenePlageV3_09_falaises_rouges_droite_nuit.png) | Grand massif rocheux sur le flanc est |
| 10 | `10_rochers_arriere_plan` | [`ArenePlageV3_10_rochers_arriere_plan_jour.png`](calques/ArenePlageV3_10_rochers_arriere_plan_jour.png) | [`ArenePlageV3_10_rochers_arriere_plan_nuit.png`](calques/ArenePlageV3_10_rochers_arriere_plan_nuit.png) | Récifs rocheux intermédiaires le long du rivage |
| 11 | `11_rochers_avant_plan` | [`ArenePlageV3_11_rochers_avant_plan_jour.png`](calques/ArenePlageV3_11_rochers_avant_plan_jour.png) | [`ArenePlageV3_11_rochers_avant_plan_nuit.png`](calques/ArenePlageV3_11_rochers_avant_plan_nuit.png) | Récifs rocheux de premier plan encadrant la caméra |
| 12 | `12_ombres_contact` | [`ArenePlageV3_12_ombres_contact_jour.png`](calques/ArenePlageV3_12_ombres_contact_jour.png) | [`ArenePlageV3_12_ombres_contact_nuit.png`](calques/ArenePlageV3_12_ombres_contact_nuit.png) | Ombres de contact douces au sol pour un ancrage réaliste |

## Méthode réellement employée

1. **Génération d’un décor complet cohérent sur magenta** : `bruts/terrain_magenta.png` (matière de grès rouge et sable doré d'après `arenapmdskybeach.png`).
2. **Génération du sol complet sous les reliefs** : `bruts/sol_complet.png`. Pas de remplissage par répétition d'un minuscule échantillon.
3. **Partition géométrique disjointe exacte** : les 7 masques de terrain visibles somment exactement à 1 sur chaque pixel valide de terrain, et 0 dans le vide.
4. **Intégration canonique de l'eau du Port** : 30 images à 130 ms issues de `large.D25P11A.gif`, sans redimensionnement destructeur.
5. **Nuages wrap continu** : bande transparente de nuages défilant en boucle parfaite sans coupure sur 30 frames.
6. **Ombres de contact et sous-sol continu** : aucune fuite de vide lors du masquage des reliefs.

## Fichiers livrés
- `calques/` : les 14 calques PNG distincts (jour et nuit), origine commune (0,0).
- `masques/` : les masques binaires de chaque calque.
- `animation/ANIMATION_WRAP.webp` : animation WebP sans perte 30 images @ 130 ms.
- `animation/02_eau_mer_port_animee_seule.gif` : eau seule animée.
- `animation/frames/` : 30 images PNG séparées de l'eau et des nuages (jour et nuit).
- `arene_plage_editable.ora` : pile OpenRaster multicouche complète.
- `review/` : GIF animés jour et nuit, compositions statiques et instantanés.
- `manifest.json`, `placement_recipe.json`, `verification.json`.
- `apercu_arene_plage_multicalques_v3.html` : lecteur interactif autonome à la racine.

## Vérifications
12 tests validés : partition exacte, 100% opacité composite, 30 frames @ 130 ms, timing 3,90 s, concordance des calques et ORA valide. Pas de test collision moteur ou import PMDO.
