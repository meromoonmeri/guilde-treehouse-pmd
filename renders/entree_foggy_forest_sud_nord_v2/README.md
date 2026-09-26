# EFF2 — Entrée Foggy Forest sans tentes, arbres en trois calques (4:3)

Demande : « la version sans tente stp et que les arbres [aient] leur propre calque, ombre etc ; même méthode avec preview html ». EFF1 reste intact.

- Aperçu : `apercu_entree_foggy_forest_sud_nord_v2.html` (racine). Décochez un calque pour l'isoler.
- Pack PMDO 0.8.12 : `EFF2_projet_pmdo_0812.zip` (projet `entree_foggy_forest_sans_tentes`).
- Calques PNG 8 px : `EFF2_calques_png_8px.zip`, ORA, `review/EFF2_scene_animee.webp`.
- Source : `source/entree_foggy_forest_sud_nord_v2/`, 14 tests.

## Méthode

Même chaîne qu'EFF1 : rendu généré **référencé** sur `Foggy_Forest_Base_Camp_TDS.png`, avec les **mêmes bruts générés** (`source/entree_foggy_forest_sud_nord_v1/bruts/`) et aucune nouvelle génération.

1. **Retrait des tentes, avant découpage.** L'emprise de chaque tente, repérée par le classifieur d'EFF1 et élargie de 3 px, est recouverte par de l'herbe du camp recopiée **du même décor**. La source est la zone d'herbe pâle la plus proche qui couvre toute l'emprise, recopiée sans retournement ; les décalages sont dans `manifest.json` → `retrait_tentes`. J'ai d'abord essayé le sol complet généré, mais sa texture plus striée faisait des rustines visibles : je l'ai écarté.
2. **Arbres en trois calques.** La zone boisée est redécoupée par couleur lissée sur 5 px :
   - **ombres portées** : l'aplat sombre et bleuté sous chaque houppier ;
   - **troncs et racines** : les pixels bruns, avec leur propre palette de 16 couleurs ;
   - **houppiers** : le reste du feuillage.
   Les petites taches et les liserés fins sont rendus au sous-bois.
3. Le reste de la chaîne ne change pas : réduction par matière, palettes séparées, mare façon Métano, scintillements natifs, brume tramée, collisions, Ground 0.8.12.

## Chiffres

- 1727 cases praticables : l'ancienne place des tentes est devenue de l'herbe praticable. EFF1 en comptait 1475.
- Fidélité des calques finaux au rip : herbe 38,3, chemin 35,9, sous-bois 36,4. Même réserve qu'EFF1 : le brut est plus laiteux que la capture.
- 14 tests PASS. Ils vérifient en plus qu'il ne reste aucune tente rose et que les ombres sont plus sombres et plus bleutées que les houppiers et placées dessous. Ils vérifient aussi que les troncs sont bruns et que les calques des arbres ne touchent ni l'herbe ni le chemin.

## Limites

- Les calques des arbres découpent les plans visibles. Il n'y a pas de faces cachées.
- Il reste quelques fragments de liseré dans les calques houppiers et ombres, au bord de la clairière.
- Pas de test PMDO en jeu. L'art n'est pas validé.
