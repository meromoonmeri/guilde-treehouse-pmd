# Guilde Treehouse — entrées et sorties PMD

**Plan et audit actuels : [RDC + 3 étages, formes arrondies conservées](plans/guilde_4_niveaux/index.html).** Le plan de référence, les connexions, les contrôles de gabarit et les manques d’intégration sont détaillés dans ce dossier.

> **Couloirs — changement de méthode :** la version procédurale a été rejetée. [Voir la première galerie réellement générée et ses calques](tilesheets/generes/galerie_est_ouest/apercu.html), traitée selon la méthode du kit d’origine. Les huit autres modules restent à remplacer.

**Nouveau : [tilesheets et modules top view](tilesheets/README.md)** — 20 objets, 32 tuiles de parquet, 16 traces spiralées sur calque séparé et 9 couloirs/paliers jour/nuit. [Ouvrir leur atelier interactif](tilesheets/apercu.html). **Couloirs v2 : 13 calques, panneaux muraux distincts du parquet et bordures d’immersion.** [Voir leur séparation](tilesheets/apercus/separation_couloir.png). Ce kit est indépendant des douze intérieurs ci-dessous.

**Version 2 — correction des accès, sans changement de direction artistique.**

Les douze intérieurs conservent le bois ambré, les textures, les dimensions, les fenêtres et l’identité de notre guilde. La référence PMD fournie par l’utilisateur sert à comprendre la construction des passages et leurs ombres, **pas à remplacer notre décor par de la roche, des briques ou de l’herbe**.

## Ce qui a été corrigé

- **Nord, salles 01/09 :** passage de plain-pied en retrait dans le mur, au lieu d’un escalier qui monte hors cadre. Le plancher reste visible dans la profondeur ombrée. Aucune porte ajoutée.
- **Est / Ouest :** sol continu jusqu’au bord de caméra, petits murs arrière raccordés et retours de bordure avec leur épaisseur. Aucun portique ni poteau isolé.
- **Sud :** continuité de sol jusqu’au bord inférieur et joues basses du contour ; aucune porte sud visible. Les deux poteaux de 06 ont été retirés.
- **Échelles 02/03 :** le tronc et l’échelle se prolongent au-delà du bord supérieur, sans sommet scié.
- **Salle 12 :** le tronc reste architectural, mais sa petite échelle sans destination a été retirée. L’accès reste au sud.
- **Une seule porte fermée visible :** celle du maître, au nord du hall 02, donnant vers 12.
- **Ombres et lumière :** contacts localisés sur les joues et les pieds d’échelle, fins reflets des seuils, atténués la nuit. Aucun halo ni bande noire traversant le passage.
- **Finition :** petits trous oubliés des persiennes 08/10 et franges roses corrigés ; masques de sol nettoyés et figés.

Les pièces restent **vides et fixes**. Aucun meuble, paillasse, tapis, plante, bannière ou lampe n’est ajouté aux fonds. Les tableaux encastrés du hall sont conservés. La banque d’objets reste séparée.

## Fenêtres et paysage

- `base_jour_transparente.png` / `base_nuit_transparente.png` : vrais PNG transparents, sans paysage intégré dans les ouvertures.
- `base_jour_magenta.png` / `base_nuit_magenta.png` : variantes de contrôle sur fond **#FF00FF**. Utiliser de préférence les PNG transparents dans le jeu.
- `fenetres_exterieur/NN/` : six paysages déjà positionnés et masqués aux fenêtres de chaque salle, y compris les petits interstices des persiennes.
- `exterieur/` : six panoramas complets issus de la géographie approuvée de la terrasse.

Ambiances : **jour, nuit, crépuscule, aube, soir et orageux**. Le paysage et la palette intérieure peuvent être choisis indépendamment. La salle 01 n’a pas de fenêtre vitrée.

## Onze calques séparés

1. Paysage extérieur interchangeable
2. Sol continu et passages
3. Structure et retours des passages
4. Cadres et persiennes, sans paysage
5. Contenu des tableaux encastrés — hall
6. Porte nord du bureau — hall uniquement
7. Décorations — **vide**
8. Objets — **vide**
9. Ombres de contact des accès
10. **Lumière et reflets des seuils — désormais renseigné**
11. Bordure avant et joues basses

Chaque salle a une version jour et une version nuit, avec **une seule image par Aseprite**. Le modelé ambiant du bois reste dans les textures : les nouveaux plans d’ombre et de lumière ne prétendent pas constituer un éclairage physique complet.

## Contenu

- `apercu_pmd.html` : aperçu autonome et hors ligne. Choix de salle, intérieur jour/nuit, six ambiances, affichage des calques, grille et zoom. **« Base seule — magenta »** permet de contrôler les fenêtres.
- `apercus/` : planches jour/nuit et comparatif des corrections.
- `salles/` : 24 compositions, 24 bases transparentes, 24 contrôles magenta et 24 Aseprite fixes.
- `calques/` : **264 PNG**, onze par salle et par palette.
- `tiled/` : 24 cartes orthogonales à cellules de **8 × 8 px**, reconstituant les images. Ce n’est pas un tileset de construction dédoublonné.
- `kit.json` : dimensions, fichiers, calques, accès et 19 repères d’intégration.
- `source/passages/` : bases corrigées, masques sémantiques validés, retouches génératives retenues, prompts et provenance. Voir [le détail de la méthode](source/passages/README.md).
- `source/natives/` : **les neuf natifs de départ, inchangés**.
- `sprites/` : banque indépendante du premier kit ; aucun de ses éléments n’est posé automatiquement.
- `portraits/falinks/` : **16 portraits d’émotions de Falinks au format PMDCollab** (40 × 40, ≤ 15 couleurs, planche SpriteBot 200 × 320 avec versions retournées), dérivés par retouche pixel du portrait Normal d’Emmuffin. Voir [leur README](portraits/falinks/README.md).
- `personnages/falinks/` : **sprite de donjon de Falinks au complet (forme 0000) au format SpriteCollab** — set donjon complet (Idle, Walk, Sleep, Hurt, Attack, Charge, Shoot, Strike, Swing, Double, Rotate, Hop), 8 directions, `AnimData.xml`, feuilles Anim / Offsets / Shadow, Aseprite animé, variantes nuit, composé à partir des unités Brass et Trooper publiées sur PMDCollab. Voir [leur README](personnages/falinks/README.md) et, pour produire le prochain personnage, [la méthode](source/personnages/METHODE_SPRITES_PMD.md).
- `personnages/zarude/` : **sprite de donjon de Zarude au format SpriteCollab** — dessin original en pixel art (13 couleurs) sur le squelette d'animation de Rillaboom #0812, set donjon complet avec Sing (13 animations), 8 directions, `AnimData.xml`, feuilles Anim / Offsets / Shadow, Aseprite animé, variantes nuit, aperçus et vérificateur. Voir [leur README](personnages/zarude/README.md).
- `rapports/audit_interieurs_guilde/` : rapport **historique**, sur l’état initial `6c4ac5a`, avant ces corrections.

Le hall mesure **1280 × 544 px**, les autres pièces **648 × 432 px**. La grille de 8 px est une grille de travail, pas une pixellisation du dessin en gros blocs.

**Le kit n’est pas un jeu intégré :** collisions, transitions, déclencheurs et ordre d’affichage des personnages restent à configurer dans le moteur. Les rectangles de `source/passages/definitions.json` sont des repères proposés, pas des triggers installés.

## Reproduction

```bash
pip install -r source/requirements.txt
python source/rebuild_landscapes.py  # facultatif si les 6 panoramas sont déjà présents
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
python source/verify_passages.py
```

Pour une salle uniquement, par exemple :

```bash
GUILDE_ROOMS=01 python source/rebuild_kit.py
python source/build_preview.py
```

Les sources artistiques et leurs masques sont figés : le build ne relance ni le générateur ni GrabCut. Les scripts de reconstruction **réécrivent les exports** ; utiliser une copie pour conserver une livraison antérieure.

Vérification navigateur :

```bash
pip install -r source/requirements-validation.txt
playwright install chromium
python source/verify_browser.py
```

Un Chromium déjà installé peut être sélectionné via `PMD_CHROMIUM=/chemin/vers/chromium`.

## Contrôles

- `controle_qualite.json` : PNG, calques, Aseprite et Tiled recomposés, transparence et magenta.
- `controle_passages.json` : 19 repères connectés au sol, dégagement, continuité au bord, petits interstices complets, effets locaux et natifs inchangés.
- `controle_navigateur.json` : 144 combinaisons salle/palette/paysage, fonctionnement hors ligne, mobile et calques d’éclairage activables.
- `controle_reconstruction.json` : 195 fichiers PNG/Aseprite/Tiled comparés après une seconde reconstruction des salles 01/02/03/08/12, identiques octet par octet.

Les fichiers Aseprite/Tiled sont relus par le vérificateur Python, pas validés par une ouverture manuelle dans leurs applications.
