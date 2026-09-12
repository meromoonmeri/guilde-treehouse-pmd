# Côtes Métano — lot 2 : dix zones supplémentaires

**10 nouveaux lieux, chacun en jour et nuit : 20 Ground PMDO natives.** Même matière Métano, mêmes six familles de nuages, même ciel, même recette de nuit et même mer animée que le lot précédent. Aucun ancien fichier de carte n'est remplacé.

## Les lieux 11 à 20

Toutes les cartes mesurent **1312 × 1024 pixels**, sur une grille de **164 × 128 cases de 8 px**.

| ID | Lieu | Organisation |
|---|---|---|
| 11 | Les anses jumelles | Deux caps nord et un grand plateau au sud |
| 12 | Le balcon asymétrique | Deux grandes terrasses décalées |
| 13 | Le chapelet marin | Trois mesas en diagonale |
| 14 | Les corniches parallèles | Deux longues bandes de prairie |
| 15 | Les mesas décalées | Deux massifs de hauteurs différentes |
| 16 | La couronne des embruns | Mesa haute entre deux ailes basses |
| 17 | Le chenal profond | Deux grandes rives séparées par la mer |
| 18 | La grande esplanade | Grand plateau sud et petit balcon nord |
| 19 | L'éperon occidental | Cap haut à l'ouest, terrasse basse à l'est |
| 20 | Les marches du levant | Trois niveaux descendant vers l'est |

Les massifs qui atteignent les bords du canevas sont des prolongements hors carte, pas des îles closes. Les groupes de mesas n'ont pas de passages automatiques : prévoir ponts ou transitions selon ton projet.

## Aperçu et fichiers

- **`apercu_dix_zones_metano_lot2.html`** : aperçu autonome, jour/nuit, animation, calques, grille 8 px, zoom 1×/2×, exports PNG.
- **`cote_metano_dix_zones_lot2_pmdo.zip`** : 20 `.rsground`, quatre tilesets `.tile`, six fonds `.dir`, scripts minimaux, installateur, provenance et aperçu autonome.
- Dans le dépôt : `sprites/cote_dix_zones_lot2/` contient les PNG séparés et les compositions. La planche réduite `PLANCHE_JOUR_NUIT_NE_PAS_IMPORTER.png` n'est pas un asset de jeu.

Les cartes utilisent **`cote20_`**, les ressources **`C20_`**, afin de cohabiter avec le lot 1. Exemple : `Data/Ground/cote20_11_anses_jumelles_nuit.rsground`.

## Installer dans ton mod

1. Fermer PMDO et sauvegarder le mod.
2. Extraire **tout** le ZIP dans un dossier temporaire.
3. Depuis ce dossier, lancer avec Python 3 (aucune bibliothèque supplémentaire) :

   ```sh
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod" --dry-run
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod"
   ```

   Sous Windows, `py` peut remplacer `python`. La cible doit être le dossier contenant **`Mod.xml`**, pas la racine du jeu.

4. L'installateur fusionne l'index natif en préservant ses entrées existantes et sauvegarde l'ancien index. Il refuse d'écraser une carte ou ressource dont le contenu a déjà été modifié.
5. Relancer PMDO avec le mod actif, ouvrir l'éditeur **Ground** et choisir une carte `cote20_…`.

Le namespace Lua est lu dans `Mod.xml`. Sur une version récente où il n'est pas déclaré, préciser `--namespace nom_du_module_lua`. Les scripts sont vides : l'animation est native.

Sans Python : fusionner `Data/` et `Content/` sans écraser tes modifications, placer les scripts sous `Data/Script/<Namespace>/ground/` si nécessaire, puis reconstruire **l'index complet des tilesets du mod** et redémarrer. Aucun `index.idx` partiel n'est fourni.

Les Ground ne s'importent pas avec « PNG to Tileset ». Pour importer les PNG séparément, garder la taille native et choisir **8 px**, sans redimensionnement.

## Calques et animations

- Fond `LayeredBG` : ciel, lune/étoiles, nuages en wrap.
- Mer : huit phases issues du cycle de palette V2 ; `FrameLength = 10`, soit environ **166,67 ms/phase** à 60 Hz.
- Une paire **Prairie / Falaise par plateau**, dans l'ordre de superposition.
- Calques vides : **Vos sols et chemins**, **Vos structures - base**, **Vos structures - avant-plan** (`Top = 4`).
- Décorations et entités libres, sauf un marqueur `entrance` dans l'herbe.

Les nuages gardent leur taille et leurs pixels : bande **1440 × 208**, défilement **−4 px/s**, sans aller-retour. Les astres sont fixes, comme dans le premier lot Métano. Les images de l'aperçu sont encodées en WebP **sans perte**, contrôlées contre les PNG ; les téléchargements de calques restent en PNG.

**Aucun bâtiment, arbre, grotte, meuble ou chemin n'est posé. Toutes les collisions sont libres (`Tags = 0`)**, même sur les parois et la mer. Dessiner les obstacles et les accès avant d'utiliser ces bases comme niveaux jouables. Les cartes portent `Released = false`.

## Même DA, nouveaux agencements

Le guide généré `source/cote_dix_zones_lot2/guide_compositions.png` propose les dix compositions. Les terrains de jeu sont des adaptations avec les modules natifs, pas des copies de pixels de ce guide.

Matière : `Metano_Town_Base` et `Metano_Town_Cliffs`, sources Halcyon / Palika et contributeurs, déjà conservées dans le dépôt. Couronnes, retours et pieds viennent des modules natifs ; les grandes faces répètent six rangées centrales sans étirer, tourner ni recolorer les textures de jour. Les rives arrière et latérales retirent par alpha les pixels de rivière bleue : ce sont donc des découpes dérivées, pas des copies intégrales de chaque tuile source. La provenance par cellule est dans `provenance/` du ZIP.

Nuages, ciel et nuit : ressources de l'autre agent au commit **`c16efe12d74361df5ba8625abb68260f5f8fc6dd`**, reprises par le pipeline du lot 1. Les fichiers d'origine et leurs blobs Git sont dans `source/cote_dix_zones/reference_autre_agent/`. La nuit applique sa saturation **0,80**, ses multiplicateurs **(0,40 ; 0,42 ; 0,58)** et ajouts RGB **(4 ; 8 ; 15)**. La mer reste le cycle V2 issu de la planche côtière fournie précédemment.

La disponibilité des ressources de référence ne leur attribue pas une nouvelle licence de redistribution.

## Validation et limites

Contrôles indépendants :

- exactement dix nouveaux lieux et vingt Ground ; compositions distinctes entre elles **et du lot précédent** ;
- provenance native des cellules, découpe alpha et formule de nuit ;
- ressources graphiques référencées, headers binaires, tailles, frames et reconstruction des pixels ;
- conservation des nuages, continuité du wrap et recomposition des PNG ;
- calques vides, grilles, collisions et marqueurs ;
- installation dans un faux mod avec index préexistant : fusion, sauvegarde et refus d'écrasement.

**Pas de test d'ouverture dans PMDO ni de désérialisation .NET.** Les raccords artistiques et l'échelle en jeu restent à vérifier à 1× puis dans le moteur. L'arrondi GPU des astres translucides peut différer légèrement du PNG. Les formes adaptent le guide aux modules ; elles ne prétendent pas reproduire exactement ses silhouettes.

## Reproduction

Depuis la racine du dépôt, avec Pillow et numpy :

```sh
.venv/bin/python source/cote_dix_zones_lot2/build.py
.venv/bin/python source/cote_dix_zones_lot2/package.py
```

`package.py` relance la validation avant de créer l'archive. Les JSON natifs décompressés sont fabriqués dans `~/.cache/cote_dix_pack_lot2/`, hors Git ; les PNG, sources, aperçu et ZIP sont livrés dans le dépôt. Les fonctions communes du lot 1 sont réutilisées avec des sorties et préfixes séparés ; ses cartes ne sont pas régénérées.
