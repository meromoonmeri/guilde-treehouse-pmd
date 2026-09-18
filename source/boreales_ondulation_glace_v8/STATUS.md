# V8 — arène de glace : aurore ondulante générée + glace latérale

Demandes : « Faut de la glace sur les zones grises de la map sur les côtés, on dirait l'arène est dans le vide » ; « le ciel boréal doit être animé comme des ondulations générées » ; « suis la méthode habituelle sans la changer ».

## Méthode habituelle appliquée
1. **Planches générées** avec fond magenta : `bruts/aurore_ondulations_8.png` (8 poses, référence de style) puis `bruts/aurore_ondulations_8_haut.png` (utilisé, rideaux remplissant la hauteur). `bruts/glace_laterale.png` : parois et plaine sans arène, bande magenta en haut.
2. **Extraction alpha** : distance au magenta (255,0,255), défringement rose sur les bords semi-transparents, nettoyage alpha 0.
3. **Calques séparés** : ciel V3 (byte-identique) → **aurore 768×256** → **glace 768×512** → terrain V3 (byte-identique). Aucun wrap, aucun défilement.
4. Scène 768×512, viewer autonome, tests, ZIP, commit/push.

## Aurore ondulante
- 8 poses dessinées générées (planche 2×4). Les cases débordant horizontalement, l'extraction se fait en **colonne unique** : fenêtre verticale de 305 px centrée sur le centroïde de chaque case (la vague traverse la case à des hauteurs différentes), marges latérales de 30 px, redimensionnement nearest 768×256, colonnes de bord mises à zéro.
- **32 étapes × 125 ms = 4,0 s** : 4 fondus prémultipliés par paire de poses (0/25/50/75 %), frame 0 = pose 0 pure, dernière étape à 25 % pose 7 + 75 % pose 0 : boucle fermée. Ondulation verticale des crêtes/creux, **translation horizontale nulle** (testée).

## Glace latérale
Panneau généré (montagnes de glace à gauche/droite, plaine basse au centre-fond, palette du terrain), posé derrière le terrain : **plus de zones grises**, l'arène est adossée à un paysage. Statique, position (0,0).

## Livrables
`aurore/poses/` (8 PNG), `aurore/frames/` (32 PNG + WebP transparent 32 frames), `calques/` (glace + V3 intacts), `review/` (scènes 0/8/16/24, GIF scène 32 frames — granularité GIF 120 ms, cycle réel 3,84 s —, planche des 8 poses), `apercu_arene_ondulation_glace_v8.html` (racine) : scène, aurore seule, calques togglables, frame par frame.

10 tests dédiés : provenance brute, poses 768×256 sans translation, fondus prémultipliés exacts, boucle fermée, glace remplissant les côtés et libre en haut, recomposition exacte de la scène, calques V3 intacts, WebP fidèle, GIF 32 frames, manifeste. Pas de test navigateur interactif ni runtime PMDO. Dessins et rythme choisis — pas le cycle officiel du jeu. Référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.

Rebuild : `.venv/bin/python source/boreales_ondulation_glace_v8/build.py` puis `package.py`.
