# Café V2 — mêmes layouts, agrandissement léger, accès originaux

Cette version corrige la V1 : on ne crée plus de nouveaux escaliers au milieu des salles. On reprend la forme des deux cafés et leur accès d’origine, avec un agrandissement modeste. Les anciennes versions restent disponibles.

Ouvrir **`apercu_cafe_multietage_v2.html`** à la racine du dépôt.

## Dimensions
| Référence | Original | Agrandissement A | Agrandissement B |
|---|---:|---:|---:|
| Metano / Halcyon |456×320|488×336|504×344|
| Spinda / EoSO |696×456|728×472|744×480|

A : +32px en largeur, +16px en profondeur. B : +48px et +24px. Des bandes natives de8px sont insérées symétriquement hors du seuil ; les pixels du seuil ne sont ni agrandis, ni retournés. Il s’agit de deux tailles proches des layouts d’origine, pas de dix architectures différentes.

Les deux sous-sols reprennent Spinda ; accueil et deux étages reprennent Metano. Toutes les salles restent sans mobilier. Les murs et leurs ornements fixes sont conservés selon la reconstruction vide.

## Entrées / sorties et éclairage
- Spinda : escalier du bas, encaissement rocheux, marches, lumière du haut des marches et dégradé sombre à leur pied, repris ensemble depuis la référence composée.
- Metano : seuil éclairé rose/blanc du bas, avec son encadrement original.
- **Aucun escalier central ajouté.** Aucune nouvelle liaison entre étages inventée.
- Les accès suivent la bordure agrandie et gardent leur taille native et leur position relative dans le layout.
- Le fond brun canonique est livré séparément : il permet de conserver correctement les transitions des ombres vers le fond.

Les boîtes source et destination de chaque accès figurent dans `manifest.json`. Le test compare directement tous les pixels des seuils finaux aux références originales, pour les20 compositions : égalité RGBA exacte. Cette garantie concerne les accès restaurés, pas l’intégralité du plancher vidé de son mobilier. Le plancher intérieur est réassemblé à partir du matériau café ; les taches lumineuses dispersées de la salle meublée Spinda ne sont pas toutes conservées.

## Fenêtres
Fenêtres **circulaires**, avec de vrais masques circulaires et cadres bois indépendants. Accueil : deux48px ; étage+1 : trois48px ; étage+2 : **deux petits hublots32px séparés, sans baie vitrée**. Aucune fenêtre aux sous-sols. Ces cadres sont de nouveaux assemblages en texture canonique, pas des sprites de fenêtre originaux récupérés.

Jour/nuit change seulement les paysages visibles dans les fenêtres. Les seuils et leur éclairage original restent identiques.

## Calques
Sept calques alignés par salle : fond canonique, sol, vues extérieures, bois/murs, bordure rocheuse, cadres circulaires, accès original. Le fichier `06_escaliers.png` contient désormais le **seuil original complet**, non les escaliers ajoutés de la V1. Il conserve son nom technique pour les exports.

Les compositions et schémas sont dans `A/` et `B/`. `PLANCHE_A.png` et `PLANCHE_B.png` montrent les cinq niveaux. La galerie permet sélection, masquage et téléchargement des calques.

## Sources et vérification
Sources natives et empreintes conservées dans `source/cafe_multietage_v1/references/` :
- [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`, `metano_cafe.rsground` et feuilles Metano café.
- [Minemaker0430/ExplorersOfSkyOrigins](https://github.com/Minemaker0430/ExplorersOfSkyOrigins), commit `4e7422acc263886198113a8256677766e4244228`, `spinda_cafe.rsground`, SpindaCafe1/2.

Scripts : `source/cafe_multietage_v2/{build,gallery,verify}.py`, `test_viewer.cjs`. Dépendances : Pillow, numpy. `verification.json` consigne les comparaisons des sources,20 recompositions, masques circulaires, seuils exacts et tailles sur grille8px. Galerie testée en DOM simulé, sans test de navigateur réel.

Livraison PNG en calques ; pas de nouvelle `.rsground`, de collisions, de transitions ou de validation PMDO. Les répétitions dues à l’insertion de bandes et les raccords du sol vidé restent des assemblages nouveaux, pas une carte canonique inchangée. Droits des ressources : auteurs, contributeurs et ayants droit concernés ; leur présence publique ne constitue pas une licence générale.
