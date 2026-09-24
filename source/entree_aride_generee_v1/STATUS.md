# Entrée aride V1 — statut

Choix utilisateur (reprise 24 septembre 2026) : map **entrée aride**, méthode
**rendu généré référencé PMD**, **statique** multi-layers, sorties **PNG + ORA**.

## Livré

- `renders/entree_aride_generee_v1/` : 6 couches 408×288, scène, planche,
  ORA, manifeste. ZIP `renders/entree_aride_generee_v1_pack.zip`.
- Viewer racine `apercu_entree_aride_v1.html` (6 calques embarqués).
- 10 tests dédiés PASS (`test_build.py`). PMDO NON TESTÉ, art non approuvé.

## Points techniques

- Bruts 1224×864 = ×3 exacts de la cible ; downscale uniforme LANCZOS /3.
- Grotte : 1 composante 825 px → bbox 190,49–223,85 au nord centre.
- Arbres connexes à la falaise à cette échelle : découpe par couleur (gris
  peu saturé reconnecté par dilatation 1 px, seuil 30 px), pas par composantes.
- Partition stricte testée : union = relief détouré, RGB intacts, recomposition exacte.
- Corridor 32 px (x 190–221) jusqu'au seuil y 97 ; la lèvre basse du cadre de
  la bouche (2–3 px) est le seuil, pas un obstacle.
- Chevauchement initial cailloux/ombres (4 px sombres dans un caillou) corrigé
  par priorités grotte > arbres > cailloux > ombres.

## Registre

Le registre natif sud–nord (`FULL_PROGRAMME_STATUS.json`) est laissé inchangé :
ce lot généré ne prétend pas être un relayout pixel-natif de la référence.
La prochaine map demandée reste à choisir (plage, jungle, cristal…).
