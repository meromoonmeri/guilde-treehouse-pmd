# Références fidèles en plusieurs calques

**Correction appliquée : reprendre les layouts de référence, ne pas réinventer les zones.** Les nouvelles compositions générées dans le lot précédent sont mises de côté ; aucun de leurs pixels n’entre dans cette livraison.

Références : fichiers ajoutés par l’utilisateur au commit **`8eb46bc`**. Les fichiers racine sont inchangés. Les noms MAP_BG sont conservés, sans attribution spéculative à des donjons nommés.

## Livré
- **14 zones de référence** à leurs dimensions originales, sans déplacement, recadrage ou changement de palette.
- Le **fond nocturne fourni**, également séparé en calques.
- Six **micro-variations optionnelles** : une très petite hausse de lumière localisée sur le sol (+2,5% avant arrondi), sans modifier les passages, silhouettes ou ouvertures.
- Les animations des trois GIF concernés : **6 phases pour D14P11A,12 pour D17P33A,30 pour D25P11A**, avec leurs durées originales.
- PNG de chaque calque, PNG recomposé, document `.ora` pour chaque référence et manifeste avec provenance.

Cela donne14 rendus de zones de référence et6 rendus subtilement modifiés, **pas20 nouveaux layouts ou20 biomes originaux**. Le doublon D13P11A n’est pas compté comme un layout supplémentaire. La demande de simplicité et fidélité passe avant le lot de compositions originales.

## Ouvrir
Galerie autonome : **`apercu_references_fideles_v1.html`**, à la racine.

La galerie permet :
- choix de la référence ;
- masquage individuel et téléchargement des calques ;
- affichage de la référence seule ;
- animation native, pause et phase par phase ;
- activation de la micro-variation lorsqu’elle existe ;
- export de la vue en PNG.

La comparaison « référence seule » affiche sa phase0. Pour comparer une animation, revenir à la même phase.

## Dossiers
| Dossier | Référence |
|---|---|
| `ref_00` | Fond nocturne PNG fourni — statique |
| `ref_01` | Entrée cascade |
| `ref_02` | D05P11A — chemin fruitier |
| `ref_03` | D05P31A — clairière fruitière |
| `ref_04` | D07P11A — corniche rocheuse |
| `ref_05` | D11P11A — passage gris |
| `ref_06` | D12P41A — cirque gris |
| `ref_07` | D13P11A — défilé désertique |
| `ref_09` | D14P11A — bassins de sable |
| `ref_10` | D17P33A — passage cristallin |
| `ref_11` | D24P11A — forêt à racines |
| `ref_12` | D24P31A — clairière à racines |
| `ref_13` | D25P11A — côte et grotte |
| `ref_14` | D28P31A — salle à fresques |
| `ref_15` | P04P01C — promontoire nocturne |

Dans chaque dossier :
- `REFERENCE_RECOMPOSEE.png` correspond exactement à la référence, phase0 pour un GIF ;
- `ref_XX_*.png` sont les calques à placer tous en(0,0) ;
- `ref_XX_calques.ora` contient les calques alignés (et la phase0 du calque animé, le cas échéant) ;
- `animation_native/` conserve les phases séparées ;
- `OPTION_reflet_discret.png` et `VARIANTE_SUBTILE.png` existent seulement pour les six petits essais lumineux.

Ne pas importer les PNG avec un redimensionnement automatique. Certains canvas ne sont pas divisibles par8 ; ils sont volontairement conservés, pas étirés pour obtenir une grille. Le format ORA est un document de montage, pas une animation multipiste PMDO.

## Nature des calques — limite importante
La séparation combine zones de profondeur, matières et pixels animés : ciel, étoiles et nuages lorsque présents, eau visible, végétation visible, ouverture sombre, détails sombres peints, massif arrière, premier plan et sol/chemin visible. Les calques vides sont omis.

**Il s’agit de partitions des surfaces visibles**, dans l’esprit des strates du pack Northern Range. Il ne s’agit pas de restaurer les véritables couches natives perdues lors de l’export aplati. Le sol sous un arbre, l’arrière d’un rocher et les surfaces occultées **ne sont pas reconstruits**. Masquer une couche peut donc laisser des transparences ; déplacer une masse de décor exige une retouche des parties cachées et de certains contours.

Le calque `details_sombres` contient des pixels sombres de la peinture (ombres, contours, creux), **pas une ombre physique noire universelle** en mode Produit. La végétation visible peut comprendre de l’herbe et de petites plantes ; les grands massifs de forêt avec troncs sont surtout répartis par profondeur.

Ce choix conserve la référence intégralement et évite d’inventer du terrain ou de déformer un accès. **Aucun mélange de références ni déplacement de portes/chemins n’est effectué.** Les micro-variations sont de simples accents lumineux, pas de nouveaux biomes.

## Vérification
`verification.json` et `verification_independante.json` donnent les résultats par référence :
- recomposition des PNG égale à la source ;
- toutes les phases des GIF comparées aux images source décodées ;
- dimensions des calques et alpha contrôlés ;
- modifications subtiles confinées à leur calque optionnel ;
- empreinte SHA256 de chaque fichier fourni.

Les sources sont celles fournies par l’utilisateur. Les droits des auteurs et ayants droit PMD restent applicables. Les variantes ne sont pas présentées comme de nouveaux sprites officiels ni attribuées à un artiste humain.

Pas de nouvelle carte `.rsground`, collision, validation PMDO/GPU ou animation inventée pour les PNG statiques. Les anciennes entrées et collections sont conservées.

Scripts : `source/zones_pmd_20_v1/references_layers.py`, `gallery_references.py`, `verify_references.py`, `test_references.cjs`. Pillow, numpy et scipy.
