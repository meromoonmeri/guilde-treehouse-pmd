# Soleil animé, grands nuages et nouveau Luminous Spring

Galerie autonome à la racine : **`apercu_soleil_spring_v1.html`**. Trois vues : côte animée, nouveau Spring animé, référence fixe Halcyon. Calques masquables, pause, position des nuages et export PNG.

## Soleil subtil
- [Planche des 8 clés](planches/soleil_8_cles.png)
- [Planche des 64 phases](planches/soleil_64.png)
- [Planche du halo seul](planches/soleil_halo_64.png)
- `soleil/frames/00.png` à `63.png` : cellules RGBA **96×96**, 80 ms/image, boucle **5,12 s**.
- `soleil/disque_fixe.png` + `soleil/halo/00.png` à `63.png` : deux calques recomposables exactement.

Huit clés générées puis détourées et recalées. Le disque est verrouillé ; l’influence des autres clés est limitée à 22%, avec interpolation alpha prémultiplié pour obtenir une animation douce. Les 64 frames ne sont pas 64 générations indépendantes. Couronne à alpha décroissant vers l’extérieur. Position dans l’aperçu côtier : **(702,212)**, centre (750,260), aligné avec le reflet V2.

## Gros nuages traversants
Trois nouveaux sprites : `nuages/{jour,coucher,nuit}_sprite.png`, et trois overlays transparents alignés **960×600** : `*_overlay.png`.

Ordre : ciel → étoiles → astre et halo → **gros nuages** → mer → reflet → falaise. Les nuages occultent donc visuellement le soleil/la lune lorsqu’ils passent devant ; ce n’est pas un nuage peint dans le ciel.

Wrap horizontal : **960 px**, vitesse **−8 px/s**, période spatiale **120 s**. Dessiner deux copies à `x` et `x−960`, avec `x = ((position_initiale − floor(t_secondes×8)) mod 960 + 960) mod 960`. Horloge indépendante du cycle solaire. Le curseur de la galerie permet de vérifier le passage sans attendre 120 secondes. Les nuages ne sont pas ajoutés au Spring, qui reste une clairière forestière.

## Nouveau Luminous Spring
- [Composition PNG](spring/composition.png)
- [Animation WebP complète](spring/animation.webp)
- `spring/01_decor.png` : nouveau pourtour végétal généré, raccordé au cœur natif.
- `spring/02_cycle_3/00.png`…`02.png` : premier groupe natif animé.
- `spring/03_cycle_13/00.png`…`12.png` : second groupe natif animé.
- `spring/frames/00.png`…`38.png` : compositions complètes, **600×600**.
- [Planche cycle 3](planches/spring_cycle_3.png) / [cycle 13](planches/spring_cycle_13.png), aperçus de cellules 300×300 ; utiliser les PNG individuels 600×600 pour l’import.

### Source réellement examinée
Carte **`Data/Ground/luminous_spring.rsground`** de [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), grille 25×25, cellules de 24 px, 2 couches. La carte référence les feuilles **`LuminousSpring` et `LuminousSpringAnim`**, présentes dans [PMDCollab/RawAsset](https://github.com/PMDCollab/RawAsset/tree/master/Tile/24x24) et non dans l’arbre propre de Halcyon. Les pins exacts, fichiers téléchargés et SHA-256 sont dans `source/soleil_spring_v1/references/provenance.json`.

Deux groupes : **38 cellules à 3 phases**, **8 cellules à 13 phases**, **10 ticks par image**. À 60 Hz : boucle commune **39 phases / 390 ticks / 6,5 s**. Le WebP alterne des durées 167/167/166 ms pour respecter 6,5 s ; la galerie calcule directement les phases à 60 ticks/s.

### Ce qui est nouveau / ce qui est conservé
- Nouveau dessin généré : feuillages périphériques, fougères, mousses et petites fleurs autour de l’aire centrale. Il reprend la composition et l’ambiance du Spring de Halcyon, sans prétendre être un nouvel asset créé par Palika.
- Conservés : position, pixels du bassin et des cellules animées, et **vraies phases lues dans les feuilles source**, pas une animation inventée à partir d’une capture.
- `spring/masque_zone_native.png` délimite la zone conservée pixel pour pixel. Le raccord au décor généré est adouci uniquement à l’extérieur de cette zone. Le décor généré brut est également conservé séparément.
- Pas de modification de la carte originale Halcyon. Pas d’intégration `.rsground` ou de validation en jeu dans ce livrable : ce sont des PNG multicouches et un aperçu animé.

## Contrôles
`verification.json` : **209 PNG décodés**, 39 recompositions exactes, 39 comparaisons pixel par pixel contre un rendu indépendant des tuiles source dans la zone protégée, disque solaire stable sur 64 phases et recomposition exacte halo+disque, raccord de boucle solaire et wrap nuages contrôlés.

Galerie testée en DOM simulé : 9 combinaisons vue/ambiance, 9 contrôles de calques, pause/reset, cycle 6,5 s, position nuages et masquage. Ce n’est pas une validation GPU ou PMDO.

## Reproduction et droits
Pillow + numpy. Scripts : `source/soleil_spring_v1/{reference,build,gallery,verify}.py` et `test_viewer.cjs`. Les dépendances de l’aperçu côtier proviennent du pack `references_calques_v2`, conservé sans modification.

Attribution : carte Halcyon / Palikadude ; graphismes de base distribués par PMDCollab/RawAsset ; Pokémon Mystery Dungeon et ses ayants droit pour les ressources concernées. La disponibilité publique ne constitue pas une licence de réutilisation illimitée. Les nouveaux dessins générés sont explicitement distingués des ressources originales.
