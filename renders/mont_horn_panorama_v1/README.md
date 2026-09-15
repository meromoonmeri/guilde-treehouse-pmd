# Mont Horn — entrée sud → nord et panorama

Nouvelle proposition 648 × 504 inspirée de `Mt_Horn_entrance_Sky.png` (552 × 360). L’entrée latérale devient une grotte frontale au nord, accessible par une crête depuis le bas de l’image. Roches gris ardoise, chemin gris légèrement chaud et chaînes de montagnes visibles des deux côtés.

## Livraison
- `../../apercu_mont_horn_panorama_v1.html` : galerie autonome avec lecture/pause, curseur, calques et vue sans nuages.
- `mont_horn/COMPOSITION.png` : état initial.
- `mont_horn/ANIMATION_WRAP.webp` : animation sans perte, 324 phases × 320 ms, boucle de 103,68 secondes.
- `mont_horn/mont_horn_panorama.ora` : sept calques alignés, état initial.
- `mont_horn/horn_composition_cle_*.png` : neuf images de contrôle, pas une séquence complète à lire directement.
- `mont_horn/horn_02_nuages_lointains_*.png` et `horn_07_nuages_overlay_*.png` : deux animations indépendantes plein cadre, 324 PNG chacune.
- `sprites/` : quatre motifs de nuages détourés et deux textures périodiques plein cadre.
- `mont_horn_panorama_v1.zip` : paquet complet avec références, scripts et galerie.

## Sept calques, dans l’ordre
1. Panorama de montagnes et ciel, opaque.
2. Nuages lointains devant le panorama, derrière le relief.
3. Falaises à gauche.
4. Falaises à droite.
5. Chemin en pierre grise.
6. Massif de l’entrée nord avec cavité et marches.
7. Voile de nuages devant les flancs des falaises.

Les quatre morceaux de premier plan sont des masques disjoints d’un même relief généré. Ils se recomposent exactement mais ne contiennent pas de surfaces cachées inventées : déplacer un morceau dans l’ORA peut donc révéler un trou. Le ciel et les montagnes restent ensemble dans un calque de panorama.

## Wrap des nuages
Déplacement vers la droite de 2 px/phase pour le plan lointain (6,25 px/s) et de 4 px/phase pour le voile proche (12,5 px/s). Translation modulo **648 px**, sans fondu entre deux images différentes, sans retour brusque à une position arbitraire. Le plan proche accomplit deux tours pendant que le lointain en accomplit un. Le passage dernière → première phase correspond exactement à un pas normal de translation.

L’overlay est ici un **calque superposé en alpha normal**, pas le mode de fusion Photoshop « Incrustation ». Son alpha ne dépasse pas 69/255 et s’efface progressivement près du centre ; le chemin et l’entrée sont dégagés. Les nuages restent à altitude fixe, sans aller-retour vertical. La galerie reproduit la même cadence que les PNG/WebP.

## Méthode et provenance honnête
La référence PMD originale a été examinée et donnée au générateur. Trois nouvelles images ont été générées : panorama sans nuages, relief isolé sur magenta, quatre motifs de nuages sur magenta. Les bruts sont conservés dans `bruts/`.

Détourage avant assemblage ; réduction au plus proche voisin ; panorama réduit à 80 couleurs ; relief ramené à 432 × 504 et placé en x=108 pour ouvrir les deux vues latérales. Le chemin légèrement beige du brut est ramené vers une gamme grise en conservant sa luminance. Les motifs sont détourés, redimensionnés et répartis en deux textures wrap ; l’animation est calculée, pas générée image par image.

**Il s’agit d’une adaptation générée à partir d’une référence PMD**, pas de sprites natifs récupérés ni d’une nouvelle entrée officielle. Contrairement aux arbres/fleurs natifs de la livraison Amp Plains, les nouvelles roches, montagnes et nuages de cette proposition sont générés. Aucun ancien décor n’est remplacé.

## Contrôles et limites
`verify.py` contrôle toutes les phases des deux nuages contre les textures sources décalées modulo la largeur, le raccord de boucle, les tailles, l’absence d’overlay sur le guide d’approche, l’opacité des compositions, les PNG de contrôle, le nombre de phases WebP et la recomposition exacte ORA/PNG.

`GUIDE_APPROCHE_24PX.png` est un guide graphique de trajectoire sur le premier plan, **pas une carte de collisions ni la preuve que chaque pixel sous le guide est marchable**. Pas de test d’import PMDO, de perspective moteur, de collisions ou de changement de zone. La destination représentée est la grotte nord, pas une sortie hors cadre.

Reconstruction depuis la racine (Pillow, NumPy, SciPy) :
```sh
.venv/bin/python source/mont_horn_panorama_v1/build.py
.venv/bin/python source/mont_horn_panorama_v1/verify.py
```
Le builder utilise aussi `source/layouts_magenta_v1/palette.py`, fourni dans le ZIP. Le manifeste décrit les tailles, l’ordre des calques et les vitesses. Les ressources de référence PMD restent la propriété de leurs ayants droit.
