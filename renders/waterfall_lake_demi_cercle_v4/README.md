# Waterfall Lake V4 — nouveau grand demi-cercle

## Contenu
- `origine_decomposee/` : **9 calques disjoints** de l’original456×312, PNG et OpenRaster. Recomposition strictement identique à l’image d’origine.
- `GUIDE_DEMI_CERCLE_SUR_ORIGINE.png` / `GUIDE_LAYOUT_504.png` : sélection projetée de la nouvelle emprise, avec cascade et écume originales exclues de la coloration.
- `sprites/lake4_falaise_seule.png` : nouveau massif sec continu, sans cascade ni écume. Fond et faces gauche/centrale/droite séparés dans les compositions.
- `jour/`, `nuit/` : **29 calques alignés**,504×360 ;24 poses sur4secondes ; compositions PNG, animation WebP et ORA de la pose0.
- Galerie autonome : `apercu_waterfall_lake_demi_cercle_v4.html` à la racine du dépôt et du ZIP. Jour/nuit, animation, chaque calque et étapes de décomposition.

## Changements et provenance
Le relief autour de la moitié supérieure du bassin est réellement remplacé par un massif continu en demi-cercle, ouvert au sud. Ancienne falaise centrale et anciennes ailes ne sont plus utilisées comme calques rocheux. L’original reste disponible intégralement, décomposé séparément.

Production séquentielle : **génération du relief sec → guide et génération séparée des chutes → animation avec la matière originale → écume canonique**. Les deux bruts sont conservés dans `bruts/`. Le guide des cascades montre les emplacements projetés ; les masques finaux et coordonnées de pied sont dans `sprites/` et `manifest.json`.

**Roche :** texture générée d’après le modèle GBA et remappée à sa palette rocheuse, pas récupération exacte de tuiles natives. La géométrie générée est adaptée au cadrage final. Ne pas assimiler cette réinterprétation à une texture native intacte.

**Chutes :** silhouettes du guide séparé recalées sur les trois sorties du relief ; matière76×48 extraite de l’original Waterfall Lake, défilant de2px par pose. Animation reconstruite depuis une image statique, pas animation GBA native récupérée. Les pieds sont (128,137), (252,109), (376,137).

**Écume :** trois poses Métano natives96×56 extraites du calque Objects Over d’Altere Pond, conservées pixel pour pixel, sans changement de taille, couleur, orientation ou découpe en JOUR. Seulement une translation vers chaque pied de chute. Copies autonomes dans `sprites/lake4_ecume_metano_native_*.png`. Source : Halcyon working-copy, commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51`, `Data/Ground/altere_pond.rsground`. Extraction et preuve temporelle existantes : `source/antre_harmonie_v3/native.py` et `references/timing_proof.json`. Trois poses de10ticks.

**Lac et plateforme :** eau et modulation douce des anneaux, disque Altere, six pas japonais, sept reflets et végétation conservés depuis V2. Toute la partie y≥180 reste identique à V2 sur les48compositions jour/nuit. Au nord, les anciens végétaux sont partiellement occultés par le nouveau relief : cette zone change volontairement.

**Nuit :** filtre exact Abyss, `source/cote_v4_abyss/night.py`, appliqué aux calques ; pas un filtre approximatif.

## Vérifications et limites
`verification.json` : PASS. Original recomposé et partition vérifiés ;48compositions,2ORA, préservation du sud, identité des trois poses d’écume placées, continuité des trois chutes et contact avec l’écume, filtre nocturne exact.

Ces contrôles ne sont **pas une validation artistique automatique ni un test PMDO**. Aucun test moteur, collisions ou échelle en jeu effectué. Les PNG des calques ont des basenames distincts `lake4_jour_*` / `lake4_nuit_*`, dimensions divisibles par8. Taille de tuile à sélectionner pour un éventuel import :8px. Les scènes et leur roche générée ne constituent pas un tileset natif canonique certifié.

## Reconstruction
Depuis la racine du dépôt avec les dépendances Pillow, NumPy, SciPy :
```
.venv/bin/python source/waterfall_lake_demi_cercle_v4/decompose.py
.venv/bin/python source/waterfall_lake_demi_cercle_v4/build.py
.venv/bin/python source/waterfall_lake_demi_cercle_v4/verify.py
.venv/bin/python source/waterfall_lake_demi_cercle_v4/package.py
```
Le ZIP contient les exports autonomes, les bruts et les scripts V4. **La reconstruction des scripts nécessite le dépôt**, notamment les exports V1/V2 et références natives antérieures ; ces dépendances ne sont pas toutes dupliquées dans le ZIP.
