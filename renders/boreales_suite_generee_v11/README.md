# V11 — suite boréale passée au générateur, calque propre sur notre ciel

Demande : « Passe les dans le générateur pour que les boréal et une suite d’animation subtile sur son propre layer pour le mettre sur notre ciel de notre zone ».

## Génération avec les deux références
Planche générée (`bruts/boreal_suite_8.png`, 2×4) avec **la texture canonique** `aurorepmdsky.png` (formes/palette des rubans) **et notre ciel de zone V3** (harmonisation des interstices navy) : 8 poses, mêmes rubans aux mêmes positions, seuls les cœurs battent légèrement et un shimmer voyage (frame 8 ≈ frame 1).

## Extraction sans ciel cuit (méthode géométrique)
La distance de couleur échouait ici : les cœurs magenta des rubans sont trop proches du magenta de fond (franges roses résiduelles, fissures conservées, cœurs affaiblis). Extraction retenue : **le fond est la zone connexe aux bords** (inondation depuis les 4 bords sur magenta-like + navy sombre cuit) ; trous internes **navy** enfermés → voile opaque (corps des rubans, harmonisé à notre ciel) ; fissures **magenta** enfermées → laissées transparentes ; petites composantes retirées ; démelage doux contre le magenta ; recadrage ; calque 768×300 centré, bords fondus. **Aucun panneau navy cuit de fond, aucune frange rose.**

## Suite animée sur son propre layer
16 étapes × 120 ms = 1,92 s : 8 poses pures (étapes paires) + 8 fondus 50 % (étapes impaires). Positions verrouillées (testé : bounding boxes à < 18 px), variations subtiles réelles, boucle exacte. Posé **une fois** à (0,0) entre ciel+étoiles V3 et glace V8 + terrain V3 (byte-identiques, dans `contexte/`). Aucun wrap.

## Livrables
`poses/` (8 PNG), `couches/` (16 PNG), `boreale_suite_16frames.webp` (transparent), `review/` (planche, GIF scène 384×256, GIF suite seule), scènes 0/4/8/12, aperçu autonome `apercu_boreale_suite_generee_v11.html` (racine), ZIP `renders/boreales_suite_generee_v11_pack.zip`.

9 tests dédiés : provenance planche, 8 poses/16 étapes, positions verrouillées + variation réelle, fondus 50 % exacts, boucle exacte, bords propres sans magenta résiduel, scène recomposée + contexte byte-identique, WebP/GIF fidèles (16×120 ms), manifeste. Pas de test navigateur interactif ni runtime PMDO. Suite dessinée par génération (références canonique + notre ciel) — pas le cycle officiel du jeu. © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.

Rebuild : `.venv/bin/python source/boreales_suite_generee_v11/build.py` puis `package.py`.
