# Dix côtes Métano — nuages et nuit Guilde / Sharpedo

## Ce qui est livré

**10 nouveaux lieux × jour/nuit = 20 Ground**, plus **4 variantes** des deux côtes V2 : **24 `.rsground`** au total dans `cote_metano_dix_zones_pmdo.zip`.

Les deux anciennes cartes V2 et leurs fichiers d'origine ne sont pas remplacés. Leurs nouvelles variantes portent le préfixe `cote10_v2_`. Toutes les ressources du présent lot portent le préfixe `C10_`.

| ID du lieu | Composition nouvelle | Dimensions natives |
|---|---|---:|
| `01_long_cap` | Grand cap à façade ondulée | 1312 × 1024 |
| `02_mesa` | Large mesa entourée de mer | 1312 × 1024 |
| `03_detroit` | Deux rives face à face | 1312 × 1024 |
| `04_deux_paliers` | Deux plateaux superposés | 1312 × 1024 |
| `05_crique` | Crique entre deux ailes rocheuses | 1312 × 1024 |
| `06_cap_est` | Promontoire ouvert vers l'est | 1312 × 1024 |
| `07_cap_ouest` | Promontoire ouvert vers l'ouest | 1312 × 1024 |
| `08_corniche` | Prairie étroite au-dessus d'une très haute face | 1312 × 1024 |
| `09_archipel` | Trois mesas à des profondeurs différentes | 1312 × 1024 |
| `10_trois_terrasses` | Trois niveaux décalés | 1312 × 1024 |
| `v2_promontoire` | Ancien terrain V2 conservé, nouveaux fonds | 1312 × 816 |
| `v2_terrasse` | Ancien terrain V2 conservé, nouveaux fonds | 1200 × 896 |

Exemple de fichier : `Data/Ground/cote10_02_mesa_nuit.rsground`.

## Voir et récupérer les PNG

Ouvrir **`apercu_dix_zones_metano.html`** : aperçu autonome, jour/nuit, animation indépendante du terrain, grille, zoom natif **1×**, visibilité de chaque calque, exports PNG de la composition, du terrain sec et des calques isolés.

Les images embarquées sont des **WebP sans perte**, vérifiés contre les PNG originaux ; les exports sont en PNG, pas en WebP. L'export nuages donne la bande de wrap complète, les autres exports de calque sont alignés aux dimensions de la zone. La planche des dix lieux est un aperçu réduit, **pas un tileset à importer**.

Dans le dépôt, `sprites/cote_dix_zones/` contient aussi les PNG natifs séparés, les compositions jour/nuit, les fonds communs et les manifestes. Pour les deux côtes V2, ces fonds communs de 1312 × 1024 sont à recadrer aux dimensions de la carte ; le viewer et les Ground réalisent déjà ce cadrage.

## Installation dans PMDO

1. **Fermer PMDO** et sauvegarder ton mod.
2. Extraire entièrement `cote_metano_dix_zones_pmdo.zip`.
3. Dans le dossier extrait, avec Python 3 :

   ```sh
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod" --dry-run
   python INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod"
   ```

   Sous Windows, utiliser `py` si nécessaire. Le dossier cible doit contenir **`Mod.xml`**. Pas de Pillow/numpy nécessaire pour l'installation.

4. L'installateur copie les nouvelles cartes et ressources. Il **fusionne l'index natif** avec les entrées déjà présentes, sauvegarde l'ancien index et **refuse tout écrasement d'une carte déjà modifiée**.
5. Relancer PMDO en mode développement avec le bon mod actif, puis ouvrir les cartes dans l'éditeur **Ground**.

Le namespace Lua est lu dans `Mod.xml`. S'il n'est pas déclaré alors que ta version récente de PMDO en utilise un, ajouter `--namespace nom_du_module_lua`. Les scripts sont de simples tables vides ; mer et nuages utilisent l'animation native, pas un script Lua.

### Installation manuelle

Fusionner `Data/` et `Content/` dans le mod, sans écraser de fichiers modifiés. Sur PMDO récent, copier aussi les scripts de `Data/Script/ground/` vers `Data/Script/<Namespace>/ground/`. Reconstruire **l'index complet des tilesets du mod** avec les outils développeur et redémarrer. Aucun `index.idx` partiel n'est livré.

**Ne pas importer les `.rsground` via « PNG to Tileset ».** Ce sont des Ground natives. Si tu importes les PNG à part, utiliser la grille **8 px**, sans agrandir les images : `TexSize = 1`.

## Calques pour tes structures

- Fond natif `LayeredBG` : ciel, astres, nuages.
- Mer : calque de tuiles animées, huit phases.
- Une paire **Prairie / Falaise par plateau**, dans l'ordre de superposition. Les deux terrains V2 ont leur calque historique unique.
- `Vos sols et chemins` : vide.
- `Vos structures - base` : vide, derrière les personnages.
- `Vos structures - avant-plan` : vide, `Top = 4`.
- Décorations et entités vides, sauf un marqueur `entrance` posé dans l'herbe.

Aucun bâtiment, arbre, chemin, meuble ou grotte n'est ajouté. Les lieux composés de plusieurs mesas ne sont pas automatiquement reliés : ajouter tes ponts, accès ou transitions selon ton projet.

**Toutes les collisions sont libres (`Tags = 0`)**, y compris sur la mer et les parois. Dessiner les obstacles après l'ajout des structures. Les maps sont marquées `Released = false` : ce sont des bases d'édition, pas des niveaux jouables finalisés.

## Reprise exacte du style de l'autre agent

Sources récupérées sur `arena/01a082db-guilde-treehouse-pmd`, commit **`c16efe12d74361df5ba8625abb68260f5f8fc6dd`** :

- les **six familles** de `source/falaise/nuages_native.png` ;
- les ciels jour/nuit et les astres natifs ;
- la recette de couleur de `source/rebuild_falaise.py`, également employée par Sharpedo ;
- les deux compositions nocturnes, gardées comme références visuelles.

Les blobs Git des références copiées sont contrôlés dans `reference_autre_agent/provenance.json`. Ce ne sont pas de nouvelles générations ressemblantes.

**Nuages :** les six blocs sont réespacés sur une bande transparente **1440 × 208**, sans les redessiner ni les agrandir. Tous les pixels du nuage source sont conservés. Wrap horizontal à **−4 px/s**, comme le déplacement de 1 px par 250 ms de l'autre agent ; boucle de 360 s sur la bande plus large. Pas de ping-pong.

**Nuit :** luminance `0.2126 R + 0.7152 G + 0.0722 B`, saturation **0,80**, multiplicateurs RGB **(0,40 ; 0,42 ; 0,58)**, ajouts **(4 ; 8 ; 15)**, arrondi identique. Cette recoloration nocturne est volontaire, demandée par l'utilisateur ; les variantes jour gardent les couleurs Métano natives.

**Ciel et astres :** horizon ramené à **y = 144** pour retrouver le cadrage de l'autre agent. La moitié gauche du ciel source, sans son croissant résiduel, est prolongée par réflexion horizontale, sans interpolation. Une seule lune est posée avec les astres source ; les groupes d'étoiles sans lune sont répétés à gauche. Les astres restent **fixes dans ce lot** : le scintillement de l'autre aperçu n'est pas importé.

**Mer :** conserve les huit phases issues du cycle de palette V2, déplacées de y=360 à y=144, et prolonge les 256 dernières lignes sans étirement. La nuit applique la même recette que le terrain. PMDO joue les textures RGBA correspondant aux palettes, et non une palette GPU mutable. `FrameLength = 10` à 60 Hz : **166,67 ms/phase**, boucle **1,333 s**.

## Construction Métano et limites artistiques

Le générateur a fourni **`guide_compositions.png`**, une planche de propositions de silhouettes. Les dix terrains sont ensuite **adaptés avec les matières natives**, pas exportés depuis l'image générée.

Quatre familles de modules complets de `Metano_Town_Cliffs` sont utilisées : descente ouest, face, retour arrondi, remontée est. Leurs couronnes, courbes et pieds sont conservés ; les hautes faces insèrent des répétitions de **six rangées centrales natives**, sans étirer les pixels ni sélectionner/recolorer les ombres indépendamment. Les modules sont déplacés sur la grille pour varier les façades. Aucun retournement ni rotation des textures de falaise.

Les prairies utilisent `Metano_Town_Base`. Pour créer des rebords arrière/latéraux transparents, les **pixels bleus de rivière sont retirés par alpha** de fragments de rives natives : la couleur des pixels survivants est inchangée. Ces tuiles dérivées **ne sont donc pas des copies byte pour byte de la tuile entière d'origine**. La provenance de chaque cellule et son éventuel masque se trouvent dans `provenance/` du ZIP.

Les silhouettes sont des **adaptations modulaires du guide**, pas sa reconstruction exacte. Les raccords de modules et les prolongements de parois restent à contrôler artistiquement à 1× et dans le moteur ; les tests de pixels ne prouvent pas que tous les raccords sont parfaits. Les terrains V2, eux, restent les générations précédentes : leur intégration dans ce lot ne les rend pas canoniques.

## Contrôles effectués

`verification.json` :

- 10 nouvelles compositions différentes ; 24 Ground, dimensions et grille cohérentes ;
- pixels des références de l'autre agent conservés ; six nuages intégralement repris ;
- formule de nuit, alpha, wrap et raccord à un pixel vérifiés ;
- matière native et opérations de découpe relues depuis les `.tile` source ;
- fichiers `.tile` / `.dir`, adresses binaires et références des maps valides ;
- reconstruction exacte des calques de terrain et des huit phases de mer ;
- PNG de composition recomposés sans différence ; images du viewer encodées sans perte ;
- calques de structures vides, collisions libres et marqueurs cohérents ;
- installation complète dans un faux mod : index existant préservé et sauvegardé, namespace créé, carte modifiée protégée.

**Pas de test dans PMDO, pas de désérialisation .NET et pas de validation artistique dans le moteur.** Les textures d'astres ont des alphas intermédiaires : leurs octets prémultipliés sont contrôlés, mais l'arrondi du mélange GPU peut différer légèrement de l'aperçu PNG.

## Reproduire

Avec l'environnement Python du dépôt (Pillow, numpy), depuis la racine :

```sh
.venv/bin/python source/cote_dix_zones/build.py
.venv/bin/python source/cote_dix_zones/verify.py
.venv/bin/python source/cote_dix_zones/package.py
```

La fabrication native se fait dans `~/.cache/cote_dix_pack/` pour éviter de versionner plusieurs centaines de Mo de JSON décompressé. Le ZIP, l'aperçu autonome, les sources et les PNG sont livrés dans le dépôt. `package.py` vérifie de nouveau les fichiers avant d'emballer le lot.

Crédits : références et textures Métano de Palika / Halcyon et contributeurs ; nuages, ciel et ambiance issus des travaux de l'autre agent dans ce dépôt ; mer V2 issue de la planche côtière fournie précédemment. Les ressources tierces ne reçoivent pas une nouvelle licence de redistribution par cette intégration. Les sources techniques natives PMDO et leur version sont documentées dans `source/pmdo_cote/README.md`.
