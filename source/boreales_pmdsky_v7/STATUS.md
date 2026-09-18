# V7 — ciel boréal PMD Sky animé, frames de la référence elle-même

Demande : « non l'image référence c'est le ciel boréal dans pmd sky c'est animée subtilement » puis « non faut pas que ce soit du wrap mais que ce soit que des frame animée ». Les frames sont **l'image de référence `aurorepmdsky.png` elle-même**, pas un dessin nouveau et pas une bande qui défile.

## Méthode
- 24 frames de 120 ms (cycle 2,88 s). Chaque frame = référence modulée : **variation proportionnelle de luminosité (±7,5 % max)** sur les pixels du rideau, pilotsée par quatre champs gaussiens fixes en cosinus (périodes entières 1×, 2×, 3× +gradient). Frame 0 = **référence exacte** ; frame 24 = frame 0 ; aucune translation, aucun warp, aucun wrap, aucune rotation de teinte.
- Protections : zone des pics de glace et nuages d'horizon (lignes ≥ 157, fondu 144→157), étoiles détectées (faible saturation, lumineuses) — inchangées dans toutes les frames.
- Overlay : alpha extrait de la référence (distance au ciel de base, voile intérieur rempli à alpha 64, petites composantes enlevées), ×2 nearest (528×314), bords gauche/droit/bas fondus. Posé **une seule fois, position fixe** (x=120, y=0) dans la scène 768×512, entre ciel V3 et terrain. Son voile varie ±11 %.
- Le rythme et l'amplitude sont **choisis, pas extraits du jeu** (cycle officiel inconnu) ; calibrés subtils, conformément à la référence.

## Contenu
- `ciel/frames/CielPmdskyV7_000..023.png` : les 24 frames du ciel (264×216).
- `ciel/ciel_boreal_anime.webp` : WebP sans perte sur les couleurs visibles.
- `overlay/frames/OverlayPmdskyV7_000..023.png` + `overlay_anime.webp` : aurore seule transparente, pose fixe.
- `review/` : GIF 24 frames, scènes composées (frames 0, 8, 16), planche de frames.
- `calques/` : ciel/étoiles/terrain V3 copiés byte-identiques.
- Aperçu autonome `apercu_ciel_boreal_pmdsky_v7.html` (racine) : ciel ×3, overlay seul, scène sans wrap, frame par frame, comparaison avec l'original figé.

12 tests dédiés : frame 0 identique à la référence, aucun changement sous la zone d'aurore, étoiles intactes, subtilité (différences proportionnelles, pas de teinte), boucle fermée, WebP fidèle, overlay à position fixe sans wrap, recomposition exacte de la scène, calques V3 intacts, GIF 24×120 ms, manifeste. Aucun test navigateur interactif ni runtime PMDO. Référence © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft ; adaptation animée, pas pixels natifs du jeu ni cycle officiel extrait.

Rebuild : `.venv/bin/python source/boreales_pmdsky_v7/build.py` puis `package.py`.
