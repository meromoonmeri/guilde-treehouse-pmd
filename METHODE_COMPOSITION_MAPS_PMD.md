# Méthode de composition des maps PMD

**Document de travail pour les prochaines maps — synthèse des README du dépôt**  
**Périmètre :** composition visuelle PMD/PMDO, couches éditables, références canoniques et contrôles.  
**Règle directrice :** une map est une composition construite à partir d'une référence analysée et de plusieurs passes de matière ; ce n'est ni une image aplatie, ni une mosaïque de tuiles choisies au hasard.

## 1. Ce que les README établissent

La documentation du dépôt décrit trois cas qui doivent rester distincts :

### A. Extension d'une matière canonique, notamment Métano

C'est le mode à employer lorsqu'une map doit réellement prolonger une zone ou un tileset canonique existant.

- Le générateur peut proposer la **silhouette, le rythme des masses et la composition**.
- Il ne fournit pas les pixels finaux et ne devient jamais une preuve de texture canonique.
- Le terrain final est reconstruit avec les feuilles natives vérifiées : modules complets de sommet, face, retour, couronne et pied ; herbe, berges, eau et animations provenant de leurs sources documentées.
- Les pixels natifs ne sont ni recolorés, ni tournés, ni retournés, ni agrandis, ni interpolés. Une découpe par alpha ou une répétition de rangées est une adaptation documentée, pas une nouvelle peinture.
- Les compositions approuvées et les anciens packs sont conservés byte à byte ; une nouvelle version reçoit de nouveaux identifiants.

Références de méthode : `AGENTS.md`, `MANUEL_METHODE_PMDO.md`, `sprites/zones_guidees/README.md`, `sprites/zones_guidees/README_multicalques.md`, `sprites/metano_pixel_perfect/README.md`, `sprites/metano_import_png/README.md`.

### B. Partition fidèle d'une zone déjà validée

C'est le mode à employer lorsqu'un rendu du dossier `renders/` est la référence de continuité.

- Le layout validé est verrouillé : pas de régénération, de déplacement, de recadrage ou de remplacement de texture sans demande explicite.
- Les PNG sont séparés en couches de surfaces visibles, tous alignés sur le même canevas et recomposés pour retrouver exactement le rendu de référence.
- Les parties cachées sous un arbre, un rocher ou une falaise ne sont pas prétendues reconstruites. Un calque extrait d'une scène n'est pas automatiquement un sprite librement déplaçable.
- Une nouvelle map peut réutiliser une logique de profondeur, un module isolé ou un cycle documenté, mais elle ne doit pas repeindre une zone validée ni lui attribuer une nouvelle géométrie.

Références : `renders/references_fideles_v1/README.md`, `renders/references_54d3731/README.md`, `renders/entrees_six_donjons_v1/sakura_validee/README.md`, `sprites/zones_guidees/README_multicalques.md`.

### C. Nouvelle entrée ou nouvelle map PMD rendue

Ce mode autorise une matière générée inspirée de PMD lorsque la demande porte sur une nouvelle entrée indépendante et non sur une extension Métano pixel-native.

- Les références canoniques PMD fixent la structure, la caméra, l'échelle relative, le langage des formes, la densité et la palette visuelle.
- La scène est générée **en une composition complète cohérente**, souvent sur fond magenta, puis détourée et découpée en couches. On ne colle pas des morceaux d'anciennes maps pour fabriquer le terrain.
- Les couches et les masques restent séparés ; le résultat généré n'est pas présenté comme une texture native récupérée.
- Les animations nouvelles sont identifiées comme des propositions. Un cycle effectivement extrait d'une source canonique est distingué d'une animation générée ou adaptée.

Références : `source/layouts_magenta_v1/WORKFLOW.md`, `renders/arene_glace_generee_v2/README.md`, `renders/arene_halcyon_v15/README.md`, `renders/entrees_pmd_collection/README.md`.

**Pour la présente demande, le mode cible sera annoncé avant chaque map.** Quand « textures canoniques » est exigé, le mode A prime : la génération sert au layout, pas aux pixels finaux. Quand une entrée indépendante est demandée, le mode C peut fournir une matière PMD générée, mais sa provenance et ses limites seront écrites sans ambiguïté.

---

## 2. Le dossier obligatoire avant toute map

Chaque map nouvelle doit avoir une fiche de composition, versionnée avec ses sources. Elle répond explicitement aux sept points demandés.

### 2.1 Références canoniques utilisées

La fiche doit donner :

1. le jeu, la zone ou le Ground de référence ;
2. le dépôt, le commit ou le fichier source précis ;
3. les références de layout, de matière et d'animation séparément ;
4. les dimensions de la carte, la grille et le `TexSize` ;
5. les coordonnées des prélèvements quand des textures natives sont employées ;
6. le hash du fichier source et, si possible, le hash de blob Git/SHA-256 local ;
7. les crédits et la portée de la licence.

Une capture ou un nom de feuille ne suffit pas : une feuille peut contenir plusieurs modules et plusieurs phases. Pour une carte native, lire le `.rsground`, toutes les feuilles `Sheet` de ses frames, les objets, marqueurs, collisions, scripts et fonds pertinents. Pour une référence aplatie, noter honnêtement ce qui est visible et ce qui est caché.

### 2.2 Analyse de la structure générale

Avant de dessiner, produire une analyse annotée de la référence :

- silhouette globale et limites de la zone ;
- axe de lecture et direction du parcours ;
- point d'arrivée, destination ou entrée ;
- plateaux, terrasses, pentes, falaises, retours, couronnes et pieds ;
- sol praticable, chemin, zones de rupture et bords qui continuent hors cadre ;
- mer, rivière, cascade, bassin ou autre surface animée ;
- plans arrière, masses latérales, premier plan et occlusions ;
- végétation, rochers, structures et éléments décoratifs ;
- niveaux de profondeur et éventuels niveaux d'élévation ;
- ombres de contact, ombres de relief, éclairage et zones de contraste ;
- largeur de passage et échelle par rapport au personnage.

L'analyse doit distinguer la **géométrie** (masques et cheminement) de la **matière** (pixels, palette, modules) et de la **mise en scène** (ombres, avant-plan, ciel et effets).

### 2.3 Plan des textures et des layers

La fiche indique pour chaque calque : son nom, sa fonction, son origine, son alpha, son ordre, son animation éventuelle et ce qu'il est interdit d'y mettre. Une carte PMD complète ne se limite pas à un calque `terrain.png`.

Pile de référence adaptable :

| Ordre | Calque | Fonction |
|---:|---|---|
| 00 | `bg_ciel` | ciel opaque ou fond de scène ; indépendant du terrain |
| 01 | `bg_astres_nuages` | astres, brume lointaine et nuages ; wrap seulement si documenté |
| 02 | `terrain_sol_base` | base opaque du sol praticable |
| 03 | `terrain_variations` | différences de sol, herbe, terre, neige, sable ou roche plane |
| 04 | `relief_arriere` | masses éloignées et volume de fond |
| 05 | `falaises_faces` | faces verticales et grandes matières de relief |
| 06 | `falaises_retours` | retours latéraux, couronnes, rebords et pieds |
| 07 | `transitions_berges` | raccords sol/eau, sol/roche, neige/glace ou matière/matière |
| 08 | `eau_fond` | bassin ou rivière derrière les éléments fixes |
| 09 | `eau_surface_phase_XX` | surface animée, écume, cascade ou reflets, par phase |
| 10 | `chemins_passages` | chemin, seuil, rampes et zones de circulation lisibles |
| 11 | `vegetation_basse` | herbes, fleurs, mousses et petits détails au niveau du sol |
| 12 | `vegetation_masses` | arbres, buissons, racines ou grands éléments arrière |
| 13 | `decor_objets` | éléments décoratifs explicitement demandés |
| 14 | `ombres_contact` | ombres locales liées aux formes et à leurs positions |
| 15 | `entree_profondeur` | bouche, vide, intérieur ou profondeur d'un passage |
| 16 | `premier_plan` | éléments devant le personnage ; couche `Top` dédiée si PMDO |
| 17 | `eclairage_effets` | lumière, poussière, aurore ou effets indépendants |

Ce tableau est un rôle de composition, pas un nombre fixe de couches. On supprime les couches réellement inutiles, mais on ne fusionne pas deux fonctions différentes pour aller plus vite. À l'inverse, une map qui nécessite plusieurs profondeurs de végétation ou plusieurs phases d'eau les sépare explicitement.

### 2.4 Composition et superposition

L'ordre de composition est décidé avant l'export :

1. stabiliser le canevas, la grille et l'orientation ;
2. poser le ciel/fond ;
3. poser le sol et les masses arrière ;
4. construire les reliefs par modules cohérents, du fond vers le premier plan ;
5. raccorder les transitions et les berges ;
6. réserver et dessiner le chemin, le seuil et les zones de retour ;
7. ajouter l'eau sur ses calques et vérifier chaque phase ;
8. ajouter végétation et décor avec leurs ombres de contact liées ;
9. poser l'entrée ou la profondeur du passage ;
10. ajouter les éléments de premier plan et effets au-dessus du personnage seulement lorsque c'est nécessaire ;
11. recomposer la scène et comparer à la référence à 1×.

La composition doit produire une lecture PMD : grandes masses organiques, plateaux lisibles, silhouettes irrégulières mais maîtrisées, profondeur par recouvrement et ombres courtes. Les murs rectilignes, les plateformes indépendantes, les contours noirs ajoutés et le bruit décoratif uniforme sont des régressions, même si toutes les tuiles sont authentiques.

---

## 3. Pipeline de production, sans raccourci

### Étape 0 — Gel des références validées

Avant une nouvelle map, consulter la dernière version du rendu concerné et son README. Ne pas modifier les PNG, ORA, cartes ou packs validés. Créer un nouveau dossier et des noms uniques pour la map en cours. La fiche doit préciser quels éléments sont **réutilisés**, lesquels sont seulement **étudiés**, et lesquels sont **nouveaux**.

Le dossier `renders/` est un corpus de référence visuelle. Les dernières versions de chaque zone y sont prioritaires ; les anciennes versions servent uniquement à comprendre l'historique et ne doivent pas être réintroduites par erreur.

### Étape 1 — Collecte et audit des sources

- retrouver le fichier original et son commit exact ;
- décoder les ressources natives plutôt que prendre une capture ;
- relever dimensions, grille, frames, alpha, index, objets et limites ;
- calculer les empreintes et écrire `provenance.json` ;
- conserver les bruts hors de la composition finale ;
- vérifier qu'une ressource nommée `Cloud`, `Background` ou `Objects` a réellement le rôle supposé.

Pour les cartes PMDO, les coordonnées sont orientées `Tiles[x][y]`. Les formats `.tile`, `.dir` et `index.idx` doivent être reconstruits ou fusionnés avec les règles du manuel ; un PNG renommé n'est pas une ressource native.

### Étape 2 — Analyse et plan de map

Écrire la fiche avant toute génération. Elle doit contenir un schéma simple de la silhouette, les bords connectés, les terrasses, l'axe du chemin, l'arrivée, le seuil, les zones d'occlusion et la réserve de futurs objets. Le layout est validé indépendamment de la texture.

Pour une entrée, préciser notamment :

- si le passage est une bouche sombre ou un corridor ouvert ;
- largeur du seuil et espace de présentation devant l'entrée ;
- direction d'arrivée et zone de retour ;
- dégagement du collider et collisions de la paroi ;
- présence d'un marqueur sans confondre marqueur et téléportation.

### Étape 3 — Guide de composition

Si le mode A ou C le justifie, demander au générateur une **composition complète**, avec :

- références canoniques affichées et nommées ;
- caméra, résolution et rapport d'échelle fixés ;
- biome, axe et niveaux de profondeur écrits ;
- absence de bâtiments, personnages, objets ou effets non demandés ;
- fond magenta si un détourage est nécessaire ;
- sol complet sous les reliefs pour éviter les trous ;
- une scène entière, pas une planche de morceaux à assembler.

Conserver la sortie brute, son prompt et ses limites. Le guide choisit la répartition des masses ; il ne certifie ni la palette native, ni les raccords, ni les collisions.

### Étape 4 — Masques et séparation des responsabilités

Créer au minimum les masques suivants :

- occupation du terrain ;
- sol praticable ;
- roche/relief ;
- eau et berge ;
- végétation arrière et premier plan ;
- entrée, vide et seuil ;
- ombre et éclairage ;
- zones interdites ou réservées.

Le masque définit une géométrie, pas une couleur. Dans une composition générée, retirer le magenta par inondation depuis le bord lorsque cela évite de supprimer une couleur légitime au centre ; documenter les franges, l'alpha binaire et les éventuelles zones cachées. Une bouche de grotte ne doit jamais être rebouchée par la plaque de sol.

### Étape 5 — Reconstruction de la matière

#### Si la map doit être canonique/pixel-native

- prélever les modules complets depuis les feuilles vérifiées ;
- préférer un panneau complet de sommet/face/pied/retour à des fragments isolés de 8 px ;
- conserver les pixels et l'alpha natifs ;
- utiliser les répétitions uniquement pour prolonger une matière cohérente et les noter dans la fiche ;
- utiliser les coordonnées source pour chaque famille de modules ;
- faire valider un témoin à taille native avant de multiplier les cartes ;
- traiter les fonds, eau et animations comme des ressources séparées.

#### Si la map est une nouvelle entrée générée dans la DA PMD

- générer le terrain entier avec les références canoniques comme guide ;
- détourer au magenta, sans frange rose ;
- faire une passe de sol complet sous les volumes ;
- séparer sol, reliefs, transitions, végétation, ombres, profondeur et premier plan ;
- ne pas appeler les pixels générés « canoniques » ;
- réutiliser seulement des cycles ou sprites dont la provenance et le statut sont explicitement documentés.

Dans les deux cas, le résultat doit rester une composition riche. « Authentique » signifie ici respecter la construction visuelle PMD, pas appliquer une texture unique à toute la toile.

### Étape 6 — Eau, végétation et animation

L'eau est une matière composée, pas un aplat bleu : fond, berges, surface, écume, cascades, reflets et ombres ont des rôles distincts. Quand un cycle canonique existe, conserver ses phases, son timing et ses pixels. Quand le mouvement est créé ou adapté, l'indiquer comme tel, fournir chaque phase en PNG et vérifier la fermeture de boucle.

La végétation suit la profondeur : massif arrière, troncs/canopées, végétation basse, éléments de bord et avant-plan. Les ombres restent liées à la silhouette et au sol de la scène ; une ombre extraite n'est pas un filtre noir universel. Les parties cachées ne deviennent pas magiquement des sprites complets.

### Étape 7 — Export éditable

Pour chaque map, livrer autant que pertinent :

- PNG RGBA de chaque couche, mêmes dimensions et origine `(0,0)` ;
- un rendu recomposé de contrôle ;
- une version sèche si l'eau/les effets sont optionnels ;
- les phases séparées des couches animées et leur manifeste de durée ;
- un document ORA/OpenRaster ou équivalent éditable ;
- les masques, la provenance et la recette de placement ;
- une galerie avec visibilité couche par couche, zoom 1×, pause et export ;
- une fiche d'intégration et les crédits.

Pour un import PNG to Tileset, garder des dimensions compatibles avec la grille de 8 px, `TexSize = 1`, des pixels nets et des noms de base uniques. Ne pas prendre une planche réduite, un GIF, un WebP ou une image avec ciel intégré comme tileset final.

Pour un vrai mod PMDO, produire un projet séparé ou utiliser l'installateur de fusion : `Mod.xml`, `Data/Ground`, `Content/Tile`, `Content/BG`, scripts namespace, index complet et identifiants uniques. Ne jamais écraser l'index d'un projet existant avec un index partiel.

### Étape 8 — Contrôles en cinq niveaux

| Niveau | Contrôle | Preuve attendue |
|---|---|---|
| A | Provenance | commits, chemins, hashes, coordonnées, crédits |
| B | Image | dimensions, grille, alpha, masques, raccords, palette/matière |
| C | Composition | ordre des couches, recomposition, phases, ORA, absence de trous |
| D | Formats/import | `.tile`/`.dir`/index ou PNG to Tileset, fusion, noms uniques |
| E | Moteur | PMDO ouvert, rendu, animation, collisions, transitions, sauvegarde |

Un test Pillow, NumPy, DOM ou une désérialisation sans affichage ne vaut pas un test graphique ou jouable. Le rapport doit dire précisément quels niveaux sont passés. Ne jamais annoncer « testé en jeu » pour un contrôle de fichiers.

---

## 4. Matrice de décision pour les textures

| Besoin | Source à employer | Ce qui est autorisé | Ce qui est interdit |
|---|---|---|---|
| Extension Métano | feuilles natives et modules documentés | sélection, découpe alpha documentée, répétition cohérente | générer une roche finale, recolorer le jour, miroir, rotation, resampling |
| Layout d'une nouvelle falaise Métano | guide généré + matière native | utiliser le guide pour choisir les silhouettes et modules | importer les pixels du guide comme tuiles finales |
| Entrée PMD indépendante | références PMD + génération complète guidée | matière inventée cohérente, calques, palette contrôlée | prétendre que le résultat est extrait/canonique, aplatir sans calques |
| Zone validée à exporter | rendu approuvé existant | partition exacte, calques alignés, ORA | redessiner la géométrie, déplacer l'accès, remplir silencieusement les parties cachées |
| Eau canonique disponible | frames et feuille source vérifiées | réutiliser phases, alpha et timing | recolorer ou inventer un cycle en le nommant natif |
| Effet animé absent des sources | référence visuelle + animation proposée | créer plusieurs frames et documenter le choix | appeler le mouvement officiel sans preuve |

---

## 5. Checklist de revue d'une map

### Avant construction

- [ ] La référence canonique et son statut sont écrits.
- [ ] Le dernier rendu validé à ne pas modifier est identifié.
- [ ] Le mode A, B ou C est choisi.
- [ ] La grille, l'échelle et les dimensions sont fixées.
- [ ] L'analyse structurelle couvre relief, chemins, eau, végétation, ombres et profondeur.
- [ ] Le schéma de layout indique arrivées, sorties, seuils et zones réservées.
- [ ] Les layers et leur ordre sont listés.
- [ ] Les textures réutilisées, adaptées et nouvellement créées sont distinguées.

### Pendant la construction

- [ ] Le sol, les reliefs, les transitions, l'eau et les détails ne sont pas fusionnés par défaut.
- [ ] Le guide généré ne remplace pas les textures natives lorsqu'elles sont exigées.
- [ ] Les modules sont posés à leur échelle ; aucune interpolation n'est utilisée.
- [ ] Les raccords sont vérifiés à 1× et non seulement sur une planche réduite.
- [ ] Les ombres restent liées à leur forme et à leur sol.
- [ ] Les chemins restent lisibles et libres des masses de premier plan.
- [ ] Chaque animation a ses phases, sa durée et son statut de provenance.
- [ ] Le ciel, les nuages, les astres et les fonds sont indépendants du terrain.

### Avant livraison

- [ ] Chaque PNG de calque a le même canevas et la même origine.
- [ ] La recomposition correspond au rendu de contrôle.
- [ ] Les masques ne créent ni roche dans le ciel, ni eau dans un chemin, ni entrée bouchée.
- [ ] Les zones de connexion sont pleines et à la bonne échelle.
- [ ] Les noms de ressources sont uniques et l'index complet est préservé.
- [ ] Le README de la map contient références, ordre des layers, provenance, crédits et limites.
- [ ] Les tests A–E sont reportés séparément ; aucune validation moteur n'est implicitement inventée.
- [ ] Les rendus et packs validés précédents sont inchangés.

---

## 6. Fiche à copier pour chaque nouvelle map

```markdown
# [ID] — [nom de la map]

## Statut et mode
- Mode : A canonique / B partition fidèle / C nouvelle entrée générée
- Version : v1
- Référence validée à préserver :
- Rendu cible / galerie :

## 1. Références canoniques
- Layout :
- Matière :
- Eau / animation :
- Source, commit, hash, crédits :

## 2. Analyse de structure
- Dimensions / grille / TexSize :
- Direction du parcours et arrivée :
- Terrasses / falaises / bords connectés :
- Sols / chemins / eau :
- Végétation / décor / ombres :
- Niveaux de profondeur et occlusions :

## 3. Layers nécessaires
| Ordre | Nom | Fonction | Source | Statique/animé |
|---:|---|---|---|---|
| 00 | | | | |

## 4. Composition
- Ordre de superposition :
- Transitions :
- Placement de l'eau et des effets :
- Éléments devant le personnage :

## 5. Réutilisation des zones validées
- Éléments repris tels quels :
- Éléments repris comme référence seulement :
- Éléments protégés contre toute modification :

## 6. Créations/adaptations
- Nouveau layout :
- Modules ou textures adaptés :
- Animations nouvelles/adaptées et statut :
- Masques / surfaces cachées complétées :

## 7. Cohérence et contrôles
- Palette / échelle / densité comparées à :
- Test de recomposition :
- Tests A–E :
- Limites restantes :
```

Cette fiche est une condition de départ, pas une note ajoutée après coup. Elle permettra de comparer chaque nouvelle map aux zones déjà validées sans les redessiner.

## 7. Conclusion opérationnelle

La méthode retenue pour la suite est donc :

**référence canonique précise → analyse structurelle → fiche de layers → guide de composition complet si nécessaire → masques → reconstruction multi-passes de la matière → transitions et ombres liées → animation séparée → recomposition/aperçu → contrôles de provenance, image, format et moteur.**

La priorité n'est pas de produire rapidement une image plausible. La priorité est de pouvoir montrer, pour chaque map, **quelle référence a décidé chaque forme, quelle texture remplit chaque couche, comment les couches se superposent, ce qui est réutilisé, ce qui est nouveau, et quel niveau de validation est réellement atteint**.
