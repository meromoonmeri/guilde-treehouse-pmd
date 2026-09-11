# Audit et manuel de reprise — branche `arena/01a082db-guilde-treehouse-pmd`

**Audit réalisé le 11 septembre 2026 (Europe/Paris).**

- **Branche auditée :** `arena/01a082db-guilde-treehouse-pmd`
- **Révision auditée :** `bc3afc6676d62e1a5d811e129070ed3443162946`
- **Base commune :** `6c4ac5aad90da4f670d4965ec3d37a3ea38b5c78` (`main`, tag `pmd-passages-ouverts-v1`)
- **Méthode d'audit :** récupération Git de la branche distante, inspection des commits, manifestes, scripts, tailles de blobs, PNG de compositions et rapports ; extraction dans un répertoire isolé ; installation isolée des dépendances Python ; exécution du vérificateur de formats de la branche auditée. Aucun fichier de la branche auditée n'a été modifié.

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

## 7. Protocole de reprise effectivement adopté sur cette branche

La correction de consigne demande désormais les **layouts des nouvelles références**, une image créée par générateur puis les **plans animés** de l’implémentation extérieure auditée. Il ne s’agit donc ni de livrer une découpe directe des fichiers fournis, ni de se limiter au format Aseprite fixe du kit de salles de `main`.

### A. Origine, génération et natives

- Les cinq entrées des commits récents sont conservées dans `source/references_exterieures/entrees/`. Elles sont des guides de composition, de lisibilité et de palette ; leurs SHA-256 restent consignés dans `provenance.json`.
- Six rendus complets ont été créés avec le générateur d’images de cette livraison : `cascades`, `prairie_maritime` et `cap_cotier`, chacun en jour/nuit. Ils sont les layouts initiaux dans `source/references_exterieures/generation/`. Six autres appels au générateur produisent explicitement les backplates `00_ciel`, un par scène/ambiance, dans `source/references_exterieures/generator_planes/`. Aucun crop, collage ni filtre de l’image de référence n’est la native finale.
- `cascades` est une composition verticale volontaire : les rendus de génération font 816 × 1 300 px et sont normalisés au plus proche voisin vers **408 × 648 px**. Les deux scènes panoramiques font 1 376 × 768 px et sont normalisées vers **688 × 384 px**.
- Chaque nuit a été créée en prenant le rendu jour correspondant comme contrainte de géométrie ; elle n’est pas une simple teinte appliquée après coup. La préparation qui est versionnée ne recontacte aucun générateur : elle valide les six sources présentes, les redimensionne et écrit la provenance reproductible de cette normalisation.

Cela garde une frontière honnête : l’export est rejouable depuis les six rasters versionnés, mais la génération artistique elle-même dépend de l’outil et de la séance de génération, comme c’était le cas des assets déjà commis de la branche auditée.

### B. Architecture animée reprise et adaptée

`source/exterior_reference_animation.py` est la mécanique relue dans `source/exterior_animation.py` de la branche auditée, adaptée seulement pour accepter le nom d’asset de chaque scène. Comme `rebuild_sharpedo.py`, le reconstructeur lit un pack de PNG sources préalablement préparé, `source/references_exterieures/plans/`, et ne repartitionne pas une composition à l’export. Elle apporte :

- `AnimatedLayer`, qui rend une phase de plan fixe, défilant ou scintillant ;
- la carte de groupes et la LUT de 24 phases pour les étoiles ; le plus grand groupe, la lune, est forcé à l’opacité 100 % ;
- un compositeur unique utilisé à la fois pour l’image 0, les cels Aseprite et les atlas Tiled ;
- `write_ase()`, qui déclare les calques une seule fois, crée le tag de boucle, écrit les cels réelles sur une période et des cels liées pour les répétitions ;
- `write_tiled()`, qui exporte les plans fixes en `imagelayer` et les opérations animées sous forme d’objet-tile pointant vers un atlas ;
- `export_variant()`, qui écrit les PNG image 0, compositions, bases, magenta, Aseprite, Tiled et métadonnées d’opérations.

Le précédent `falaise` emploie 480 phases afin de parcourir ses 480 px de nuages. Pour les nouveaux layouts, la boucle commune est volontairement plus courte : **24 phases × 250 ms = 6 000 ms**, avec un décalage horizontal de 1 px par phase. C’est un choix documenté, contrôlé et compatible avec la période de scintillement déjà employée ; ce n’est pas une revendication que la nouvelle composition aurait une boucle de 480 px.

### C. Plans produits et conservation de l’image 0

Les plans, dans l’ordre de composition, sont :

| Scène | Plans |
| --- | --- |
| `cascades` | `00_ciel`, `01_astres`, `02_nuages`, `03_eau_cascades`, `04_cascades_ecume`, `05_ilot_rocheux`, `06_vegetation` |
| `prairie_maritime` | `00_ciel`, `01_astres`, `02_nuages`, `03_mer_reflets`, `04_vagues_reflets`, `05_falaises`, `06_prairie_chemin`, `07_fleurs_vegetation` |
| `cap_cotier` | `00_ciel`, `01_astres`, `02_nuages`, `03_mer_reflets`, `04_vagues_reflets`, `05_falaise_terrain`, `06_maison`, `07_vegetation` |

L’eau, le relief, le terrain/la maison et la végétation sont des plans séparés et éditables. Dès `prepare_references_exterieures.py`, chacun est écrit dans `source/references_exterieures/plans/<scene>/<ambiance>/` : c’est le pack de « natives de calques » analogue à `source/sharpedo/mer_native.png`, `vagues_native.png` et `falaise_native.png`. `rebuild_references_exterieures.py` les charge ensuite nommément, comme `rebuild_sharpedo.py`, sans appliquer de nouvelle heuristique de segmentation. `02_nuages` défile là où le layout contient des nuages ; la prairie a un ciel délibérément dégagé et garde un PNG nuages transparent au lieu d’inventer une masse nuageuse. `01_astres` est transparent le jour et animé la nuit.

Afin qu’un nuage en déplacement ne découvre pas une découpe vide, `00_ciel` reçoit une reconstitution inpaintée derrière les pixels mobiles. À la phase 0, les pixels originaux des nuages/astres sont composités au-dessus : **la composition est donc identique, pixel par pixel, à la native générée**. Cette méthode implique que le ciel et les plans atmosphériques peuvent se chevaucher précisément à l’image 0. Les plans de décor terrestre restent séparés ; le contrôle ne prétend plus faussement que chaque pixel de tous les plans est exclusivement attribué une seule fois.

### D. Exports et contrôle exécuté

Chaque scène/ambiance de `references_exterieures/` contient les PNG RGBA, la composition, les bases transparente/magenta, un `.aseprite` de 24 images et une carte `.tmj`. Nuages, étoiles et crêtes d’eau/cascades animés ont leur atlas dans `animations/`; les groupes des étoiles sont conservés dans `etoiles_groupes.png`. `apercu_references_exterieures.html` encode ses PNG en WebP data URI, permet de changer scène/ambiance, pause/reprise, visibilité de chaque plan et grille de 8 px sans appel réseau.

Les commandes suivantes ont été exécutées après le changement vers l’architecture animée :

```bash
python source/prepare_references_exterieures.py
python source/rebuild_references_exterieures.py
python source/verify_references_exterieures.py
```

Le vérificateur de cette livraison contrôle les dimensions/alpha des natives, l’identité de chaque PNG livré avec sa source dans le pack de plans, l’identité native = composition à la phase 0, les bases, les deux ambiances, la périodicité et le mouvement des plans non vides, tous les pixels de toutes les cels Aseprite, les cels liées des plans fixes, les atlas et séquences de 24 tuiles Tiled, la grille 8 px de l’aperçu et l’absence d’URL réseau. Il ne rend pas de jugement esthétique ni de licence : une revue humaine reste nécessaire.

---

## 8. Règles à conserver pour les suites

1. Toujours lire les commits dans l'ordre temporel avant d'associer une sortie à une référence.
2. Conserver l'image complète native en source, puis produire les plans et tous les formats depuis elle. Ne jamais ne modifier qu'une composition livrée.
3. Pour une ambiance nuit, conserver la géométrie du layout jour lorsque cela est demandé ; isoler astres et nuages dans des plans dédiés et garder la lune fixe.
4. Employer une grille 8 px lorsque les cartes Aseprite/Tiled sont demandées, sans transformer le rendu en gros carrés de 8 px.
5. Vérifier la recomposition pixel à pixel à la phase 0. Lorsqu’un plan se déplace, reconstituer derrière lui un fond cohérent ; ne pas prétendre que ce fond et l’atmosphère sont disjoints.
6. Distinguer clairement références de travail, sources externes, natives préparées et exports de jeu ; garder les informations de provenance avec les assets.
7. Ne pas prétendre qu'un test de format valide une décision artistique ou une licence.
8. Limiter les gros binaires aux formats explicitement demandés. Pour une simple référence, les PNG peuvent suffire ; pour une intégration modulaire, garder en plus Aseprite/Tiled et les scripts de contrôle.

---

## 9. État de cette livraison

- Les trois layouts sont produits dans `references_exterieures/` en **jour et nuit**, avec sept ou huit plans sémantiques par ambiance.
- Les six natives finales viennent des rendus générés de cette livraison ; les références récentes restent des guides tracés, non des pixels livrés.
- Les nuages non vides défilent, les étoiles nocturnes scintillent, les lunes restent fixes et les crêtes d’eau/cascades bouclent dans Aseprite, Tiled et l’aperçu.
- La chaîne préparation → export → vérification a été exécutée avec succès sur cette architecture animée.
- L’aperçu `apercu_references_exterieures.html` est autonome et permet de masquer chaque plan, changer d’ambiance et mettre la boucle en pause.

Ce manuel doit être lu avec `references_exterieures/README.md`, qui décrit le contrat de fichiers de la nouvelle livraison.
