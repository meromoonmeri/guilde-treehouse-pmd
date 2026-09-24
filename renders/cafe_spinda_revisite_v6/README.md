# Spinda — nouvelles générations N/S et oculus café

Trois nouvelles compositions référencées sur le plan N/S approuvé et le seuil de l’accueil choisi. **Généré d’après la référence ≠ mêmes pixels que l’escalier de référence**. Le plan a été approuvé ; ces nouvelles images restent soumises à votre appréciation artistique.

- Accueil 0 : N monte vers café +1 ; S descend vers casino −1.
- Casino −1 : retour N montant ; E vers salon des jeux au même niveau.
- Café +1 : retour S descendant ; E vers salon lumineux au même niveau.
- Aucun troisième accès extérieur ajouté. Les deux salons conservent leur architecture V4.
- Nouvel oculus bois miel / verre doux / croisillon, conçu pour les intérieurs café ; **pas le sprite de la guilde**. Calque séparé et sprite 72×72 indépendant. Deux instances au café, trois au salon haut.

## Calques et import
Ouvrir `index.html` en HTTP, ou extraire `SpindaV6_pack.zip`. Les PNG des calques sont **dans le ZIP**, également lu directement par l’atelier du dépôt ; pas besoin de conserver une seconde copie des mêmes calques. Le ZIP extrait contient un atelier autonome et tous ses fichiers graphiques.

Salles 600×448, grille Ground 8 px. Parquet, motifs lumineux, parois, bordure basse, modules d’accès N/S et fenêtres séparés. Les accès incluent marches, joues rocheuses et raccords : les déplacer laisse un trou, ils ne sont pas des sprites autonomes. Les autres partitions décrivent les surfaces visibles, pas des volumes complets. La lumière des seuils reste intégrée au module d’accès. Recomposition RGBA du terrain vérifiée à l’identique des nouvelles générations normalisées ; réduction nearest ×0,5 réservée aux images générées, jamais aux assets natifs.

Les quatre générations brutes complètes sont archivées en WebP **sans perte**, y compris le dessin initial de fenêtre. Le catalogue et les flammes sont hérités de V4, sans nouveau mobilier revendiqué. Mobilier/rubans/tapis assortis restent à produire. Aucun meuble, feu ou Pokémon placé dans les nouvelles salles.

## Limites
Repères recalés sur les nouvelles géométries (N : [304,88], arrivée [304,200] ; S : [304,384], arrivée [304,280]). Ils ne reprennent pas les tests d’identité des pixels de l’audit V5. Les ports latéraux sont calculés sur les seuils visibles. **Warps, collisions, navigation et rendu PMDO non installés/non testés.** Les transitions sont indépendantes, pas une mosaïque seamless.

Reconstruction : `.venv/bin/python source/cafe_spinda_revisite_v6/build.py`.
