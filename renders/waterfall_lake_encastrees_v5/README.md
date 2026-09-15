# Waterfall Lake V5 — nuances PMD et chutes latérales encastrées

Correction locale de la V4 approuvée. Le demi-cercle, le bassin, les anneaux, la plateforme, les pas japonais, les reflets et les écumes restent inchangés.

## Corrections
- Les trois cascades utilisent maintenant les **quatre phases natives de la cascade River d’Altere Pond**, avec leur palette de huit couleurs visibles, leurs filets clairs irréguliers et leurs nuances bleues. Matière issue de `source/antre_harmonie_v3/references/chute_native_0..3.png` : rectangle opaque48×96 extrait du crop48×112. Halcyon working-copy `1522c7a8b7a34d70078e11ed605b21d563b0dc51`. Preuve de timing : `references/timing_proof.json` du même dossier source ;10ticks par phase.
- Adaptation de hauteur aux trois chutes ; largeur centrale ajustée et côtés recadrés. Les motifs proviennent des poses natives, **mais les sprites finaux sont adaptés**, pas identiques aux sprites canoniques. Les bords ombrés utilisent exclusivement la palette native de l’eau.
- Les sorties latérales sont plus étroites, avec une ouverture resserrée sous le sommet et des bords en décrochements fixes. La roche existante est remise devant l’eau sur ces lèvres ; une ombre étroite de renfoncement accompagne les contacts. Aucun nouveau pilier ajouté et aucune modification globale du massif.
- L’écume Métano de la V4 est conservée intégralement, avec son cycle natif de trois poses.

## Livrables
504×360,31calques,24poses/4secondes. `jour/` et `nuit/` : PNG séparés et compositions, ORA de la première pose, animation WebP. Galerie autonome à la racine du dépôt et du ZIP : `apercu_waterfall_lake_encastrees_v5.html`. Comparaison V4/V5 disponible dans le menu ; `AVANT_APRES.png` compare les poses0.

`sprites/` contient la matière native, les canaux finaux, les lèvres rocheuses et les ombres. `MASQUE_RETOUCHE.png` limite exactement l’emprise autorisée aux trois anciennes silhouettes d’eau.

## Vérifications
`verification.json` :48compositions,2ORA,26anciens calques inchangés, tous les pixels hors des trois anciens masques de chute identiques à V4 dans toutes les poses jour/nuit. Chutes continues et en contact avec l’écume. Cycle de quatre phases. Filtre exact Abyss vérifié.

Ces tests ne certifient pas automatiquement la qualité artistique des raccords. **Aucun test PMDO, collisions ou échelle en jeu effectué.** Import éventuel des PNG de calques :8px, basenames distincts `lake5_jour_*` / `lake5_nuit_*`. Ce lot n’est pas un tileset natif complet.

## Reconstruction
Depuis la racine du dépôt, avec Pillow/NumPy/SciPy :
```
.venv/bin/python source/waterfall_lake_encastrees_v5/build.py
.venv/bin/python source/waterfall_lake_encastrees_v5/verify.py
.venv/bin/python source/waterfall_lake_encastrees_v5/package.py
```
Les exports et la galerie du ZIP sont autonomes. La reconstruction nécessite le dépôt et ses dépendances V4/références Altere ; elles ne sont pas toutes dupliquées dans le ZIP. V4 et livraisons précédentes préservées.
