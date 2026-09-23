# Entrée en lisière — six groupes de calques

**Une entrée dans le même lieu que la Forêt envahie H07P03**, avec une disposition d’obstacles boisés inspirée de `Mystifying_Forest_entrance_TDS.png` : arrivée sud dégagée, clairière, passage nord entre deux groupes d’arbres. Pas de grotte générique, de porte artificielle ou de ciel bleu ajouté.

Cette livraison porte sur **une entrée**, conformément à la dernière demande, pas sur la finale ni les22cartes complètes. Les anciens lots restent inchangés. La finale et les autres duos restent à produire/reprendre.

## Calques alignés480×336 (Ground8px)

1. **Fond forestier** : profondeur vert pâle, distincte des arbres proches ; ce n’est pas un ciel ouvert.
2. **Sol continu** : herbe séparément générée et conservée sous les arbres/rochers, sans trous sur la zone praticable. Le prolongement nord généré est limité au plan proche, le haut du cadre appartient au fond forestier.
3. **Rochers** : quatre groupes complets de pierres générées, ajustés aux pieds des arbres et non suspendus sur leurs feuillages.
4. **Arbres et racines** : véritables silhouettes détourées, sans le fond ni le sol de la première tentative. Décor de bordure ancré au canevas, pas des sprites d’arbres hors-champ reconstruits en entier.
5. **Végétation basse** : herbes longues/pointues et fougères des bordures ; passage central libre.
6. **Lumière PMD** : deux pistes transparentes séparées, rayons et particules, jamais cuites dans le terrain.

Les cinq plans statiques sont cinq générations dédiées, pas cinq bandes découpées dans une seule image. Les deux guides complets et la première tentative d’arbres avec fond résiduel sont conservés dans l’historique, sans être présentés comme des calques validés. Les créations ont été normalisées au plus proche voisin et alignées sur les76couleurs visibles de H07P03 ; **elles restent générées, non natives**. Tous les PNG d’import conservent leurs pixels sans perte.

`manifest.json` donne l’ordre des plans, les cadences et les positions indicatives de l’arrivée et de l’entrée. `python assemble.py --tick 64 --out assembled` recrée la composition et son terrain transparent (Pillow/NumPy). Les images sont dans `calques/` et `06_lumiere/`. Les aperçus sans lumière et des six groupes sont dans `apercus/`.

## Lumière canonique — source explicitement réemployée

La lumière provient de **H07P04W (Forêt lumineuse)** du PMD Red PC Port épinglé, et non de H07P03, dont le fond d’origine est statique. Sa présence dans cette nouvelle entrée est un **choix de composition demandé**, pas une affirmation que cette animation appartenait à la Forêt envahie canonique.

- **Rayons** :32phases BPL,8ticks par phase, période256ticks.
- **Particules** :14poses BPA,7ticks par pose (durée stockée6 +1), période98ticks ; leur palette est invariante sur les32phases BPL.
- Les indices gris2–13 et les indices colorés1/14/15 sont séparés, sans recoloration, resampling ou déplacement. La recomposition des deux pistes est vérifiée contre **les448combinaisons natives**. Géométrie des rayons indépendante du BPA, couleurs des particules indépendantes du BPL.
- Fusion **additive RGB555, coefficients16/16** ; le noir est neutre. Ne pas utiliser un collage alpha normal pour la lumière. La réunion des deux pistes est ajoutée au terrain. Les PNG gardent les couleurs source ; la composition d’aperçu simule cette addition en RGB555.
- Base d’aperçu60Hz ; phase initiale conventionnelle en régime établi, pas une capture de démarrage du jeu.

Le WebP de la carte est un **extrait de256ticks, environ4,27s**, une image tous les8ticks, lu une seule fois. Les deux horloges restent indépendantes : leur boucle commune dure12544ticks (environ209s). L’extrait ne prétend pas être cette boucle complète. Les WebP de présentation sont compressés avec perte ; les frames PNG natives du pack ne le sont pas.

## Bonus demandé : cascades/colonnes de lave canoniques

`bonus_lave/` contient **six modules natifs** tirés de H26P01, palette4 : chacun possède8phases BPL ×3ticks, soit24ticks /400ms. Trois hauteurs visibles existent :56,112et168px ; les six emplacements source sont conservés séparément, sans miroir/agrandissement/recoloration ajouté. Les pixels du pied et du halo natif sont conservés. Les cascades sont raccordées au haut du cadre source : aucun sommet hors champ n’est inventé.

Ce sont les véritables colonnes de lave, **pas la texture de lave horizontale du premier pack**. Elles sont livrées à part pour les zones volcaniques et ne sont pas placées dans cette forêt. Le WebP des cascades présente leur boucle complète de400ms, contrairement à l’extrait forestier.

## Provenance et limites

Sources Red Port, pins et SHA figurent dans le manifeste ; données binaires et preuve C originales conservées dans le premier pack `DB1_cinq_duos_multicalques.zip`. La référence Mystifying Forest du dépôt est utilisée pour la disposition des arbres, pas déclarée comme un import natif Red Port. Aucune référence/ancienne livraison n’est écrasée.

Le contrôle du passage central est un test de pixels conservateur, **pas des collisions ou warps installés en PMDO**. Ni le moteur PMDO, ni le PC Port exécuté, ni une approbation artistique ne sont revendiqués. Les contraintes visibles et le sol sous les décors sont testés ; les limites hors champ des grands arbres restent celles du canevas.

## Téléchargements directs

- [LE1_lisiere_calques_et_effets.zip](https://raw.githubusercontent.com/meromoonmeri/guilde-treehouse-pmd/7253a42e93d8cc24358e4477e6e9c2056d118845/renders/lisiere_pmd_v1/LE1_lisiere_calques_et_effets.zip)
- [LE1_lisiere_animee.webp](https://raw.githubusercontent.com/meromoonmeri/guilde-treehouse-pmd/7253a42e93d8cc24358e4477e6e9c2056d118845/renders/lisiere_pmd_v1/LE1_lisiere_animee.webp)

[Planche des six groupes](LE1_calques_apercu.png) : aperçu réduit à75% ; les calques PNG du ZIP et sa planche complète restent à1×.

Ces deux fichiers lourds sont conservés à l’identique dans Git au commit indiqué par les liens. Le serveur et `release.py` les rematérialisent avec contrôle SHA-256 ; ce ne sont pas des fichiers perdus. Tous les calques PNG sont dans le ZIP.
