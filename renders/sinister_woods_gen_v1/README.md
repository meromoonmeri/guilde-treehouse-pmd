# Entrée de forêt style Sinister Woods — lot généré v1

**Statut : pixels GÉNÉRÉS (détourage magenta), pas des tuiles natives.**
Références de style : `Mystifying_Forest_entrance_TDS.png`, `Southern_Jungle_entrance_S.png`.
Galerie : `apercu_sinister_woods_gen_v1.html` (racine).

## Contenu

- `bruts/` : 3 planches générées (terrain 848×1264, arbres 1124×944, frises 1120×960).
- `calques/` : 11 calques 512×640 + découpes sources (`spec_*`, `part_*`).
  - `00_base_terrain` : scène opaque (recadrage 776×970 → 512×640, resampling documenté).
  - `01–05` : 3 grands arbres + 2 buissons indépendants.
  - `06–08` : frises sombres gauche/droite + arche de lianes (découpes à chevauchement, pixels dupliqués à l'identique).
  - `09–10` : herbes d'avant-plan (chemin d'arrivée laissé dégagé au centre).
- `anim/` : pulsation du bosquet (4 phases) + lucioles procédurales (8 phases, 150 ms).
- `scene_composite.png`, `scene_animee.gif`, `sinister_woods_gen_v1.ora`, `sinister_woods_gen_v1_pack.zip`.
- `manifest.json` : SHA-256 des bruts, recadrages, colonnes de découpe, comptes.

## Méthode

Bruts sur magenta → seuillage + despill (2 anneaux + passe globale, 0 résidu testé) →
normalisation LANCZOS → assemblage sur grille 8 px → ORA/ZIP/galerie.
Scripts : `source/sinister_woods_gen_v1/` (`build.py`, `test_build.py` 53 tests PASS, `package.py`).

## Limites explicites

- Art généré, pas natif : ne pas importer comme tileset sans validation.
- Les arbres cuits dans la base ne sont pas des objets indépendants (seuls les 5 spécimens + frises le sont).
- Lucioles/pulsation = VFX procéduraux, pas des cycles PMD récupérés.
- Pas de collisions, pas de test PMDO/GPU, art non approuvé.
- Les sols cachés sous les arbres ajoutés ne sont pas reconstitués (ils reposent sur la base).
