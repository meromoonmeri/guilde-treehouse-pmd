# Luminous Spring — petit relief et escalier

Retouche locale du layout central `spring_arc_en_ciel_v1/01_source_centrale`. Le bassin, la forêt et les astres lumineux ne sont pas déplacés. Ajout d’un socle bas et d’un escalier central avec une roche gris-vert guidée par les rochers déjà présents sur le site, sans matériau Métano ocre.

## Voir
- [Composition PNG](composition.png)
- [Avant / après](AVANT_APRES.png)
- [Animation, 39 phases / 6,5 s](animation.webp)
- Galerie autonome à la racine : `apercu_spring_escalier_v1.html`, avec avant/après, pause, six calques masquables et export PNG.

## Calques 600×600
1. `calques/01_decor_original.png` — décor central précédent, sans lumière.
2. `calques/02_petit_relief.png` — retouche locale du socle.
3. `calques/03_escalier.png` — marches et raccord central.
4. `calques/04_eau_cascades.png` — phase initiale, inchangée.
5. `calques/05_halo_arc_en_ciel.png` — phase initiale, inchangée.
6. `calques/06_faisceau_arc_en_ciel.png` — phase initiale, inchangée.

Pour les phases 00–38, les trois animations sont réutilisées **sans modification et sans offset** depuis `../spring_arc_en_ciel_v1/commun/{eau_cascades,halo_bassin,faisceau}/`. Ordre de dessin : les six calques dans l’ordre ci-dessus. Durée : 10 ticks par phase à 60 Hz, soit 6,5 secondes pour la boucle. WebP : 167/167/166 ms répétés 13 fois.

Le décor original reste sous les retouches. Le relief et l’escalier sont des calques de remplacement local avec un léger raccord alpha, pas des sprites complets destinés à être placés arbitrairement ailleurs. Le masque `masque_modification.png` indique exactement la zone affectée.

## Méthode et vérification
Une nouvelle génération guidée par le layout central et la référence Halcyon a produit le socle/escalier. Le brut est conservé dans `bruts/`. Il est remis au format nearest puis limité à la zone locale ; les zones animées sont protégées. **La texture est guidée par la roche locale, pas reconstruite pixel pour pixel en tuiles natives.**

`source/spring_escalier_v1/build.py` reconstruit le livrable et vérifie l’égalité pixel par pixel hors masque sur chacune des **39 phases**. `verification.json` contient le résultat et la superficie du masque. Aucune modification d’une carte `.rsground` ni validation PMDO/GPU. Anciennes versions conservées.

Source Halcyon / Palikadude et feuilles PMDCollab/RawAsset : provenance conservée dans `source/soleil_spring_v1/references/provenance.json`. Respecter les droits des ressources d’origine ; les nouvelles parties générées ne sont pas attribuées à Palika.
