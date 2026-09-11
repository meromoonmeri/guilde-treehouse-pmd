# Audit de `main` — méthode de travail et règles de reprise

**Date : 8 septembre 2026.**

**Référence auditée :** `origin/main`, commit `6c4ac5aad90da4f670d4965ec3d37a3ea38b5c78`, après actualisation depuis GitHub.

**Périmètre :** documentation, tous les scripts, manifestes, assets, aperçu, contrôles, historique de `main` et métadonnées de livraison. Les autres branches ne sont pas prises pour référence.

## Conclusion

La méthode observable est une **reprise des images validées au générateur, suivie d'un traitement et d'exports par scripts Python**. Ce n'est ni une création intégrale des salles par dessin procédural, ni une application à réécrire avec un framework, ni un projet de jeu déjà intégré.

La continuité à respecter est : **préserver les bases et la direction graphique, retoucher seulement ce qui est demandé, reconstruire les calques et tous les formats associés, vérifier les résultats et fournir un aperçu autonome.** Les scripts et les assets existants n'ont pas été modifiés pendant cet audit ; seul ce rapport est ajouté.

Les contrôles livrés passent sur `main` et après reconstruction. Les 24 compositions de salles et leurs 48 bases transparentes/magenta sont reproduites **à l'octet près**. La reconstruction complète n'est toutefois pas strictement identique pour tous les fichiers éditables et les planches : détails ci-dessous.

## 1. Ce que l'historique permet réellement de savoir

- `main` contient **un seul commit**, daté du 5 septembre 2026 : « Guilde PMD: 12 salles, passages ouverts, paysages modulaires et calques fixes ».
- Le tag `pmd-passages-ouverts-v1` pointe sur ce même commit.
- La [release correspondante](https://github.com/meromoonmeri/guilde-treehouse-pmd/releases/tag/pmd-passages-ouverts-v1) annonce un kit vérifié et propose `Guilde_Treehouse_12_Salles_Vides_Fixes.zip` de 35 528 491 octets.
- Aucune PR, issue ou configuration GitHub Actions n'a été trouvée. Aucun `AGENTS.md`, journal de conversation ou historique de prompts n'est présent dans `main`.
- Le README indique explicitement que les retouches ont été réalisées **avec le générateur à partir des images du kit** ; les images de jeu fournies par l'utilisateur servaient à comprendre les passages, pas à être collées dans les décors.

**Limite importante :** les sources permettent de reconstituer la chaîne technique et les choix conservés, pas les prompts exacts, le générateur précis, les essais rejetés, l'ordre des échanges ou le style conversationnel de l'ancien agent. Un commit de livraison unique ne permet pas non plus de déduire ses habitudes de commit ou de revue.

L'archive de release n'a pas pu être téléchargée dans cet environnement en raison d'un échec réseau ; son contenu n'a donc pas été comparé au dépôt. Les métadonnées de la release ont bien été consultées.

Références : [README, lignes 62–74](README.md), historique Git et release GitHub.

## 2. Structure du kit à conserver

Le commit audité contient **659 fichiers suivis**, dont 595 PNG, 24 Aseprite, 24 cartes Tiled et 5 scripts Python.

| Élément | Organisation actuelle |
| --- | --- |
| Salles | 12 identifiants stables, `01` à `12`, dossiers nommés en français |
| Dimensions | Hall 02 : **1280 × 544 px** ; autres salles : **648 × 432 px** |
| Grille | **8 × 8 px** ; 160 × 68 cellules pour le hall, 81 × 54 ailleurs |
| Intérieurs | Jour et nuit ; fixes, sans animation |
| PNG de salles | 24 compositions, 24 bases transparentes, 24 bases magenta |
| Calques | 11 par salle et par palette, soit **264 PNG** |
| Fenêtres | 12 masques et **72 vues extérieures** positionnées |
| Paysages | Jour, nuit, crépuscule, aube, soir, orageux |
| Édition | 24 Aseprite à une seule frame ; 24 cartes `.tmj` |
| Objets séparés | **135 sprites individuels**, deux atlas jour/nuit et deux halos fixes |
| Présentation | Deux planches et un HTML autonome d'environ 5 Mo |

La grille de 8 px est un repère d'édition et d'export, **pas une consigne pour transformer l'image en gros blocs de 8 px**.

### Règles visuelles explicites

- Conserver l'univers graphique du premier pack : structure en bois, proportions, cadrages et rendu existants.
- Garder les salles **vides et fixes**. Ne pas replacer automatiquement meubles, plantes, tapis, paillasses, bannières ou lampes depuis la banque de sprites.
- Les accès ordinaires sont des **ruptures du contour traversées par le plancher**, pas des battants, arches ou portiques ajoutés.
- Aucune porte sud visible. Les accès nord de 01 et 09 sont ouverts ; les échelles existantes gardent leur fonction.
- Une seule porte fermée visible : **au nord du hall 02, vers le bureau 12**, avec son emblème à quatre ailes. L'accès intérieur de 12 reste au sud, sans porte dessinée.
- Dans le hall, tronc et échelle continuent au-delà du bord supérieur.
- Conserver les deux tableaux encastrés du hall.
- Garder des ombres de contact, pas une barre noire qui bouche le passage.
- Conserver cadres, croisillons et persiennes ; les vues extérieures restent indépendantes, jamais peintes dans la base intérieure.
- La salle 01 n'a pas de fenêtre vitrée. Les interstices des persiennes de 08 et 10 reçoivent aussi le paysage interchangeable.

Références : [README, lignes 3–60](README.md), [règles d'accès](source/regles_acces.json), [manifeste courant](kit.json).

## 3. Chaîne de travail reconstituée

### A. Préserver les références et repartir des sources retenues

`source/base_kit.json` conserve des informations du pack antérieur, dont le nom `Guilde_Treehouse_12_Zones_Jour_Nuit.zip`, une empreinte SHA-256 et `source_originale_modifiee: false`. Le README demande aussi de laisser les archives de la terrasse approuvée intactes.

Ces archives originales ne sont pas présentes dans `main` : leur intégrité historique est **documentée mais non revérifiable ici**. Les références effectivement disponibles sont les natives, les couches du paysage et l'emblème.

Les retouches graphiques principales proviennent du générateur ; Python prend ensuite en charge le détourage, la séparation des couches, des corrections locales contrôlées, les variantes de palette et les exports. Il ne faut donc pas remplacer cette méthode par un redessin complet des salles en code.

### B. Neuf natives produisent douze salles

`source/rebuild_kit.py` charge les images de `source/natives/`, puis applique les correspondances et miroirs suivants :

| Salle | Source native | Transformation | Accès actuels |
| --- | --- | --- | --- |
| 01 — Accueil | `01.png` | Aucune | N, S |
| 02 — Hall des missions | `02.png` | Aucune | O, S, échelle N, porte N vers 12 |
| 03 — Salle commune | `03.png` | Aucune | O, E, S, échelle N |
| 04 — Cantine | `04.png` | Aucune | E |
| 05 — Chambre de l'équipe | `05.png` | Aucune | E |
| 06 — Chambre du veilleur | `06.png` | Aucune | S |
| 07 — Chambre des résidents | `05.png` | Miroir horizontal | O |
| 08 — Dortoir des apprentis | `08.png` | Aucune | E |
| 09 — Grand dortoir | `09.png` | Aucune | N |
| 10 — Dortoir des explorateurs | `08.png` | Miroir horizontal | O |
| 11 — Chambre des éclaireurs | `05.png` | Miroir horizontal | O |
| 12 — Salle du chef | `12.png` | Aucune | S |

**Conséquence pratique :** retoucher `05.png` affecte 05, 07 et 11 ; retoucher `08.png` affecte 08 et 10. Les bases de 07 et 11 sont actuellement identiques. Il ne faut pas croire que douze dossiers impliquent douze images sources indépendantes.

Les anciens champs `entrees_originales` de `base_kit.json` ne sont pas les règles actuelles : par exemple, ils conservent l'ancienne liaison du bureau avec 03. La reconstruction utilise les passages de `source/regles_acces.json`. Du manifeste ancien, elle utilise surtout les identifiants, noms et dossiers des salles.

Référence : [rebuild_kit.py, lignes 9–13 et 47–50](source/rebuild_kit.py).

### C. Détourer et décomposer sans remplacer le résultat graphique

Le script :

1. Supprime le magenta des natives par seuils de couleur et nettoyage de proximité.
2. Repère la porte verte du hall ; corrige localement son petit emblème avec `source/embleme_4_ailes.png`, sans redessiner la salle entière.
3. Détecte les trous de fenêtres avec SciPy et les composantes connexes OpenCV ; sépare le bois des cadres et croisillons.
4. Isole le contenu des tableaux encastrés du hall.
5. Segmente le sol avec **GrabCut**, puis inclut les continuités des accès et sépare structure et bordure avant.
6. Décompose les ombres de contact sur un plan d'opacité indépendant. Une assertion exige de retrouver les couleurs de la native détourée à un niveau par canal près.

Ordre fixe des calques :

```text
00_exterieur
01_sol
02_structure
03_cadres_fenetres
04_tableaux
05_porte_maitre
06_decorations       — vide
07_objets            — vide
08_ombres_acces
09_eclairage_fixe    — vide
10_bordure_avant
```

Les couches vides sont **volontaires** : elles font partie du contrat de livraison. La couche de porte doit être vide hors du hall.

Référence : [rebuild_kit.py, lignes 20–24 et 51–129](source/rebuild_kit.py).

### D. Produire des variantes fixes, sans changer la géométrie

- La nuit intérieure est dérivée des couches de jour : coefficients RVB `(0.36, 0.34, 0.43)`, ajouts `(9, 10, 19)`, arrondi au pair. Le calque d'ombre garde sa même opacité.
- La géométrie et l'alpha des douze bases sont identiques entre jour et nuit, ce qui a été vérifié.
- Les paysages jour/nuit se recomposent chacun à partir de neuf couches de `source/paysage_reference/`.
- Les quatre autres ambiances dérivent de cette même géographie par palettes, ciel et météo. La pluie est fixe et sa génération utilise une graine explicite, `808`.
- Un panorama continu est redimensionné au plus proche voisin, positionné derrière la salle puis masqué aux ouvertures : pas de paysage inventé indépendamment pour chaque fenêtre.
- Palette intérieure et ambiance extérieure restent sélectionnables indépendamment.

Références : [rebuild_landscapes.py](source/rebuild_landscapes.py), [rebuild_kit.py, lignes 20–21 et 133–149](source/rebuild_kit.py).

### E. Reconstruire les livrables, pas seulement un PNG

- PNG composés, bases transparentes et variantes de contrôle sur `#FF00FF`.
- PNG séparés de chaque calque.
- Aseprite écrits directement en binaire avec compression zlib, onze couches, une frame et grille de 8 px.
- Cartes Tiled orthogonales : chaque image de calque sert de tileset découpé en cellules de 8 px. Les tuiles reconstituent l'image ; ce n'est pas un système de collisions ni une bibliothèque de terrain procédural.
- `kit.json` et planches jour/nuit.
- La banque de sprites antérieure est conservée séparément ; les scripts actuels **ne la reconstruisent pas**.

Le filtre `GUILDE_ROOMS=05,07,11` permet de reconstruire un sous-ensemble, puis de fusionner ces entrées dans le manifeste existant. Le code montre que cette possibilité est prévue ; il ne prouve pas quelles commandes l'ancien agent a effectivement exécutées.

Référence : [rebuild_kit.py, lignes 15–19, 25–36 et 130–174](source/rebuild_kit.py).

### F. Construire un aperçu léger et autonome

`source/build_preview.py` produit le HTML : Canvas et JavaScript natif, sans backend, framework ou dépendance réseau nécessaire à l'affichage.

Les images sont embarquées en PNG ou WebP sans perte, dédupliquées par SHA-256. Une partie des couches nocturnes est calculée dans le navigateur pour éviter d'embarquer des doublons. **La formule de nuit est donc présente à la fois dans Python et JavaScript : toute évolution doit maintenir les deux en accord.**

L'interface française conserve sélection de salle, palettes, six paysages, calques, magenta, grille, zoom, miniatures et vue des panoramas. Les couches vides sont désactivées. L'aperçu doit fonctionner hors ligne, sur mobile et en iframe `sandbox="allow-scripts"`.

Référence : [build_preview.py](source/build_preview.py).

## 4. Contrôles effectivement exécutés pendant l'audit

Les essais ont eu lieu dans des copies isolées extraites de `origin/main`, sous `.cache/`, avec un environnement Python dédié. Aucune reconstruction n'a été lancée sur les assets de travail.

| Vérification | Résultat |
| --- | --- |
| `verify_pmd.py` sur les fichiers de `main` | **PASS** |
| Reconstruction paysages → kit → aperçu, puis `verify_pmd.py` | **PASS** |
| PNG / Aseprite / Tiled | Recompositions exactes pour les 24 variantes |
| Calques vides, porte isolée, transparence et magenta | Assertions livrées réussies |
| `verify_browser.py` sur l'aperçu de `main` | **144 comparaisons**, erreur maximale **0**, aucune erreur JS |
| Même vérificateur après reconstruction | **144 comparaisons**, erreur maximale **0**, aucune erreur JS |
| Hors ligne, iframe sandbox, image fixe, mobile 390 px | Tests livrés réussis |
| Vérification complémentaire de largeur | Pas de débordement observé à 320, 390, 680, 950 et 1280 px dans l'état testé |
| 135 sprites et atlas jour | Fichiers présents, tailles et rectangles cohérents, pixels identiques aux zones d'atlas, pas de chevauchement de rectangles |
| Placements historiques de sprites | 121 références, aucun identifiant inconnu |
| Manifeste courant | Chemins des fichiers de salles valides ; règles embarquées identiques au fichier de règles |

Les deux exécutions de `verify_pmd.py` produisent un rapport identique à `controle_qualite.json` commité. Le rapport navigateur commité indiquait une erreur maximale de 1 ; l'environnement de cet audit obtient 0, sans modifier les assertions.

Inspection visuelle effectuée sur les planches jour/nuit, la native et la base transparente du hall, les six paysages reconstruits, l'atlas et les captures bureau/mobile.

### Environnement utilisé

Python `3.11.2`, Pillow `12.3.0`, NumPy `2.4.6`, SciPy `1.17.1`, OpenCV headless `5.0.0.93`, Playwright `1.62.0`.

Le CDN d'installation standard de Playwright était inaccessible. Les tests ont utilisé Chromium `152.0.7977.0`, distribué par `@sparticuz/chromium@152.0.0`, avec ses bibliothèques embarquées. Un adaptateur d'audit a uniquement sélectionné ce binaire et ses options de lancement ; les vérificateurs du dépôt et leurs assertions sont restés inchangés. Aucun flag de désactivation de la sécurité web n'a été utilisé pour les tests réussis.

## 5. Constats et limites à connaître

### 5.1 Reproductibilité des fichiers éditables — vigilance moyenne

Après reconstruction paysages → kit → aperçu et validation des assets, **avant réécriture du rapport navigateur**, **648 fichiers sur les 659 suivis sont identiques à l'octet près**. Les 11 fichiers différents à ce stade sont :

- `apercu_pmd.html` ;
- les deux planches ;
- les calques sol et structure jour/nuit de 12, soit quatre PNG ;
- les deux Aseprite de 12 ;
- les deux cartes Tiled de 12.

Pour 12, **10 positions de pixels changent d'affectation entre sol et structure**. Cela se répercute dans les fichiers éditables et l'aperçu embarqué, mais ne change pas la composition finale. Un essai supplémentaire avec `GUILDE_ROOMS=12` retrouve les mêmes PNG de sol/structure que `main`, alors que l'exécution complète en diffère. Le découpage dépend donc du contexte d'exécution dans l'environnement testé ; `cv2.grabCut` est appelé sans réinitialisation explicite de sa graine.

Les différences des planches se situent dans les bandes de texte. Le rendu typographique dépend notamment de Pillow et de la police système ; sa cause historique exacte n'est pas établie.

Les dépendances ne sont pas verrouillées dans `requirements.txt`. **Ne pas promettre une reconstruction intégralement identique sans vérifier les différences.** À l'inverse, les 24 compositions, 24 bases transparentes, 24 bases magenta, six panoramas et 72 vues de fenêtres sont identiques à l'octet près dans cet essai.

La reconstruction crée également deux fichiers absents du commit : `exterieur/ambiances.json` et `apercus/paysages_six_ambiances.png`.

Références : [requirements.txt](source/requirements.txt), [rebuild_kit.py, lignes 37–39, 46 et 88–94](source/rebuild_kit.py), [rebuild_landscapes.py, lignes 43–48](source/rebuild_landscapes.py).

### 5.2 Historique graphique incomplet — limite de reprise

Les neuf chemins `guides/NN_guide.png` référencés dans `source/regles_acces.json` n'existent pas dans le dépôt. Ils ne sont pas lus par les scripts de reconstruction actuels, donc ce manque ne les bloque pas.

Les prompts et les archives originales ne sont pas présents non plus. Pour reproduire une ancienne consigne qui ne serait pas exprimée par les sources disponibles, il faudra retrouver la référence ou demander une précision, plutôt que l'inventer.

### 5.3 Les tests techniques ne remplacent pas l'examen artistique

`verify_pmd.py` vérifie les pixels recomposés, les formats et les couches attendues. Il ne reconnaît pas sémantiquement une porte éventuellement dessinée dans un mur, ne compte pas les ailes de l'emblème et ne juge pas la qualité artistique des passages.

Aseprite et Tiled ont été vérifiés **par lecture et recomposition des fichiers**, pas dans leur interface graphique. Le README le précise pour Aseprite. Ni collisions, ni transitions, ni déclencheurs de porte ne sont fournis ou testés.

### 5.4 Petit défaut d'état dans l'aperçu — confirmé, faible impact

Reproduction sur le hall :

1. Cliquer sur **« Base seule — magenta »**.
2. Recocher le calque **« Paysage extérieur interchangeable »**.
3. Le paysage revient et le magenta disparaît, mais le bouton « Base seule — magenta » reste visuellement actif et « Vue composée » reste inactif.

Le gestionnaire de case appelle `draw()` sans resynchroniser les boutons via `update()`. Le rendu est correct, son indication d'état est trompeuse. Ce chemin d'interaction n'est pas couvert par le vérificateur livré. Aucune correction appliquée durant l'audit.

Référence : [build_preview.py, ligne 43](source/build_preview.py).

### 5.5 Deux précisions de documentation

- « Vrais PNG RGBA » décrit correctement l'objectif de transparence, mais pas tous les encodages : parmi les 24 bases transparentes, **13 sont RGBA et 11 sont indexées avec une table de transparence**. La transparence est bien réelle dans les deux cas ; un importeur doit prendre en charge les PNG indexés transparents ou les convertir en RGBA.
- Playwright n'est qu'un commentaire dans `source/requirements.txt` ; le bloc de commandes du README ne lance pas `verify_browser.py`. L'installation du module et d'un navigateur est nécessaire pour reproduire aussi ce contrôle.

Références : [README, lignes 21 et 64–69](README.md), [rebuild_kit.py, lignes 15–19](source/rebuild_kit.py), [requirements.txt](source/requirements.txt).

## 6. Protocole à suivre pour les prochaines demandes

1. **Relire les règles actuelles**, identifier les salles concernées et inspecter leurs sources et sorties. Ne pas utiliser les anciennes liaisons de `base_kit.json` comme plan actuel.
2. **Préserver les références validées et les archives d'origine** ; ne pas repartir d'une nouvelle direction graphique sans demande explicite.
3. **Pour une retouche graphique, repartir des images du kit avec le générateur**, en limitant la demande à la zone ou au changement demandé. Garder Python pour les traitements, corrections locales contrôlées, palettes, calques et exports.
4. **Vérifier les sources partagées** : 05/07/11 et 08/10. Reconstruire toutes les variantes affectées, ou rendre une source indépendante seulement si la demande le nécessite.
5. **Conserver les contrats existants** : identifiants, dimensions, grille, ordre des onze calques, couches volontairement vides, indépendance intérieur/paysage, formats fixes. Ne pas éditer uniquement un export qui sera écrasé à la reconstruction.
6. **Reconstruire la chaîne concernée**, puis l'aperçu. Une modification des paysages impose de recalculer leurs vues de fenêtres ; une modification de la formule de nuit impose aussi de synchroniser le JavaScript de l'aperçu.
7. **Exécuter les deux vérificateurs, inspecter les visuels et comparer les fichiers**, surtout les calques. Ne pas se contenter du message final de génération ni d'un ancien JSON de contrôle.
8. **Livrer des fichiers cohérents et un compte rendu factuel**, en français : changements effectués, contrôles exécutés, limites restantes. Mettre à jour les explications si les règles évoluent. Pas de refonte de l'architecture ou de nouveau framework sans besoin explicite.

Chaîne complète actuelle, à exécuter dans un environnement isolé et avec les dépendances nécessaires :

```bash
pip install -r source/requirements.txt
pip install playwright
python -m playwright install chromium

python source/rebuild_landscapes.py
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
python source/verify_browser.py
```

Exemple de reconstruction ciblée d'une source mutualisée, après préparation des paysages :

```bash
GUILDE_ROOMS=05,07,11 python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
python source/verify_browser.py
```

**Position de reprise :** suivre la méthode documentée et ses invariants, sans prétendre connaître les étapes historiques absentes et sans reproduire volontairement un défaut connu. Les constats de cet audit ne constituent pas une autorisation de retoucher les salles ou de refondre les scripts. Aucun commit, push, changement de branche ou nouvelle publication n'a été effectué.
