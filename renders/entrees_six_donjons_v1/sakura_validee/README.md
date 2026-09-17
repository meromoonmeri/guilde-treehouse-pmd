# Entrée Sakura A validée — sept calques et sprites d’arbres

**La première génération validée est conservée, sans modification de son layout.** Tous les calques activés recomposent exactement ses pixels, sur1200×896. Le PNG approuvé reste inchangé dans `../bruts/sakura_printemps_A.png`.

Ouvrir `apercu_sakura_entree_calques_v1.html` à la racine. La galerie propose masquage et téléchargement des calques, sol seul, arbres seuls, ombres seules et feuille d’arbres.

## Livrables principaux
- `SAKURA_ENTREE_A_multicalques.ora` : document OpenRaster éditable (Krita/GIMP compatibles), sept calques alignés.
- `SAKURA_ARBRES_tilesheet_8px.png` : deux arbres isolés, détourage transparent, feuille416×216, grille8px.
- `arbre_centre_sprite.png`, `arbre_avant_gauche_sprite.png` : mêmes sprites séparés, padding transparent au multiple de8, aucun redimensionnement.
- `SAKURA_ARBRES.tsj` : description de la feuille pour Tiled. Ce n’est pas un autotile DTEF de donjon.
- `composition_identique.png` : contrôle du résultat final.
- `manifest.json` : coordonnées source, positions dans l’atlas, points de contact des troncs, dimensions et empreinte de l’image validée.
- `import_png/` : copies des sept calques avec noms de ressources uniques `SAKURA_ENTREE_A_*`, plus la feuille d’arbres.

## Pile de calques, tous en(0,0)
1. **Sol et chemin reconstitué** : `01_sol_chemin_reconstitue.png`. Sol plein, pas de trous transparents en forme d’arbres. Les pixels restés visibles sont conservés ; les zones cachées sont complétées depuis un fond généré puis rapproché de la couleur d’herbe source.
2. **Ombres portées** : `02_ombres_portees.png`, séparées des arbres et de la végétation.
3. **Végétation basse et pétales** : `03_vegetation_basse_petales.png`.
4. **Profondeur de l’entrée** : `04_profondeur_entree.png`, obscurité du passage forestier.
5. **Arbres de la lisière** : `05_arbres_lisiere.png`, massif périphérique.
6. **Arbre central** : `06_arbre_centre.png`.
7. **Arbre avant gauche** : `07_arbre_avant_gauche.png`.

`ARBRES_TOUS_alternative.png` remplace les calques5–7 si un massif unique est préférable. Ne pas le superposer en plus des trois calques.

`SOL_PROPRE_alternative.png` est la plaque de sol entièrement reconstituée, sans conservation des pixels originaux visibles. Elle peut servir pour une nouvelle composition ; **elle change le rendu du sol**. La galerie ne l’utilise pas par défaut. Les variations de teinte restantes dans le sol conservé témoignent des raccords de reconstruction, pas d’une couche de végétation cachée volontairement.

## Détourage et limites
Les deux arbres isolés sont extraits de l’image validée, sans nouveau dessin ni nouvelle pose. Les fragments d’arbres voisins ont été retirés de leurs sprites ; les franges vertes de contact sont rangées avec les ombres de la scène. Les arbres de la lisière se chevauchent : leurs parties occultées **ne sont pas reconstruites** et ne sont donc pas présentées comme une bibliothèque de sprites complets.

Les ombres sont des **pixels peints de la scène sur fond transparent**, avec une partie des transitions de contact. Ce n’est pas une ombre noire universelle en mode Produit ; leur couleur et leur empreinte correspondent à ce sol et à ces placements. Déplacer un arbre sur un autre sol nécessite de déplacer/retoucher son ombre et éventuellement ses pixels de contact. Le document est adapté au montage de la scène, pas à un éclairage dynamique automatique.

Le rendu vise la DA sprite PMD mais vient d’une génération guidée et de corrections de masques. Il n’est ni attribué à un artiste humain, ni présenté comme des sprites canoniques récupérés.

## Échelle et import
Les exports gardent la résolution de l’image validée ; aucun agrandissement ou réduction silencieux. Les sept calques1200×896 et le tilesheet416×216 sont divisibles par8. Pour une découpe8px via PNG to Tileset, utiliser les noms uniques dans `import_png/`. Cela ne garantit pas que la taille des arbres par rapport à un personnage PMDO soit déjà validée : vérifier l’échelle et le placement dans l’éditeur avant de généraliser.

Pas de `.rsground`, collision, transition, animation ni test PMDO/GPU livré. Les autres entrées du lot sont encore des propositions brutes ; seule cette Sakura A a été validée et préparée ici.

## Références et reproduction
- Sinister Woods, PMD Rescue Team : miniature PNG réellement consultée depuis [Mystery Dungeon Wiki](https://mysterydungeonwiki.com/wiki/Rescue_Team:Sinister_Woods). La récupération pleine résolution n’a pas abouti ; ne pas confondre cette miniature avec un export du dépôt PMD-RED-PMDO-PORT.
- PMD Sky : `source/references_54d3731/murky_clairiere.png`, extrait de la référence Murky Forest fournie précédemment.
- Palette de notre prototype `sakura_printemps` utilisée comme guide.

Provenance détaillée : `source/entrees_six_donjons_v1/references/provenance.json`.
Scripts : `layers_sakura.py`, `package_sakura.py`, `test_sakura.cjs`. Pillow, numpy et scipy. Le brut validé et la plaque de travail sont conservés.

`verification.json` : sept calques alignés, recomposition identique, deux sprites égaux à leurs emplacements dans l’atlas et document ORA à sept couches. Tests du viewer en DOM simulé, pas de validation dans un navigateur réel.
