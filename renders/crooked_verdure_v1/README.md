# Crooked Cavern — biome verdoyant, roche grise

Galerie : `apercu_crooked_verdure_v1.html` à la racine. Vue Crooked Cavern multicouche et bouton pour voir directement le Spring animé.

## Livrables
- [Crooked Cavern PNG](composition.png) / [agrandissement nearest ×3](composition_x3.png)
- [Animation WebP](animation.webp) / [GIF](animation.gif)
- [Spring : colonne irisée en GIF](spring_colonne_irisee.gif)

## Matériaux et disposition
Canvas natif **320×240**, sans agrandissement du dessin des rochers. Référence réellement utilisée : `source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png`, calque des objets `layer_1.png`, et carte `.rsground` correspondante. Provenance source dans le dossier `source/cote_v5_expeditions/references/`.

- Dessin des parois conservé à l’échelle 1 ; entrée décalée de **+8 px**. Une bande de 8 px complète le bord gauche.
- Roche recolorée en gris légèrement froid : luminance arrondie `.299R + .587G + .114B`, puis RGB = luminance × `[.91,.97,1]`. **La couleur est nouvelle, mais les motifs rocheux ne sont pas redessinés par le générateur.**
- Deux groupes de blocs natifs repositionnés pour modifier légèrement l’avant-plan.
- Sol : patch d’herbe natif de Luminous Spring, coordonnées `[250,390,314,454]`, répété ; chemin conservant les pixels du sol sableux de Crooked Cavern. Les contours herbe/roche sont des masques manuels, pas un nouveau tileset natif.
- Six petites touffes végétales générées guidées par le Spring, séparées des matériaux canoniques. Leur dessin n’est pas prétendu identique à des assets Halcyon.

`bruts/proposition_layout.png` est la proposition générée de direction artistique. Le rendu final revient aux vrais pixels rocheux pour conserver leur texture. `bruts/vegetation.png` contient les décorations ajoutées.

## Calques
1. `calques/01_sol_herbe_chemin.png`
2. `calques/02_paroi_grise.png`
3. `calques/03_rochers_gris.png`
4. `calques/04_vegetation.png`
5. `animation/particules/00.png`…`47.png`

Tous sont alignés sur 320×240 et se composent dans cet ordre.

## Animations
La carte Halcyon Crooked Cavern source est **statique** : ses 1399 références de tuiles ont une seule frame. Aucune animation native de cascade, roche ou végétation n’est inventée comme si elle provenait du jeu.

L’animation nouvelle ajoute seulement quelques particules lumineuses discrètes : **48 phases × 80 ms = 3,84 s**, mouvement et intensité cycliques. Aucun déplacement des parois. Le WebP conserve les 48 phases sans perte. Le GIF utilise une palette commune de 256 couleurs ; deux phases devenues identiques sont fusionnées, soit **47 images encodées**, avec une durée totale toujours de 3,84 s.

Le Spring GIF est une conversion de `renders/spring_colonne_irisee_v1/animation.webp` : **78 images / 6,5 s**, bassin turquoise, escalier conservé, colonne seule irisée. Palette GIF limitée à 256 couleurs ; le WebP original reste la référence sans perte.

## Vérifications et limites
`verification.json` : comparaison indépendante des pixels opaques de la paroi avec la formule de recoloration et le décalage annoncés ; recomposition exacte de la première scène ; décodage et durée des animations. Scripts : `source/crooked_verdure_v1/build.py` (Pillow + numpy).

Pas de nouvelle carte `.rsground`, collision ou validation en jeu. Le sol répété et les raccords sont des propositions graphiques à valider. Les ressources antérieures ne sont pas modifiées.

Attributions : carte Halcyon / Palikadude ; textures originales distribuées dans les sources référencées du dépôt ; herbe Luminous Spring de PMDCollab/RawAsset. Disponibilité publique ne signifie pas licence illimitée. Respecter les droits Pokémon Mystery Dungeon et des contributeurs. Les ajouts générés ne sont pas attribués à Palika.
