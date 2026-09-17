# Manuel de production — falaises Métano et entrées de donjon PMDO

**Version du document : 13 septembre 2026 · cible moteur : PMDO 0.8.12.**

Ce manuel décrit les méthodes effectivement employées, leurs limites et le protocole nécessaire pour passer des contrôles de fichiers à une validation dans le moteur. Il ne certifie pas une installation ou une ouverture de carte qui n’a pas eu lieu.

## 1. État exact des livraisons

| Élément | État |
|---|---|
| Pack `cotes_metano_abyss_0812_pmdo.zip` | Livré : dix terrains, vingt variantes jour/nuit |
| Filtre nocturne Abyss | Implémenté et comparé aux sources |
| Sept falaises + trois entrées | Livrées dans `mod_metano_expeditions_pmdo_0812.zip` : 20 nouveaux Ground + 20 précédents |
| Références Crooked Cavern / Brine Cave / Drenched Bluff | Tilesets téléchargés, décodés et références des cartes contrôlées |
| Installation PMDO ici | **Moteur installé depuis RUNTIMEPMDO, ressources de base récupérées** |
| Désérialisation par le vrai chargeur | **40 Ground du mod Expéditions : PASS, sans affichage** |
| Éditeur graphique / rendu / test de jeu | **Lancement en échec (code 139), non validés** |

Le détail des tentatives est dans [installation_pmdo.json](source/cote_v5_expeditions/installation_pmdo.json). Un programme Python qui vérifie du JSON ou reconstruit une image n’est pas le moteur PMDO. Depuis cette première étude, le [test natif documenté](source/pmdo_runtime/README.md) appelle le vrai chargeur PMDO et valide vingt désérialisations, sans GPU.

## 2. Contrat artistique et technique

1. Garder des silhouettes organiques, de vastes plateaux et de hautes parois, pas des plateformes rectangulaires indépendantes.
2. Utiliser Métano pour la matière de jour : herbe, roche, rebords et retours.
3. Étudier les entrées de Palika et d’Explorers of Sky Origins pour leur **layout et leur construction**, pas pour copier leurs textures dans les nouvelles falaises.
4. Conserver les nuages et les ressources de ciel Guilde/Sharpedo ; appliquer au terrain le filtre exact demandé d’Abyss.
5. Séparer les éléments pour permettre l’édition : terrain, détails, volumes, entrée, animations, éléments devant les personnages.
6. Ne pas placer des maisons, arbres, PNJ ou scripts narratifs non demandés.
7. Préserver les anciennes livraisons ; attribuer au nouveau lot ses propres identifiants.
8. Une référence générée ne constitue jamais une preuve de fidélité des pixels natifs.

### Ce que signifie « même méthode Guilde »

Une composition lisible, des ressources séparées, des transparences propres, des fonds animés indépendants et un véritable Ground modifiable. Cela ne signifie pas que toute image générée peut être importée telle quelle en jeu.

## 3. Retrouver les vraies ressources, pas seulement les captures

Pour chaque dépôt de référence :

- résoudre un commit précis, pas seulement un nom de branche ;
- récupérer la carte `.rsground` et lire toutes les références `Sheet` de ses frames ;
- télécharger uniquement les feuilles référencées nécessaires à l’étude ;
- conserver le chemin distant, le commit, le hash de blob Git et le SHA-256 local ;
- lire également les calques, objets, marqueurs, collisions et scripts pertinents ;
- ne pas confondre un nom de tileset et une carte : une feuille peut contenir plusieurs dispositions ou phases.

Les références du nouveau lot sont enregistrées dans [provenance.json](source/cote_v5_expeditions/references/provenance.json). Les contrôles sont reproductibles avec :

```sh
.venv/bin/python source/cote_v5_expeditions/audit_references.py
```

## 4. Résultat de l’étude des trois entrées

| Référence | Dimensions réelles | Grille | Calques graphiques |
|---|---:|---:|---|
| Palika — Crooked Cavern | 320 × 240 px | 40 × 30 cellules de 8 px | Base, Objects, Shadows |
| EoSO — Brine Cave | 648 × 504 px | 27 × 21 cellules de 24 px | Un calque référant la feuille animée |
| EoSO — Drenched Bluff | 528 × 408 px | 66 × 51 cellules de 8 px | Background, Details |

### Crooked Cavern

Feuilles : `Crooked_Cavern_Base`, `Crooked_Cavern_Objects`, `Crooked_Cavern_Shadows`.

La base contient déjà la bouche de grotte, les grandes masses latérales et le sol du vestibule. Les détails ne servent pas à construire toute la structure. Les ombres sont un troisième calque, avec des valeurs d’alpha intermédiaires. La carte contient aussi un marqueur et un spawner d’allié : ils appartiennent au scénario de Palika, pas à notre futur pack.

**À retenir pour le layout :** bouche sombre lisible au fond, large espace de rassemblement au premier plan, convergence des parois vers l’accès, séparation des ombres et des détails.

**À ne pas copier :** la palette rocheuse, les objets ou les callbacks narratifs qui dépendent de `common`, `PartnerEssentials` et de la progression du chapitre 3.

### Brine Cave

Feuille : `Brine Cave Entrance`. Son index est en **24 px**. Sa grande image de feuille n’est pas la taille de la carte : le tableau de placements permet de reconstituer une carte de 648 × 504 px. Les 567 cellules du calque possèdent plusieurs frames ; cela ne prouve pas que chacune change visuellement à chaque phase.

**À retenir pour le layout :** parvis asymétrique, entrée reculée dans la falaise, progression latérale depuis la côte, mer au pied de la corniche.

**Erreur à éviter :** considérer la feuille comme une image de carte, ou réduire chaque tuile 24 × 24 à 8 × 8. Pour convertir une grille, une tuile 24 × 24 se découpe en **neuf cellules 8 × 8**, sans modifier ses pixels. Dans notre futur lot, ses textures restent des références d’étude : nous reconstruisons la matière avec Métano.

### Drenched Bluff

Feuilles : `DrenchedBluffEntranceBackground` et `DrenchedBluffEntranceDetails`.

La base décrit le sol et les volumes de fond ; le second calque contient les blocs et détails qui encadrent le passage. Une entrée de donjon peut être un **corridor ouvert**, pas forcément une bouche de grotte noire.

**À retenir pour le layout :** deux épaules rocheuses, axe de progression vers le nord, seuil dégagé, resserrement progressif. Ne pas copier les rochers verts, les végétaux ou le PNJ de la référence.

Le [rapport complet](source/cote_v5_expeditions/audit/references.json) donne les feuilles, cellules occupées, tailles, alpha, animations et entités. Les images du dossier `audit/` sont des études, **pas des nouveaux assets à importer**.

## 5. Concevoir sept falaises et trois entrées

Avant de produire les ressources, écrire pour chaque carte :

- sa fonction : espace libre, passage, belvédère, entrée ;
- son nombre de terrasses et leur ordre de profondeur ;
- les côtés où le terrain rejoint la limite de carte ;
- la position du point d’arrivée ;
- pour un donjon : position du seuil, largeur libre, direction d’entrée et zone de retour ;
- les zones réservées aux futures structures ;
- le rôle des fonds et la présence de mer.

Les dix fonctions proposées pour ce lot sont : crête sinueuse, caps reliés, éventail de terrasses, lagune latérale, côte découpée, sommet à balcon, cap à chenal ; puis vestibule de grotte, corniche d’accès maritime et passage entre deux épaules. Ces intentions sont maintenant réalisées dans le lot Expéditions. Voir sa [notice et ses limites](source/cote_v5_expeditions/README.md).

Une silhouette supplémentaire doit être réellement nouvelle : retourner, étirer ou recolorer une ancienne carte ne suffit pas.

## 6. Utiliser le générateur uniquement comme guide

Fournir les références de caméra, d’échelle et de composition. Demander explicitement l’absence de structures et de détails non voulus. Un guide peut proposer le rythme général des masses, mais ne fournit pas les couleurs finales des roches.

Contrôler systématiquement : nombre de panneaux, numérotation, absence d’objets parasites, continuité des terrasses et échelle de l’entrée. Le guide actuel `guide_compositions.png` a produit **douze panneaux avec des numéros répétés**, malgré une consigne de dix : il n’est pas un plan de production conforme et ne doit pas être découpé automatiquement en dix cartes. Les compositions utiles doivent être sélectionnées/redéfinies dans une spécification explicite.

Ne jamais tenter de réparer une roche non conforme par une succession de retouches générées présentées comme « pixel perfect ». Plusieurs essais précédents ont conservé les mauvaises pierres ou introduit des artefacts.

## 7. Échelle : pixels, cellules et affichage

Trois notions différentes :

- **pixel natif** : unité de l’image source ;
- **cellule Ground** : `TexSize × 8` pixels ;
- **zoom de l’éditeur/aperçu** : agrandissement d’affichage, pas modification des ressources.

Nos packs récents utilisent `TexSize=1`. Une feuille source peut cependant avoir un autre `tileSize`, comme les 24 px de Brine Cave. Lire les en-têtes : ne pas généraliser à partir d’un seul pack.

Interdits pour le terrain natif de jour : agrandissement arbitraire, interpolation, rotation, miroir, recoloration improvisée. La nuit constitue une exception explicite demandée par l’utilisateur, avec un filtre précisément identifié.

Pour vérifier l’échelle, comparer un module complet avec son témoin à 1×, pas seulement une planche réduite. Un contact sheet peut créer du moiré ; il ne remplace pas la lecture des pixels natifs.

## 8. Masques et silhouette

Séparer au minimum :

- occupation du terrain ;
- surface herbeuse ;
- roche ;
- espace extérieur ;
- pour les nouvelles entrées : vide de la bouche, seuil et passage.

Les masques définissent la géométrie ; ils ne transportent pas les couleurs du générateur. Leur union et leurs intersections doivent être vérifiées. Des pixels de roche ne doivent pas apparaître dans le ciel ; une bouche de grotte ne doit pas être bouchée par une couche de remplissage.

Pour les lots déjà approuvés, comparer exactement l’alpha final avec le masque approuvé. Pour de nouveaux layouts, établir et valider leur propre géométrie avant de prétendre l’avoir « conservée ».

### Bords collés à la grille

Retirer les bandes extérieures vides sur les côtés de connexion. Aligner le recadrage sur 8 px ; documenter les pixels éventuellement coupés. Ne pas étirer le dessin pour remplir le cadre.

Tester les contacts séparément pour chaque côté. Un seul contact n’est pas la preuve que tout le bord est plein, et une falaise qui touche le cadre n’est pas automatiquement une sortie praticable ou scriptée.

## 9. Reconstruction Métano par modules cohérents

Référence actuelle : `source/cote_v4_abyss/prepare.py`.

| Fonction | Feuille | Rectangle en pixels |
|---|---|---|
| Herbe | Metano_Town_Base | `(0,640)-(128,768)` |
| Face | Metano_Town_Cliffs | `(912,464)-(976,512)` |
| Retour arrondi | Metano_Town_Cliffs | `(680,464)-(744,512)` |
| Couronne | Metano_Town_Cliffs | `(912,448)-(976,464)` |
| Pied | Metano_Town_Cliffs | `(912,528)-(976,544)` |

Préférer des rectangles cohérents de matière et des modules complets de sommet/face/pied à une sélection aléatoire de fragments de 8 px. Les grandes faces du pack livré répètent des panneaux 64 × 48, les retours suivent les bords et les couronnes suivent les terrasses.

Découper par alpha conserve les RGB source des pixels retenus, mais change le contour du module. C’est une adaptation documentée, pas une copie intégrale de la carte Métano.

Les pixels d’herbe contenus dans une couronne rocheuse sont exclus lorsque leur placement créerait une marche verte rectangulaire. Cela retire des pixels ; cela ne repeint pas les autres.

### Limite fondamentale

Un remplissage natif peut rester trop répétitif ou trop plat. « Zéro différence RGB » prouve une origine, pas une qualité artistique. Examiner les raccords, la continuité des lignes rocheuses, la profondeur et l’échelle. Ne pas appeler « meilleur résultat » une mosaïque uniquement parce que ses tuiles sont authentiques.

## 10. Construire les entrées sans copier leurs textures

La construction des entrées dissocie :

1. relief de la falaise Métano ;
2. cadre et rebord de l’ouverture ;
3. vide de la cavité ;
4. seuil et espace praticable devant la bouche ;
5. ombre locale éventuelle, sur son propre calque ;
6. détails facultatifs ;
7. marqueur et déclencheur de transition.

Étudier Crooked/Brine/Drenched ne donne pas l’autorisation artistique de conserver leurs palettes dans un décor demandé Métano. Si un module Métano ne permet pas une ouverture donnée sans déformation, adapter le layout ou concevoir un assemblage natif explicite. Ne pas agrandir une petite porte ni coller silencieusement une façade étrangère.

La bouche doit se lire à la taille du personnage. Le parvis doit permettre de se présenter devant le seuil et de revenir en arrière. Le héros ne doit pas pouvoir marcher dans la paroi parce que le dessin semble ouvert.

## 11. Architecture des calques

Dans le pack Métano/Abyss livré : mer, herbe, faces, retours, couronnes, pieds, puis trois calques de structures vides. Les fonds ciel/astres/nuages sont séparés de ces couches de tuiles.

Pour les nouvelles entrées, ajouter des couches dédiées au cadre/seuil et à l’ombre, sans les fusionner avec la roche globale. Un élément qui doit passer devant le personnage doit utiliser une couche appropriée : `Top=4` dans le moteur audité. Ne pas placer toute la falaise au-dessus du joueur par défaut.

Les entités, objets et décorations sont distincts des calques de tuiles. Un marqueur d’arrivée n’est pas un PNJ ni un téléporteur automatique.

## 12. Filtre nocturne exact d’Abyss

Source épinglée : Abyss V4, commit `55860b9a5eb48697a3cea3a8bdfce5f0529d6141`, script `tools/tile_night.py`, blob `438383f479e2d80a6a0b3be4cced4087470d9835`.

Pour un pixel non transparent :

```text
gris = 0.299*r + 0.587*g + 0.114*b
luminance = gris / 255
k = 0.20 + 0.30*luminance
saturation = 0.95
r' = (r*saturation + gris*(1-saturation)) * k*0.52
g' = (g*saturation + gris*(1-saturation)) * k*0.70
b' = (b*saturation + gris*(1-saturation)) * k*1.60 + 6*luminance
```

Respecter l’ordre des opérations du script et sa troncature entière, conserver l’alpha et ne pas refiltrer une image déjà nocturne.

Implémentation : `source/cote_v4_abyss/night.py`. Vérifications réalisées sur 1421 couleurs des sources, puis sur les feuilles complètes `Base_Night`, `Cliffs_Night` et `Fringe_Night`.

Le filtre est appliqué une fois aux terrains, à la mer et aux nuages. Les ressources déjà distinctes de ciel nocturne et d’astres restent leur artwork nocturne. Ne pas ajouter le filtre Guilde/Sharpedo par-dessus celui d’Abyss.

## 13. Mer, nuages et temps moteur

- Mer actuelle : huit phases issues de la côte V2, pas la rivière canonique Métano.
- `FrameLength=10` : dix frames moteur par phase ; boucle de 80 frames, soit environ 1,33 s à 60 Hz.
- Nuages : six familles prélevées sans agrandissement, bande de 1440 × 208 px, déplacement horizontal −4 px/s, répétition X.
- Ciel et astres : ressources distinctes ; contrôler le placement de la lune sur la carte la plus étroite.

Une animation de palette s’implémente ici par des frames explicites. Ne pas confondre les phases avec des types de terrain. Vérifier les transitions de fin de boucle et éviter un raccord discontinu au wrap.

## 14. Alpha droit et alpha prémultiplié

Les PNG d’édition sont généralement traités en alpha droit. Les textures natives `.tile` et `.dir` du moteur audité utilisent des pixels prémultipliés :

```text
RGB_stocké = RGB_droit * alpha / 255
```

Un pixel translucide n’a donc pas les mêmes RGB dans les deux représentations. Comparer les données dans le bon espace, sinon un test peut signaler de faux écarts ou masquer une double multiplication.

Crooked Cavern illustre réellement cette question : sa feuille Shadows contient plusieurs niveaux d’alpha. Pour une image d’étude, l’auditeur déprémultiplie avant composition Pillow. L’opération introduit un arrondi possible ; une capture moteur peut différer légèrement. Ne pas revendiquer une identité GPU sur cette seule image.

## 15. Format natif des ressources

### `.tile`

En-tête : `int32 tileSize`, `int32 count`, puis `count` enregistrements `(int32 x, int32 y, int64 offset)`. À chaque offset : `int64 longueurPNG`, puis PNG. Plusieurs coordonnées peuvent partager le même payload.

Une ancienne documentation de référence décrit deux mots de 32 bits pour la longueur et un padding. Pour nos exports, suivre la lecture moteur auditée en **64 bits** ; les deux descriptions se confondent seulement pour de petites longueurs dont le mot supérieur vaut zéro.

### `.dir`

Pour les fonds statiques employés : longueur PNG en 64 bits, PNG prémultiplié, puis quatre entiers de 32 bits décrivant largeur, hauteur, type de rotation et nombre de frames. Ne pas remplacer ces fichiers par des PNG renommés.

### `index.idx`

Index des banques de tuiles : nombre de feuilles, nom encodé comme une chaîne .NET à longueur 7-bit UTF-8, puis nœud d’index. Il doit contenir toutes les feuilles du projet concerné. Ne jamais écraser l’index d’un projet existant avec un index limité au nouveau pack.

## 16. Construire un `.rsground`

Partir d’un schéma reconnu et audité, pas d’un simple JSON inventé. Les packs récents ciblent la sérialisation `0.8.12.0` et le type `RogueEssence.Ground.GroundMap, RogueEssence`.

Contrôler notamment : `TexSize`, `AssetName`, nom, dimensions, `Layers`, `obstacles`, `Background`, `Entities`, décorations et marqueurs. Les tableaux de tuiles sont orientés `Tiles[x][y]`.

Le numéro de version inscrit ne constitue pas à lui seul une preuve de compatibilité. L’audit des sources réduit le risque ; seul un chargement réussi dans le moteur cible complète cette vérification.

## 17. Collisions, seuil et destination du donjon

Les anciens packs côtiers laissent volontairement les collisions libres. **Ce n’est pas une configuration jouable finale.** Pour les entrées :

- définir le sol praticable et les parois bloquantes ;
- laisser un passage suffisamment large pour le collider du personnage ;
- placer l’arrivée sur du sol libre ;
- séparer le marqueur d’arrivée, la zone de déclenchement et le point de retour ;
- vérifier les noms, callbacks Lua et identifiants de destination ;
- ne pas reprendre les scripts narratifs de Palika/EoSO avec leurs dépendances de quête ;
- tant que le donjon cible n’est pas fourni, documenter explicitement le raccord manquant.

Une entrée visuellement complète n’est pas une transition fonctionnelle. Tester aussi le retour, l’annulation éventuelle, la sauvegarde/recharge et la variante nocturne.

## 18. Projet séparé et installation sûre

Un pack autonome d’édition comporte `Mod.xml`, ses propres `Data/Ground`, `Data/Script/<namespace>/ground`, `Content/Tile`, `Content/BG` et son index complet. Le nom de dossier, namespace, UUID et préfixes de banques doivent être distincts de ceux des anciens lots.

Pour un projet existant, employer l’installateur de fusion : prévalidation, détection des conflits, conservation des autres tilesets, sauvegarde de l’index, puis écriture. Tester une seconde installation identique et le refus d’écraser une carte modifiée.

Ne pas importer un PNG de composition contenant ciel, nuages et mer comme tileset unique. Cela détruirait la séparation nécessaire à l’édition et aux animations.

## 19. Installer et démarrer le vrai PMDO ici

Cible : Linux x64, version 0.8.12. L’asset officiel du moteur est `pmdc-linux-x64.zip`, 77 503 089 octets, release PMDC v0.8.12. Un moteur seul peut nécessiter les ressources du jeu et des bibliothèques graphiques ; vérifier le contenu avant de conclure que l’installation est complète.

Les tentatives initiales via l’hôte des releases et les dépôts Debian ont échoué. **Ce blocage a ensuite été contourné grâce au dépôt `meromoonmeri/RUNTIMEPMDO` fourni par l’utilisateur** : téléchargement du ZIP comme blob Git, CRC valide et SHA-256 identique au digest de la release officielle. Le binaire démarre, répond à `-help` et annonce 0.8.12.0 / .NET 8.0.26.

Les ressources de base ont été récupérées depuis `audinowho/DumpAsset` au commit épinglé dans le rapport. Le manque initial de `Base/PathParams.xml` est résolu. Il n’est plus nécessaire de demander une archive Linux à l’utilisateur.

L’éditeur plante encore au démarrage avec le code 139, y compris après un essai avec les bibliothèques embarquées et SDL offscreen. La cause exacte reste à diagnostiquer ; aucun rendu GPU n’est validé. En revanche, un hook Lua temporaire dans la copie de cache a permis d’appeler **le véritable `DataManager.GetGround`** sur les vingt cartes livrées : PASS pour les dimensions, la grille et les calques. La constante de grille graphique est initialisée explicitement pour ce test sans affichage, puis le script original est restauré.

Voir [installation, provenance, résultats et reproduction](source/pmdo_runtime/README.md). Les étapes restantes sont le diagnostic du crash graphique, une session éditeur fonctionnelle, puis les tests visuels, animations et collisions. Le test sans affichage ne les remplace pas.

Le code `PMDC/Program.cs` de v0.8.12 confirme les options `-dev`, `-quest [folder]`, `-asset [path]`, `-appdata [path]`. Exemple de principe **non exécuté** :

```sh
./PMDC -dev -quest cotes_metano_abyss_0812
```

Adapter le nom réel de l’exécutable et les chemins après extraction. Ne pas utiliser aveuglément une commande de conversion/réindexation contre les données de l’utilisateur. Ne pas considérer un essai `-help` comme un démarrage de l’éditeur.

## 20. Protocole de validation en cinq niveaux

### A — Provenance

Hashes des fichiers, coordonnées des prélèvements, droit/gauche inchangés, absence de recoloration de jour.

### B — Images

Dimensions divisibles par la grille, alpha attendu, pas de bande vide aux connexions, pas d’arbre/bâtiment parasite, pas de trou involontaire, raccords et volumes examinés au zoom natif.

### C — Formats

Décoder les `.tile`/`.dir` exportés, résoudre toutes les frames, reconstruire les couches, contrôler prémultiplication, index, entités et scripts. Ne pas simplement relire les PNG d’entrée.

### D — Installation

Projet temporaire avec une banque étrangère, simulation sans écriture, fusion, double installation, refus de conflit, vérification du namespace. Puis tester le ZIP réellement livré, pas seulement un dossier de staging.

### E — Moteur

Ouverture dans PMDO 0.8.12, tous les calques visibles, comparaison 1×, animation pendant plusieurs boucles, marche et collisions, déclenchement/retour de donjon, sauvegarde et réouverture. Capturer les erreurs et ne pas les remplacer par une affirmation de compatibilité.

Un rapport doit indiquer quels niveaux ont été effectués. Les packs ont des contrôles A–D. Le dernier pack Métano/Abyss possède désormais un test de désérialisation par le moteur réel ; **la partie graphique et interactive du niveau E reste non validée**.

## 21. Aperçu et exports

L’aperçu HTML utilise des images WebP sans perte embarquées, contrôlées contre les PNG. Il permet jour/nuit, calques, grille, zoom 1×, pause, phase zéro et exports PNG. Le zoom ne modifie pas l’export natif.

Les tests Node actuels simulent le DOM et contrôlent les interactions ; ils ne sont ni un vrai navigateur ni un test du moteur. Les planches réduites sont des documents de lecture, jamais des assets à importer.

## 22. Reproduction du pack Métano/Abyss antérieur

Dépendances de la chaîne images : Python, Pillow, NumPy. Outils auxiliaires : Git, GitHub CLI, Node pour les tests d’interaction. Ces outils ne remplacent pas PMDO.

```sh
.venv/bin/python source/cote_v4_abyss/prepare.py
.venv/bin/python source/cote_v4_abyss/build.py
.venv/bin/python source/cote_v4_abyss/make_project.py
.venv/bin/python source/cote_v4_abyss/package.py
node source/cote_dix_zones/test_viewer.cjs apercu_cotes_metano_abyss.html
```

Le package exécute son vérificateur avant archivage. Les sorties natives non compressées sont dans `~/.cache/cote_v4_abyss_pack/`. Les copies PNG régénérables sont ignorées par Git ; le ZIP et l’aperçu conservent les pixels finaux.

Ces commandes reproduisent **le pack Métano/Abyss antérieur**. Pour le mod Expéditions de 40 Ground, suivre les commandes de `source/cote_v5_expeditions/README.md`.

## 23. Erreurs connues et réponses correctes

| Symptôme | Mauvaise réponse | Réponse correcte |
|---|---|---|
| Roche générée non Métano | Affirmer que le prompt garantit la fidélité | Reconstruire depuis les sources natives |
| Import perçu minuscule | Agrandir tous les PNG | Vérifier taille des cellules, zoom et échelle des modules |
| Mur natif trop répétitif | Se contenter de zéro écart RGB | Revoir panneaux, retours et composition |
| Frange sombre sur un overlay | Repeindre au hasard | Vérifier alpha droit/prémultiplié et double mélange |
| Tileset manquant | Remplacer tout l’index | Fusionner l’index complet de destination |
| Nuit trop sombre | Ajouter encore un filtre | Vérifier qu’Abyss est appliqué une seule fois |
| Porte sans passage | Croire que le trou graphique suffit | Ajouter collisions, seuil et transition testée |
| Guide avec mauvais nombre de panneaux | Découper sans contrôle | Refaire une spécification explicite |
| ZIP moteur inaccessible | Dire que PMDO est installé | Documenter l’échec et obtenir l’archive par une voie disponible |
| Vérification Python réussie | Dire « testé en jeu » | Marquer le niveau réellement vérifié |

## 24. Provenance, attribution et archivage

Conserver les crédits Métano / Palika / Halcyon, ceux des références EoSO, ceux des variantes Abyss et des fonds Guilde/Sharpedo. Un dépôt public n’est pas une licence de réutilisation sans restrictions.

Les textures des trois entrées de référence sont archivées pour analyse, pas choisies comme matière des nouvelles cartes. Les téléchargements de moteur, bibliothèques et fichiers temporaires doivent rester hors du contenu versionné du projet.

Ne jamais effacer un ancien pack pour faire place à une correction. Marquer la livraison courante, conserver les rapports et décrire ce qui change réellement.


## 25. Livraison Métano Expéditions : sept falaises et trois entrées

Le fichier courant est **`mod_metano_expeditions_pmdo_0812.zip`**, projet `metano_expeditions`. Il réunit 20 nouveaux Ground `v50812_*` et les 20 Ground `v40812_*` du pack précédent, laissés identiques. Les archives modulaires plus anciennes ne sont pas incluses.

Les nouvelles silhouettes sont définies par `layouts.py` : contours Catmull-Rom rasterisés à la résolution native, plateaux superposés et découpes explicites des deux baies. Il s’agit d’une interprétation du guide, pas de l’extraction de ses panneaux mal numérotés. Le guide ne fournit aucun RGB final.

Les deux grottes utilisent un même encadrement Métano natif dans deux layouts différents ; le troisième accès est un corridor ouvert. Les palettes Crooked Cavern, Brine Cave et Drenched Bluff ne sont pas utilisées. Leurs ressources restent uniquement dans le dossier d’étude. Les accès sont sur un sixième calque de terrain indépendant.

Les nouvelles collisions bloquent les cellules partiellement hors herbe et les éléments d’accès. Une recherche de chemin vérifie un dégagement 16×16 depuis chaque arrivée jusqu’au seuil. Les accès entre terrasses secondaires et le comportement réel des collisions restent à contrôler dans le jeu.

**Les destinations des trois donjons restent non configurées.** Le mod fournit les marqueurs `donjon_seuil` et une fiche de raccordement, pas une téléportation vers un donjon inventé. Le projet est prêt à ouvrir pour éditer, pas présenté comme une aventure complète.

`runtime_test.py` a chargé les **40 Ground avec le vrai PMDO 0.8.12**, et vérifié dimensions, grille, nombre de calques et nombre de marqueurs. Le test est sans affichage, avec la constante de grille graphique initialisée explicitement. Aucun nouveau succès de rendu GPU ou de gameplay n’est revendiqué. Les lanceurs Windows/Linux servent à ouvrir le projet dans l’installation du joueur ; ils ne changent pas cette limite de validation.
