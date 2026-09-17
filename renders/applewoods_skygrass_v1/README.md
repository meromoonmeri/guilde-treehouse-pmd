# Apple Woods — prairie Sky Peak et entrée du vieux pommier

Nouvelle proposition de layout légèrement modifié, guidée par `Apple_Woods_entrance_TDS.png` du commit46e93da et les références Sky Peak déjà présentes dans `source/sky_peak_v1/`. Le passage central et les deux bordures de verger restent le principe de composition ; la sortie nord devient une entrée naturelle dans le gros tronc d’un pommier ancien.

## Création et calques

- Sol clair inspiré de l’herbe courte de Sky Peak, généré comme plaque de fond complète.
- Chemin crème-ocre accordé à la nouvelle herbe, sur un calque séparé avec sa lisière.
- Quatre variantes de pommiers générées sur magenta, détourées, harmonisées et instanciées en **vingt calques d’arbres individuels**.
- Grand arbre d’entrée généré séparément ; profondeur de l’ouverture, tronc/racines et canopée en trois partitions complémentaires.
- Ombres de contact et petites bases feuillues des fleurs séparées.
- Fleurs sur **trois calques animés** : gauche, droite, autour de l’entrée.

Le sol caché est reconstitué pour permettre de retirer le chemin. Les sprites ordinaires et le grand arbre complet sont fournis dans `sprites/` ; certains sont volontairement coupés par les limites du canevas lors de leur placement. Les partitions tronc/canopée de l’arbre d’entrée ne reconstruisent pas les faces cachées entre ces éléments.

## Fleurs Sky Peak

Dix petits groupes de fleurs sont extraits des quatre frames du GIF local Sky Peak (`gif_0.png` à `gif_3.png`). Leurs pixels visibles et leur échelle sont conservés, sans recoloration. Les masques de détourage sont reconstruits par sélection de couleur. Le cycle source comporte quatre phases à **200 ms**, avec des poses répétées dans son mouvement aller-retour ; il n’est pas présenté comme quatre poses toutes différentes.

Vingt-six placements sont répartis sur l’herbe autour du chemin, avec des décalages de phase. Les trois calques animés se recomposent exactement depuis les sprites sources exportés. Les petites feuilles/tiges sous les groupes sont reconstituées sur un calque statique, pas revendiquées comme des sprites natifs récupérés.

## Livrables

`entree_pommier/` — 552×408, dimensions multiples de8.
- `COMPOSITION.png`, `ANIMATION_COMPLETE.webp`.
- Quatre compositions PNG ; cycle 0,8 s.
- **30 calques** : 27 statiques et trois groupes animés de quatre PNG.
- `entree_pommier.ora` avec la phase zéro. Les phases d’animation sont dans les PNG, pas dans une timeline ORA.
- `sprites/` : quatre pommiers, le grand arbre entier et les dix groupes floraux en quatre phases.
- `PLANCHE_POMMIERS.png`, masques de chemin et de contrôle de l’approche.
- `APPLEWOODS_SKYGRASS_calques.zip` : scènes, calques, sprites et documentation ; bruts et galerie exclus.
- Galerie autonome à la racine : `apercu_applewoods_skygrass_v1.html`.

## Vérifications et limites

Scripts : `source/applewoods_skygrass_v1/build.py`, puis `verify.py` (Pillow, numpy, scipy).

Opacité, recomposition ORA/PNG exacte, quatre compositions distinctes, conservation des pixels floraux natifs, placement des fleurs hors du chemin et vingt arbres sur vingt calques vérifiés. Un corridor de24px rejoint le pied du tronc depuis le sud. Ce contrôle géométrique ne valide pas le franchissement de l’ouverture dans le moteur.

Pas de test PMDO/GPU, de collisions, de transition de donjon ou d’échelle des personnages validée. Les sols et arbres générés ne sont pas des nouveaux sprites officiels. Les anciennes références et les autres lots restent inchangés.

L’utilisateur a choisi de réaliser cette forêt en premier. Le deuxième chantier demandé, la reprise des siphons, est livré séparément dans `renders/siphons_ecoulement_v3/`.
