# Arène générée V2 — retour à la méthode demandée

L’utilisateur corrige explicitement : utiliser la méthode des anciens rendus générés, **pas des bouts de maps assemblés**. Ce lot remplace donc la proposition de terrain `exports/ice_arena_aurora_v1`, sans effacer les anciennes ressources.

## Méthode réellement employée

Référence de workflow : `source/layouts_magenta_v1/WORKFLOW.md`, son `build.py`, et le terrain magenta des rendus Northern.

1. Génération d’un **seul décor complet cohérent** sur magenta : `bruts/terrain_magenta.png`. Les références de matière sont l’arène de glace PMD et l’ancien rendu Northern ; elles ne sont pas découpées puis collées dans le terrain final.
2. Nouvelle génération du **sol complet sous les reliefs** : `bruts/sol_complet.png`. Pas de remplissage à partir d’un petit échantillon répété.
3. Normalisation des images générées à512×640, nearest-neighbor, détourage et alpha binaire. Cette normalisation concerne les générations, pas les aurores canoniques.
4. Séparation alignée en sol complet, sol visible, chemin sud, reliefs arrière, reliefs avant gauche/droit et petits reliefs. La recomposition restitue exactement le terrain généré normalisé/détouré.
5. Ajout séparé du fond : ciel, brume, aurores et étoiles. Les deux animations précédentes sont conservées byte-identiques ; **leur mouvement était une création proposée sur le dessin canonique, pas un cycle original du jeu récupéré**.

Le terrain est redessiné d’après les matières PMD : **pas certifié pixel-exact canonique**. L’expression « textures canoniques » ne sert pas ici à masquer une génération ou à justifier un nouveau collage. Les masses et leurs ombres sont conçues ensemble par le rendu.

## Livrables

- Galerie `apercu_arene_glace_generee_v2.html` : scène animée, pause/lecture, sélection d’étape et visibilité des calques.
-7calques de terrain et2calques de fond statiques, PNG512×640 ;128PNG d’aurores/étoiles264×216.
-64étapes,100ms chacune, boucle6,4s ; GIF à palette réduite et WebP sans perte. Le GIF utilise des rectangles différentiels vérifiés, sans répétition inutile du terrain complet à chaque étape.
-`arene_generee_editable.ora` : plans alignés, fond et phase0 de l’animation, éditables. Les séquences animées restent dans leurs dossiers PNG.
-Masques de séparation, deux générations brutes, manifeste et vérification.

Les reliefs sont des **plans de profondeur d’une composition cohérente**. Le sol caché est généré ; les faces arrière cachées des falaises ne sont pas complétées pour déplacer chaque masse librement. La séparation reste éditable dans l’ORA. Pas de collision, warp ou importPMDO/Tiled validés.

11tests dédiésPASS. Art à examiner. Autres zones et programme guilde non déclarés achevés. Références natives PMD et leurs ayants droit respectifs ; terrain nouvellement généré, sans prétendre l’avoir extrait du jeu.
