# Layouts légers sur magenta — feuillage, siphons, irisations et lave

Galerie autonome : **`apercu_variantes_magenta_v1.html`**, à la racine. La galerie ouvre les nouveaux ajouts, permet de masquer chaque calque, de contrôler les animations et d’exporter chaque phase en PNG.

## Derniers ajouts demandés

| Dossier dans `variantes/` | Modification | Animation |
|---|---|---|
| `foret_mousse_immersive` | Bordures de feuillage, palette mousse dorée | Statique |
| `foret_emeraude_immersive` | Même cadrage de feuillage, palette émeraude | Statique |
| `sables_siphons_eau` | Siphons d’eau à la place des siphons de sable ; un petit galet décalé de4px à droite et2px vers le haut |6 phases ×60ms, cycle360ms |
| `cristal_irise` | Reflets bleu–rose–blanc sur la glace et les cristaux | Base12 phases ×160ms + reflets24 phases ×80ms ; cycle commun1920ms |
| `cote_cendres_lave` | Roche gris cendré, eau remplacée visuellement par de la lave, légère lueur chaude sur la berge | Lave30 phases ×130ms + lueur30 phases ×130ms ; cycle3900ms |

« Roche couleur centre » a été interprété comme **gris cendré**. Il s’agit d’une proposition visuelle, pas d’un changement des dégâts, collisions ou règles de terrain PMDO.

L’archive **`VARIANTES_PMD_calques.zip`** regroupe ces cinq ajouts, leurs PNG, frames, boucles WebP complètes et documents OpenRaster. Les huit variantes de base restent accessibles dans `zones/` et dans la galerie, sans remplacement.

### Feuillages immersifs
Deux rameaux ont été générés isolément sur magenta, détourés puis placés en bordure. Leurs sprites complets sont conservés dans `rameaux_detoures/`. Les bordures gauche/droite et leur ombre de premier plan sont des calques séparés.

Les accès du haut et du bas, ainsi que le corridor central, restent dégagés. Le test contrôle l’absence de feuillage dans la bande centrale. Les feuilles sont statiques ; aucune animation de vent non demandée n’est annoncée.

La première recherche `bruts/feuillage_immersif.png` reproduisait trop de forêt : elle est archivée mais **n’est pas utilisée**. La feuille de rameaux utilisée est `bruts/rameaux_premier_plan.png`.

### Siphons d’eau et lave : adaptations, pas animations natives retrouvées
Les siphons d’eau adaptent les couleurs et le contraste des **six phases natives de sable** tout en conservant leurs formes et leur timing. La lave adapte les **trente phases de l’eau côtière**. Ce sont des liquides stylisés dérivés des séquences de référence, **pas des séquences originales PMD d’eau tourbillonnante ou de lave récupérées dans les fichiers du jeu**.

Les empreintes alpha des zones animées et leurs cadences restent inchangées. Leurs mouvements héritent donc de la référence : les siphons gardent la contraction des anneaux, la lave garde le mouvement des nappes côtières. La lueur chaude ajoutée à la berge est nouvelle et indépendante ; elle peut être désactivée.

### Reflets bleu–rose–blanc
Le calque de reflets utilise un champ RGB **fixe** allant du bleu au blanc et au rose. Seule son opacité varie ; il n’y a ni rotation continue de teinte ni déplacement arbitraire de la géométrie des reflets. Le masque sélectionne les zones claires du passage et des cristaux, pas tout l’arrière-plan.

Les24 phases de reflets partagent le même cycle de1,92s que les12 phases de base. La galerie compose ces deux cadences séparément. Le calque peut être masqué pour retrouver la version boréale de base.

## Méthode du premier lot, conservé

Quatre layouts légèrement modifiés, deux palettes chacun :
- côte : ardoise rosée / cuivre et lagon ;
- passage cristallin : boréal / opalin ;
- forêt à racines : mousse dorée / émeraude ;
- bassins de sable : ocre / rose du désert.

Références réellement utilisées : les fichiers du commit utilisateur **`8eb46bc`**, identifiants `D25P11A`, `D17P33A`, `D24P31A`, `D14P11A`. Les compositions fidèles précédentes et tous les fichiers racine sont inchangés.

Pipeline :
1. extraction des références et de toutes leurs phases ;
2. préparation de masques magenta pour les régions animées ;
3. génération guidée de petites modifications du décor statique ;
4. détourage du magenta et nettoyage des franges ;
5. remise au canvas de référence au plus proche voisin ;
6. protection des empreintes animées et raccords de berge ;
7. calques de sol, ombres de contact, massifs/décor, raccords et animation ;
8. harmonisation des couleurs identique sur toutes les phases de chaque palette.

Les recherches restent dans `bruts/`. Ce ne sont pas des sprites canoniques identiques : le terrain a été guidé au générateur et les palettes ont été modifiées volontairement. Les nouveaux dessins ne sont pas attribués aux auteurs des sprites natifs ni à un artiste humain.

## Sols, ombres et limites des calques

Les calques de sol incluent une reconstruction sous les éléments masqués, issue de plaques de sol générées. Pour les sables, deux tentatives de génération du sol vide ont échoué : le sol sous les rochers est reconstitué par répétition d’un échantillon24×24 prélevé dans le sable du terrain généré. L’échantillon et sa reconstruction sont archivés dans `masques/sables/`.

Les ombres de contact sont recréées depuis les silhouettes détourées ; les ombres intrinsèques des textures restent dans les objets. Les raccords proches des zones animées sont protégés pour éviter les fuites de magenta et les décrochages de vagues.

Les massifs forestiers et rocheux sont des couches de composition. Les faces cachées des arbres et parois **ne sont pas toutes reconstruites** ; il ne faut pas les considérer comme une bibliothèque de tous les objets complets déplaçables librement. Les sprites de rameaux, eux, sont isolés et réutilisables.

## Fichiers à utiliser

Chaque dossier de scène contient :
- `COMPOSITION.png` : rendu de phase0 ;
- PNG des calques statiques, avec noms uniques ;
- PNG de chaque phase des calques animés, s’il y en a ;
- `ANIMATION_COMPLETE.webp` pour la boucle complète, sans raccourci tronqué ;
- un `.ora` éditable, contenant les calques et la phase0 des groupes animés.

Les PNG conservent les canvas de référence :648×504,456×504,504×480 ou456×384 selon la zone. Les générations brutes ont été ramenées à ces dimensions au plus proche voisin, pas lissées. Les dimensions finales sont divisibles par8 pour une découpe8px via PNG to Tileset ; **cela ne constitue pas une validation de l’échelle ou du rendu en jeu**.

La galerie et les manifestes donnent l’ordre des couches, les fichiers, les durées et les cycles. Les calques commencent tous en(0,0). Le `.ora` est un document de composition statique à la phase0, pas une animation intégrée à PMDO.

## Vérifications

`verification.json` :
- huit variantes de base et cinq variantes supplémentaires ;
- **96 frames de base** vérifiées dans les régions protégées contre les références après transformation de palette ;
- **102 PNG de couches animées supplémentaires**, incluant des adaptations et des effets nouveaux, pas102 frames natives inédites ;
- dimensions et recompositions opaques contrôlées ;
- ORA recomposés et comparés aux PNG ;
- alpha des liquides adaptés égal à celui de leur parent ;
- couleurs RGB fixes des reflets, variation effective de l’alpha ;
- lueur de berge confinée hors du liquide ;
- accès central dégagé par le feuillage ;
- galerie testée en DOM simulé.

**Pas de validation PMDO/GPU, de carte `.rsground`, de collision ou de comportement de lave.** Les tests de fichiers ne remplacent pas l’essai visuel et jouable dans l’éditeur.

## Reproduction

Scripts dans `source/layouts_magenta_v1/` : `prepare_sources.py`, `build.py`, `palette.py`, `enhancements.py`, `gallery.py`, `boards.py`, `verify.py`, `test_viewer.cjs`. Pillow, numpy, scipy ; Node uniquement pour le test DOM. Les générations sont archivées, pas recréées par un build déterministe.
