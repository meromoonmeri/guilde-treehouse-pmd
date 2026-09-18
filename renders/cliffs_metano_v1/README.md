# Falaises Métano — sprites et nouvelles zones, lot 01

**[Planche des quatre compositions](PLANCHE_FALAISES_METANO.png)** · **[Atelier interactif](index.html)** · **[Kit téléchargeable](METANO_CLIFFS_V1_pack.zip)**

Demande du 18 septembre 2026 : des **cliffs / falaises**, à partir des références qui ont servi aux anciens rendus Métano, et de nouvelles zones. Ni ponts, ni étangs. Anciens assets et cartes conservés sans modification.

## Contenu

| Composition | Usage proposé | PNG transparent jour |
|---|---|---|
| Cap des Alizés | Sprite de plateau isolé, retour concave | [PNG](01_cap_des_alizes/METANO_CLIFFS_V1_01_cap_des_alizes_terrain_jour.png) |
| Balcon du Levant | Sprite de corniche courbe | [PNG](02_balcon_du_levant/METANO_CLIFFS_V1_02_balcon_du_levant_terrain_jour.png) |
| Défilé des Explorateurs | Nouvelle zone sèche ouverte sud–nord | [PNG](03_defile_des_explorateurs/METANO_CLIFFS_V1_03_defile_des_explorateurs_terrain_jour.png) |
| Terrasses du Sillage | Nouvelle zone étagée, grand escalier | [PNG](04_terrasses_du_sillage/METANO_CLIFFS_V1_04_terrasses_du_sillage_terrain_jour.png) |

Chaque dossier contient le terrain **jour et nuit**, une version magenta, deux scènes PNG et deux projets **OpenRaster `.ora`**. Dimensions réelles : **1264 × 848 px**, RGBA, alpha binaire. Pas de redimensionnement des terrains après génération. Les deux sprites sont entourés de transparence ; les deux zones se prolongent aux bords pour leurs accès.

Les noms `METANO_CLIFFS_V1_*` sont uniques : l’importeur PMDO peut écraser les ressources ayant le même basename.

## Méthode du dépôt suivie

1. Références réellement fournies au générateur : [scène Métano](../../source/falaises_generees/reference_canonique.png), [échantillons natifs](../../source/caps_terrasses_v4/reference_matiere_stricte.png), puis présentation [Crochet droit V4](../caps_terrasses_v4/08_crochet_droit_terrain.png) pour les sprites et [témoin Métano](../falaise_metano_temoin/01_crete_sillage_transparent.png) pour les zones.
2. Quatre compositions texturées sur magenta. Deux passages correctifs supplémentaires : retrait de la banquette parasite du cap ; suppression du garde-corps et ouverture nord pour le défilé. Les **six bruts** restent dans `bruts/`, sans écrasement.
3. Détourage magenta suivant les règles du lot Caps/Terrasses V4. Ombres mauves conservées, RGB invisible mis à zéro.
4. Couleurs ramenées aux **328 RGB natifs de la palette V4**, par plus proche couleur en CIELAB. Cela ne modifie pas la géométrie mais peut simplifier le grain de certaines surfaces ; les bruts restent disponibles pour comparaison.
5. Nuit avec le filtre Abyss déjà employé dans le dépôt. Pas de palette nocturne inventée.
6. Contexte séparé, aperçu, ORA et vérification de recomposition.

**Textures de référence canoniques, nouveaux dessins générés.** Ni les dessins, ni leurs dimensions ne sont certifiés comme des tuiles natives PMD. La référence effective est Métano issue de Halcyon ; aucune nouvelle extraction spécifique de Bourg-Trésor n’a été réalisée. Appartenir à la palette canonique n’est pas une preuve d’identité du motif.

## Calques — ce qu’ils permettent vraiment

Comme Caps/Terrasses V3–V4, le **terrain est un seul calque réunissant herbe, roche, bordures et escaliers éventuels**. Il n’y a pas de faux calques sémantiques découpés par couleur ni de sol caché prétendument reconstruit.

Les `.ora` contiennent cinq plans de même taille, tous à `(0,0)` :

1. ciel jour/nuit validé ;
2. astres natifs indépendants ;
3. six familles de nuages validées, phase 0 ;
4. océan, phase 00 ;
5. terrain complet.

Ils s’ouvrent dans Krita ou GIMP. Déplacer le terrain entier est possible ; déplacer indépendamment ses morceaux ou retirer une falaise pour révéler un sol complet ne l’est pas. Les ORA sont **statiques**, pas des projets d’animation PMDO.

**Correction demandée par l’utilisateur :** les fonds de Caps/Terrasses V3 étaient les mauvais. Le ciel et les nuages sont désormais repris depuis les sources validées **Guilde/Sharpedo, commit `c16efe12`**, dans `source/cote_dix_zones/reference_autre_agent/`. Le ciel utilise sa moitié gauche sans lune cuite, répétée en miroir sans resampling, comme le lot Dix Zones ; astres natifs sur un plan séparé. Les **six familles de nuages** sont déplacées entières sur leur bande de **1440 × 208**, sans agrandissement. Nuit des nuages : formule Guilde/Sharpedo originale, pas le filtre Abyss du terrain. Wrap **−4 px/s, boucle 360 s**, visible dans l’atelier. Les terrains jour/nuit sont conservés à l’identique.

Seule la mer reste issue de Caps/Terrasses V3, adaptée en nearest pour la démonstration. Aucun pixel du terrain n’est redimensionné. Les scènes marines ne constituent pas de nouvelles cartes d’eau.

L’océan du viewer reprend **64 phases × 50 ms = 3,2 s** du lot V3. Les 128 PNG jour/nuit correspondants sont dans `contexte/`. Ce n’est ni un nouveau cycle officiel extrait, ni une animation ajoutée à un Ground. La case animation est indépendante des calques et respecte la préférence système de réduction des mouvements.

## Import PNG to Tileset

- Utiliser **uniquement `*_terrain_jour.png` ou `*_terrain_nuit.png`** pour importer le terrain transparent.
- Taille des tuiles : **8 px** → feuille de **158 colonnes × 106 lignes**.
- Pas de marge, pas d’espacement, pas de lissage.
- Importer dans une nouvelle ressource et **vérifier d’abord l’échelle à côté d’un personnage et d’une falaise native**. Dimensions divisibles par 8 ne signifient pas échelle native garantie.
- Poser des rectangles complets ; ce ne sont **pas** des autotiles universels. Pas de garantie de raccord entre deux sprites.
- Tracer les collisions, définir les entrées/sorties et la profondeur d’affichage dans votre projet. Aucun `.rsground`, `.tile`, script de téléportation ou collision n’est fourni.
- Ne pas importer la planche, les scènes, les bruts ou les ORA comme tilesets de terrain transparent.

## Inspection visuelle et réserves

- **Cap :** banquette parasite retirée. Texture rocheuse encore plus grosse que l’échantillon natif ; à valider à l’échelle du jeu.
- **Balcon :** silhouette et sol continus, retours mauves. Face assez régulière ; pas de certification de raccord.
- **Défilé :** la correction a ouvert le mur du fond jusqu’au sol central. Le résultat est un défilé, **plus le cirque initial**. Les grandes surfaces vertes et les accès sont visibles ; leur praticabilité n’a pas été testée dans PMDO.
- **Terrasses :** plages de sable et banquette intermédiaire ajoutées par le générateur. Escalier référencé mais redessiné, pas extraction native.

Tous sont des **candidats inspectés, non encore approuvés par l’utilisateur**. Ni la scène de démonstration ni les contrôles de fichiers ne valent validation moteur.

## Sources et contrôles

- [Manifest détaillé et empreintes](manifest.json).
- [Contrôles automatisés](../../source/cliffs_metano_v1/verification.json).
- [Audit des couleurs](../../source/cliffs_metano_v1/audit_couleurs.json).
- [Scripts et reproduction](../../source/cliffs_metano_v1/README.md).

Le ZIP contient les huit terrains, les huit projets ORA, les calques de contexte, la planche, un catalogue HTML local et la notice. Pour éviter la duplication, les six bruts et les huit scènes PNG restent consultables dans le dépôt mais ne sont pas inclus dans ce kit.
