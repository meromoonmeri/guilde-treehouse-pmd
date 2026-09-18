# Arène de Plage Multicalques V3 — 2026-09-18

Demande stricte : « CHAQUE ÉLÉMENT DOIT AVOIR SON PROPRE CALQUE. SUIS LA MÉTHODE DES READ ME DES ZONES DANS LE DOSSIER RENDER. ARRÊTE DE MODIFIER LE TRAVAIL ET NOTRE MÉTHODOLOGIE. »

Application intégrale de la méthodologie canonique (AGENTS.md, WORKFLOW.md, renders/arene_glace_large_v3) :
- Scène 648 × 504 (divisible par 8), intégrant sans redimensionnement l'animation canonique d'eau du Port de PMD Ciel (large.D25P11A.gif, 30 frames @ 130 ms, période de 3,90 s).
- Décomposition stricte en **14 calques autonomes** :
  1. `00_ciel_pmd` (ciel PMD distant)
  2. `00b_etoiles` (étoiles nocturnes isolées)
  3. `01_nuages_wrap` (nuages défilants en boucle continue sans raccord 30 frames)
  4. `02_eau_mer_port` (mer animée 30 frames D25)
  5. `03_ecume_rivage` (écume et ressac du rivage)
  6. `04_sol_sable_complet` (sous-sol continu sous les reliefs pour garantir zéro trou)
  7. `05_sol_sable_visible` (arène de sable centrale)
  8. `06_acces_sud` (sentier d'approche sud praticable)
  9. `07_falaises_rouges_arriere` (arche et falaises de fond)
  10. `08_falaises_rouges_gauche` (massif rocheux ouest)
  11. `09_falaises_rouges_droite` (massif rocheux est)
  12. `10_rochers_arriere_plan` (récifs côtiers de mi-plan)
  13. `11_rochers_avant_plan` (récifs rocheux de premier plan)
  14. `12_ombres_contact` (ombres de contact douces au sol)

Livrables conformes :
- `renders/arene_plage_multicalques_v3/` avec README.md complet, calques/, masques/, bruts/, animation/, review/, arene_plage_editable.ora, manifest.json, placement_recipe.json, verification.json.
- Galerie autonome `apercu_arene_plage_multicalques_v3.html` à la racine.
- Suite de tests unitaires `test_build.py` validant les 14 calques, la partition, l'opacité 100%, l'absence de fuite et le timing.
