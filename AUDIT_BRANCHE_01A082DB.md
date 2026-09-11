# Audit et manuel de reprise — branche `arena/01a082db-guilde-treehouse-pmd`

**Audit réalisé le 11 septembre 2026 (Europe/Paris).**

- **Branche auditée :** `arena/01a082db-guilde-treehouse-pmd`
- **Révision auditée :** `bc3afc6676d62e1a5d811e129070ed3443162946`
- **Base commune :** `6c4ac5aad90da4f670d4965ec3d37a3ea38b5c78` (`main`, tag `pmd-passages-ouverts-v1`)
- **Méthode d'audit :** récupération Git de la branche distante, inspection des commits, manifestes, scripts, tailles de blobs, PNG de compositions et rapports ; extraction dans un répertoire isolé ; installation isolée des dépendances Python ; exécution du vérificateur statique de la branche auditée. Aucun fichier de la branche auditée n'a été modifié.

Ce document sépare les **faits vérifiés** des déclarations présentes dans la branche. Il explique la chaîne qui avait été livrée, ses limites et le protocole de reprise appliqué ici.

---

## 1. Résumé factuel

La branche auditée ajoute deux projets extérieurs complets, `falaise/` et `sharpedo/`, un aperçu commun, un rêve 3D indépendant, des scripts d'export/contrôle et de nombreux fichiers binaires. Son approche est bien une chaîne **native validée → calques PNG → composition → Aseprite/Tiled → aperçu HTML → vérifications**.

La scène `falaise` contient six ambiances et six calques ; `sharpedo` contient deux ambiances et sept calques. Les nuages, étoiles et, pour `sharpedo`, les vagues sont exportés comme animations. Les douze salles du kit historique ne sont pas modifiées graphiquement par ce commit ; le README racine est seulement préfixé pour les référencer.

**Constat déterminant pour les nouvelles références :** le gros commit de production `0ebe42c` a été créé **avant** les deux commits qui ajoutent les nouvelles images de référence. Il ne peut donc pas avoir utilisé ces ajouts comme entrées, même si les cinq fichiers se trouvent au sommet final de la branche. Les reprendre maintenant impose une nouvelle préparation, ce qui est précisément fait dans cette branche de travail.

---

## 2. Chronologie exacte et conséquence

| Heure Europe/Paris | Commit | Contenu réellement ajouté |
| --- | --- | --- |
| 11 sept. 2026, 12:36:40 | `0ebe42c` — *Finalise les exterieurs PMD et ajoute le reve 3D plein ecran avec previews GIF* | `falaise/`, `sharpedo/`, `reve/`, aperçus, contrôles, scripts et documentation. 236 chemins changés. |
| 11 sept. 2026, 12:41:27 | `6cf427c` — *référence à refaire pour notre PMD* | `232024.png` et `2cwdrrs469f61.gif`. |
| 11 sept. 2026, 12:44:30 | `bc3afc6` — *Add files via upload* | `anothercliff reference to made.jpg`, `made-a-set-of-customizable-pelipper-post-office-wallpapers-v0-lg3yjp20ve9d1.png`, `pondourpmdàrefaire.png`. |

Les heures des deux derniers commits sont déjà en `+0200`. Celle du premier est stockée en UTC dans Git, donc convertie en CEST dans ce tableau. `0ebe42c` précède les références de **4 min 47 s** puis **7 min 50 s**.

### Conséquence

Les sorties antérieures `falaise/compositions/*` et `sharpedo/compositions/*` ne sont **pas** une réponse traçable aux cinq nouveaux fichiers. Les prendre telles quelles, les renommer ou seulement les aplatir aurait masqué cette rupture de chronologie. La reprise correcte consiste à :

1. inventori­er et conserver les nouvelles entrées ;
2. préparer des natives qui en reprennent réellement les layouts ;
3. séparer ces natives en calques ;
4. produire et contrôler les exports associés.

---

## 3. Inventaire de la branche auditée

La révision finale contient **898 fichiers suivis**, pour **143 977 024 octets** (environ **137,31 MiB** Git ; environ 140 MiB après extraction). La base `main` compte 659 fichiers ; les trois commits ajoutent donc 239 fichiers nets, avec deux fichiers existants modifiés (`README.md`, `.gitignore`). Le diff agrégé liste 241 chemins modifiés : **162 binaires** et **79 textuels**, pour **24 759 lignes ajoutées** et aucune ligne supprimée.

Répartition après extraction :

| Extension | Nombre |
| --- | ---: |
| PNG | 742 |
| TMJ | 34 |
| Aseprite | 32 |
| JSON | 24 |
| Python | 22 |
| Markdown | 12 |
| HTML | 5 |
| JavaScript | 3 |
| GIF | 3 |
| JPEG/JPG | 4 |
| TSJ | 2 |
| CSS | 2 |
| WebP | 1 |

Les blobs les plus lourds sont l'aperçu du rêve (`apercu_reve.html`, 8,29 Mo), les GIF, les Aseprite animés de `falaise`/`sharpedo`, l'aperçu PMD préexistant et les atlas. Cette duplication est cohérente avec un aperçu hors ligne, mais rend cette livraison très volumineuse ; recopier l'intégralité dépasserait la cible de taille prudente d'un patch de travail.

### Les cinq nouvelles entrées

| Commit | Fichier | Format / dimensions observés | Lecture de travail |
| --- | --- | --- | --- |
| `6cf427c` | `232024.png` | PNG RGBA, 1193 × 451 | Planche en trois panneaux : îlot suspendu, cascades, horizon et végétation ; la moitié basse est une vue technique magenta. |
| `6cf427c` | `2cwdrrs469f61.gif` | GIF indexé, 504 × 504, 4 images | Prairie maritime fleurie ; les images montrent le même layout avec un mouvement d'eau. |
| `bc3afc6` | `pondourpmdàrefaire.png` | PNG indexé, 472 × 752 | Référence de bassin/cascades et planche de tiles/palettes, pas une composition prête à afficher. |
| `bc3afc6` | `anothercliff reference to made.jpg` | JPEG RGB, 3840 × 2400 | Layout côtier de jour : prairie, chemin, maison-courrier, falaise et mer. |
| `bc3afc6` | `made-a-set-of-customizable-pelipper-post-office-wallpapers-v0-lg3yjp20ve9d1.png` | PNG RGBA, 3840 × 2400 | Contrepartie nocturne du même layout côtier. |

Les noms de fichiers ne constituent pas une licence ni une provenance complète. Les sources sont donc conservées comme **références de travail** et leur usage est tracé dans `source/references_exterieures/provenance.json`; elles ne sont pas déclarées créations originales de ce dépôt.

---

## 4. Ce que faisait exactement le commit de production précédent

### 4.1 `falaise/` — Prairie de la guilde

Le manifeste annonce une scène de **480 × 408 px**, sur grille 8 px, avec six ambiances (`jour`, `nuit`, `crepuscule`, `aube`, `soir`, `orageux`) et une boucle de 480 images de 250 ms (120 s).

Les plans, du fond vers l'avant, sont :

1. ciel ;
2. astres ;
3. nuages ;
4. reliefs ;
5. falaise/prairie/chemin/escalier ;
6. végétation additionnelle vide.

`source/rebuild_falaise.py` charge les natives déjà préparées depuis `source/falaise/`, applique les palettes de variante puis appelle `export_variant()` de `source/exterior_animation.py`. Les nuages défilent avec une période de 480 pixels. Les étoiles nocturnes ont 24 phases, tandis que la lune est exclue de la variation. Le script produit PNG de calques, compositions, bases transparente/magenta, Aseprite animé, Tiled et `falaise/kit.json`.

Les documents de provenance indiquent une passe image générée pour la falaise complète et le rétablissement d'un rectangle d'escalier depuis une référence externe. Le code de reconstruction ne contacte toutefois aucun générateur : il réutilise `falaise_eos_generee.png`, `sommet_genere.png` et les autres bitmaps déjà commis. La génération artistique n'est donc pas reproductible depuis les seuls scripts, faute de modèle, paramètres, graines et historique de requêtes.

### 4.2 `sharpedo/` — Falaise côtière

Le manifeste annonce **504 × 384 px**, grille 8 px, deux ambiances (`jour`, `nuit`) et une boucle commune de 2 520 images (630 s). Ses sept plans sont :

1. ciel ;
2. astres ;
3. nuages ;
4. mer ;
5. vagues ;
6. falaise/prairie/chemin ;
7. décor additionnel vide.

`source/rebuild_sharpedo.py` charge les natives de `source/sharpedo/`, les ciels/nuages/astres partagés, puis exporte la mer en dix phases de 250 ms. `source/prepare_mer_reference.py` conserve l'atlas de ces phases ; `source/exterior_animation.py` l'écrit vers Aseprite et Tiled avec des cels liés et des objets-tuiles animés. Un tileset de vingt motifs de bordures est en plus généré pour la palette Tiled.

La documentation promet une paroi naturelle, sans forme de requin, et un chemin ouvert à droite/bas. Le contrôle protège des pixels de prairie/chemin et vérifie la présence d'une nouvelle paroi dans le masque prévu. Là encore, le script rejoue les assemblages à partir de fichiers binaires déjà présents ; il ne refait pas une génération d'image.

### 4.3 Exports communs et aperçu

`source/exterior_animation.py` porte la mécanique d'export :

- `AnimatedLayer` calcule un déplacement cyclique, une phase d'étoiles ou une frame d'atlas ;
- `write_ase()` écrit toutes les frames avec des cels liés après une période ;
- `write_tiled()` transforme les plans fixes en image layers et les plans animés en objets-tuiles ;
- `export_variant()` écrit les calques, la composition, la base, le magenta, Aseprite et Tiled.

`source/build_preview_falaise.py` encode les images en WebP data URI puis injecte CSS, JavaScript et données dans `apercu_falaise.html`. Le rendu est autonome et hors ligne ; l'interface permet notamment de masquer les calques, changer d'ambiance et parcourir les frames. `apercu_reve.html` et `reve/` forment un sous-projet distinct (questionnaire 3D Three.js), sans relation technique avec les nouveaux layouts extérieurs.

---

## 5. Contrôles réellement exécutés pendant cet audit

L'audit a été exécuté dans une archive isolée de la révision `bc3afc6`, avec Python 3.11.2, Pillow 12.3.0, NumPy 2.4.6 et OpenCV 5.0.0. La commande suivante a réussi sans modification du checkout audité :

```bash
python source/verify_falaise.py
```

Résultat observé :

```text
PASS falaise jour — 480 frames ; PNG/Aseprite/Tiled identiques
PASS falaise nuit — 480 frames ; PNG/Aseprite/Tiled identiques
PASS falaise crepuscule — 480 frames ; PNG/Aseprite/Tiled identiques
PASS falaise aube — 480 frames ; PNG/Aseprite/Tiled identiques
PASS falaise soir — 480 frames ; PNG/Aseprite/Tiled identiques
PASS falaise orageux — 480 frames ; PNG/Aseprite/Tiled identiques
PASS sharpedo jour — 2520 frames ; PNG/Aseprite/Tiled identiques
PASS sharpedo nuit — 2520 frames ; PNG/Aseprite/Tiled identiques
```

Cela valide la structure de **2 880** frames de `falaise` et **5 040** frames de `sharpedo` dans les formats déclarés. Précision importante : le vérificateur lit tous les cels Aseprite et toutes les phases d'atlas Tiled, mais la recomposition complète est comparée sur neuf positions représentatives par ambiance (`0`, `1`, `6`, `12`, `23`, `24`, milieu, avant-dernière, dernière), et non sur les 7 920 instants possibles d'une composition finale.

Le vérificateur du kit existant de `main` a aussi été relancé dans cet environnement et réussit :

```text
PASS: 12 salles, 24 Aseprite fixes, 11 calques, 6 vues, fenêtres transparentes, magenta exact, Tiled identique.
```

Les quatre compositions jour/nuit de l'ancienne branche ont été inspectées visuellement dans cet audit. Les rapports navigateur déjà commis annoncent 54 comparaisons pour `falaise` (erreur maximale prémultipliée 1,1647) et 18 pour `sharpedo` (maximum 2,0), hors ligne et sans erreurs JavaScript. **Ils ne sont pas comptés comme une réexécution indépendante ici** : Playwright et un Chromium exécutable ne sont pas fournis dans l'environnement d'audit. Le script navigateur est présent et a été lu, mais il n'a pas été lancé.

---

## 6. Risques et limites relevés

1. **Décalage des références.** C'est le point bloquant majeur : les images ajoutées après `0ebe42c` n'ont pas servi à son rendu.
2. **Étape générative non reproductible.** Les images retenues et quelques prompts sont conservés, mais pas le modèle, les réglages, les graines, les essais rejetés ou la conversation qui a conduit aux assets.
3. **Dépendances non verrouillées.** `source/requirements.txt` liste les paquets sans versions ; Playwright est seulement commenté. Une reconstruction dans un autre environnement peut différer ou échouer.
4. **Validation sémantique limitée.** Les contrôles sont solides sur les octets/frames/recompositions, mais ne jugent pas automatiquement l'intérêt artistique, l'absence de tout motif involontaire ou la cohérence de gameplay.
5. **Licences et traçabilité.** Les sources de la branche évoquent des régions de référence EoS réutilisées. Les nouvelles images ajoutées n'ont pas de métadonnées de licence dans le commit. Elles doivent rester attribuées/validées selon leur provenance avant une redistribution comme assets de jeu.
6. **Volume.** Aseprite, atlas, HTML autonomes et GIF dédoublent les pixels. Ils sont appropriés pour une livraison éditable, mais pas pour une petite référence graphique. Il faut définir dès le départ si l'objectif est une image, un kit modulaire ou les deux.
7. **Collisions non fournies.** Les cartes Tiled de la branche auditée n'intègrent pas les transitions/collisions moteur ; les rectangles sont des repères de production.

---

## 7. Protocole de reprise adopté sur cette branche

La correction de consigne demande maintenant de conserver **les layouts des nouvelles références et une structure à plusieurs calques**, à la manière du précédent agent. La livraison ajoutée ici suit donc le protocole ci-dessous.

### A. Références et natives

- Les cinq nouvelles entrées ont été placées sous `source/references_exterieures/entrees/` ; leurs empreintes SHA-256 sont régénérées dans `source/references_exterieures/provenance.json`.
- Un panneau propre de `232024.png` est sélectionné, sans séparateur noir ni bande magenta technique. Il est redimensionné au plus proche voisin vers **592 × 448 px**.
- L'image 0 du GIF de prairie maritime est conservée au format source **504 × 504 px** ; ce layout devient la troisième scène. Les quatre phases restent en planche de référence afin de tracer le mouvement observé, sans l'inventer ni l'appliquer à une scène non demandée.
- Les deux grandes références côtières jour/nuit sont réduites par le facteur entier quatre vers **960 × 600 px**, sans recadrage ni interpolation. Elles gardent donc le layout fourni : prairie, maison-courrier, falaise et mer.
- Les variantes nocturnes de cascades et de prairie maritime gardent strictement leurs géométries de jour. Une transformation chromatique fixe et de petites étoiles limitées à l'atmosphère constituent ces variantes ; aucun terrain n'est déplacé.

### B. Calques produits

`references_exterieures/cascades/`, `references_exterieures/prairie_maritime/` et `references_exterieures/cap_cotier/` contiennent chacun, pour jour et nuit :

- cinq PNG RGBA dans `calques/<ambiance>/` ;
- une composition complète dans `compositions/` ;
- une base transparente et une base magenta dans `bases/` ;
- un Aseprite statique à une image et cinq vrais calques ;
- une carte Tiled à cinq `image layers` sur une grille de 8 px.

Le séparateur attribue chaque pixel opaque d'une native à **un seul plan**. Il n'y a ni trou ni recouvrement. Le fond reçoit les pixels non spécialisés ; l'atmosphère, le relief, l'eau/cascade, la maison et la végétation reçoivent ensuite leurs zones sémantiques. Cette propriété est plus importante qu'une simple liste de PNG : elle garantit que masquer un calque dans l'aperçu est significatif et que la recomposition ne modifie pas l'image de référence.

### C. Contrat et contrôle

Les scripts de cette branche sont :

```bash
python source/prepare_references_exterieures.py
python source/rebuild_references_exterieures.py
python source/verify_references_exterieures.py
```

Le premier prépare les natives et enregistre les entrées. Le second répartitionne les pixels, produit tous les exports et construit `apercu_references_exterieures.html` avec les plans encodés localement. Le dernier relit les PNG, vérifie la partition, recompose les images, relit chaque cel Aseprite, valide les liens Tiled, les bases transparente/magenta, les différences jour/nuit et l'absence de requête réseau dans l'aperçu.

Aucun appel à un service réseau, aucun générateur en ligne et aucune animation ne sont nécessaires pour rejouer l'export des fichiers versionnés. Comme pour le kit historique, une inspection artistique humaine reste complémentaire.

---

## 8. Règles à conserver pour les suites

1. Toujours lire les commits dans l'ordre temporel avant d'associer une sortie à une référence.
2. Conserver l'image complète native en source, puis produire les plans et tous les formats depuis elle. Ne jamais ne modifier qu'une composition livrée.
3. Pour une ambiance nuit, conserver la géométrie de la variante jour, sauf demande explicite de layout différent ; isoler astres/nuages du terrain dans un plan dédié.
4. Employer une grille 8 px lorsque les cartes Aseprite/Tiled sont demandées, sans transformer le rendu en gros carrés de 8 px.
5. Vérifier les plans par une partition/une recomposition pixel à pixel avant de déclarer qu'ils sont indépendants.
6. Distinguer clairement références de travail, sources externes, natives préparées et exports de jeu ; garder les informations de provenance avec les assets.
7. Ne pas prétendre qu'un test de format valide une décision artistique ou une licence.
8. Limiter les gros binaires aux formats explicitement demandés. Pour une simple référence, les PNG peuvent suffire ; pour une intégration modulaire, garder en plus Aseprite/Tiled et les scripts de contrôle.

---

## 9. État de cette livraison

- Les trois layouts nouvellement ajoutés sont produits dans `references_exterieures/` en **jour et nuit, cinq plans par ambiance**.
- Les références récentes sont réellement utilisées dans la préparation ; elles ne sont pas confondues avec le rendu antérieur à leurs commits.
- La chaîne préparateur → export → vérificateur a été exécutée avec succès après la modification de consigne vers une livraison multicouche.
- L'aperçu `apercu_references_exterieures.html` est autonome et permet de masquer chaque plan.

Ce manuel doit être lu avec `references_exterieures/README.md`, qui décrit le contrat de fichiers de la nouvelle livraison.
