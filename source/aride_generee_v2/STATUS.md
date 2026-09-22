# Aride generee V2 — entree de donjon desertique (map finale)

Demande : reprendre les textures ET les layers au generateur pour assembler
une map finale, guidee par `entrancearidedungeonpmdsky.png`. Une seule map
soignee + animation proposee. PAS de mosaïque de pixels natifs.

## Bruts (4 generations)
- `bruts/parois_grotte.png` (1200x896) : massif canyon + bouche a gauche + strip sable
- `bruts/sol_sable.png` (1224x864) : sable plein cadre, sentier clair, cailloux
- `bruts/props_arbres_blocs.png` (1224x864) : 8 props isoles (2 grands, 2 moyens,
  2 arbustes, 2 blocs) — mieux que demande (2 arbustes + 1 bloc suppl.)
- `bruts/fx_poussiere.png` (1224x864) : 3 volutes horizontales

## Pipeline (build.py)
Downscale /3 BOX (400x298 parois, 408x288 autres) -> detourage magenta par
seuil global d<170 (aucun rose interieur, tous les materiaux a d>300) +
pelage de 2 anneaux d<230 + recopie voisin -> quantification 128 couleurs ->
assemblage 400x360 (grille 8 px), raccord dithere Bayer 8 (y220-236) entre le
seuil de la paroi et le sol, plafond noir echantillonne dans la bouche.

Lecons : le seuil serre d<48 (V16) laissait la frange magenta cuite des
contours (d 100-230) ; le seuil global large est sur ici. Ne pas reappliquer
le mapping `order` arbuste/bloc : le tri (rangee, x) donne deja le bon ordre.

## Animation proposee (pas un cycle officiel)
3 bandes, derive horizontale wrap 48/72/36 px par cycle (4/6/3 px par frame),
12 frames x 100 ms, scintillement alpha 150+-25 sinusoidal. Boucle parfaite
verifiee (decalages entiers + periode du sinus). Mouvement mesure : 8,5 % des
pixels bougent entre f0 et f6.

## Livrables (renders/aride_generee_v2/ + ZIP + galerie racine)
12 couches (plafond, sol, parois, 8 props pieds sur grille 8 px), 12 frames FX,
12 composites, GIF + WebP, ORA editable, composite, access_review
(arrivee [185,356] -> seuil [130,203], degagement 8 px teste), manifest.json.
8 tests PASS. Galerie `apercu_aride_generee_v2.html` (calques, lecture, acces).

## Limites
Textures generees DA PMD, pas pixels natifs ; bouche/cadence choisies ;
pas de test PMDO/GPU ; collisions + warp grotte a configurer moteur.
Rebuild : build.py puis package.py (tests avant ZIP).
