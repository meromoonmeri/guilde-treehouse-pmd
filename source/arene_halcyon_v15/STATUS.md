# V15 — zone générée (méthode canonique) convertie aux critères Halcyon/Palika

Demande : « Utilise la méthode canonique de création de map avec ton générateur d’image et les animations boréal. Plusieurs frames d’ondulation. Convertir la zone dans les critères de Halcyon Palika. »

## Méthode canonique
- `bruts/terrain_complet.png` : terrain **généré plein cadre** (928×1152) avec bande magenta en haut — pas de collage de morceaux.
- Alpha par **inondation du magenta depuis le haut** : ciel transparent, paysage complet conservé (y compris les pointes de pics qui dépassent dans la bande — testé : zéro magenta résiduel opaque).

## Ondulations boréales générées
- `bruts/boreale_ondulations_8.png` : planche 2×4 générée (même rideau, vague qui monte/descend, palette canonique PMD Sky).
- 8 frames extraites : `couches/aurore/AuroreV15_00..07.png`, **toutes exactement 768×256**, 8 × 150 ms = 1,2 s, boucle (IoU adjacent > 0,55 testé : même rideau, poses différentes).

## Critères Halcyon/Palika
- Calques fixes empilés : `ciel_fixe.png` (navy uniforme) → `etoiles_fixes.png` → aurore (8 frames) → `terrain_fixe.png`.
- **Position sur grille 8 px** : aurore posée à (80, 24). Nommage uniforme, taille uniforme, durée uniforme par frame. Aucun wrap.
- `manifest.json` : grille, ordre des calques, SHA des bruts. Viewer `apercu_arene_halcyon_v15.html` (calques togglables, frame par frame), GIFs, WebP, ZIP.

8 tests dédiés PASS : provenance SHA, terrain canonique sans magenta résiduel, frames uniformes 768×256 + grille 8 px, ondulation réelle, calque sans ciel, scène recomposée exacte, WebP/GIF 8×150 ms, manifeste. Pas de test navigateur ni runtime PMDO. Généré d’après la référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft ; poses et cadence : nos choix.

Rebuild : `.venv/bin/python source/arene_halcyon_v15/build.py` puis `package.py`.
