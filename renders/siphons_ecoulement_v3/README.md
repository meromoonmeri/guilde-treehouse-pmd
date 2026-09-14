# Siphons V3 — écoulement autour des obstacles et rives discrètes

Reprise non destructive de `eau_siphons_rapides_v2`. Les coordonnées des siphons et la chaussée sèche sont conservées. Le matériau d’eau est régénéré, les anciens anneaux bleus et les six poses dérivées du sable ne sont plus utilisés pour animer les bassins.

## Courant cohérent vers les siphons

Un champ stationnaire2D est calculé sur une grille de2px, avec :
- les rochers et la chaussée comme frontières imperméables ;
- neuf zones d’absorption aux centres des siphons ;
- de la circulation autour des centres, puis une projection de pression ;
- des frontières extérieures ouvertes qui alimentent les absorptions.

La divergence du champ correspond au retrait d’eau dans les siphons. Le flux normal sur les faces solides est nul. Le débit net venant des bords correspond au débit total retiré, à la précision numérique du solveur. Les petites poches transparentes entièrement enfermées dans les sprites ne participent pas à la circulation ouverte.

`CHAMP_ECOULEMENT.npz` contient les vitesses sur les faces, les obstacles, le domaine actif et les absorptions ; les contrôles sont reproduits par `verify.py`.

## Rendu et couleurs

Une nouvelle plaque de matière d’eau est générée dans une palette bleu–turquoise assortie aux roches gris bleuté. Elle est animée par des remontées de trajectoires dans le champ de vitesse. Deux phases de déformation se relaient pour boucler sans remise à zéro visible. Des filets suivent également le champ et disparaissent près des absorptions : les trajets montrés sont ceux qui atteignent un siphon dans la fenêtre de boucle.

Les cuvettes reçoivent une nouvelle ombre de profondeur progressive, sans reprendre l’ancienne géométrie animée des siphons de sable. Les filets courbes rendent la convergence et la rotation lisibles.

Les contours humides des rochers sont légèrement assombris/bleutés ; leurs silhouettes et leurs intérieurs sont conservés. Le calque de reflets de rive est limité à deux pixels autour du contact, avec une opacité maximale de **28/255** (18/255 côté roche), pour éviter les halos blancs épais. Son déplacement dépend du courant local, avec des périodes arrondies pour fermer la boucle. La chaussée reste sèche.

## Livrables

`siphons_ecoulement/` — 456×384.
- `COMPOSITION.png` et `ANIMATION_COMPLETE.webp`.
- **128 compositions PNG à50ms**, soit20 images/s et une boucle de6,4s.
- **9 calques** : 6 statiques et 3 groupes animés de128 PNG (eau advectée, filets du courant, reflets des rives).
- `siphons_ecoulement.ora`, phase zéro.
- Données de contrôle du champ et positions des traceurs : `.npz` à côté de la scène.
- `SIPHONS_ECOULEMENT_V3_calques.zip` : scène, calques, contrôle numérique et documentation ; brut généré et galerie exclus.
- Galerie autonome à la racine : `apercu_siphons_ecoulement_v3.html`. Animation complète128phases ; le curseur inspecte32échantillons (une phase sur quatre) pour alléger le fichier. Les128 PNG complets restent dans le pack.

L’ordre d’assemblage est dans `manifest.json`. Les animations sont des séquences PNG indépendantes ; l’ORA n’est pas une timeline.

## Vérifications

Scripts : `source/siphons_ecoulement_v3/build.py`, puis `verify.py` (Pillow, numpy, scipy).

Contrôles : conservation du débit dans le calcul2D, flux nul sur les faces solides, extrémités visibles des traceurs dans le fluide, silhouettes des rochers/chaussée inchangées, intérieurs secs préservés, opacité des rives bornée, 128 compositions opaques et distinctes, recomposition exacte depuis les PNG et l’ORA.

## Limites importantes

Il s’agit d’une **approximation stationnaire2D**, pas d’une simulation3D de surface libre, de turbulence complète ou de niveaux d’eau. Le shader de texture et les traceurs sont des visualisations bouclées. L’intégration utilise de petits pas bornés et refuse les mouvements d’échantillonnage vers une cellule solide. Les masques graphiques finaux restent distincts de la grille conservatrice de2px.

Les données de débit et de vitesse sont en unités de rendu, pas en unités d’un bassin réel. Le percentile95 de vitesse est réglé à140px/s pour la lecture à l’écran. Aucun personnage n’est aspiré par un script : pas de test PMDO/GPU, de collisions moteur ou d’interactions configurées. Les ressources précédentes restent conservées.
