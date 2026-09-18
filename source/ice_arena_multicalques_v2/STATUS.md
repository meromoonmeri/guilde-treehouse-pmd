# Arène de glace V1 → 5 calques + boréal animé (repassée au générateur)

Demande : « repasse la zone au générateur pour décomposer la map en plusieurs layout, résultat identique à la référence : terrain / bordure / cliff / sky / boréal », avec le boréal qui change de couleur et une légère ondulation.

Méthode (conforme à la règle « le générateur fournit le guide, jamais les pixels ») :
- Le générateur a produit une **carte sémantique plate** `generation/layer_masks_guide.png` (5 couleurs index : rouge=terrain, vert=bordure, bleu=cliff, noir=ciel, magenta=boréal), même composition et silhouettes que la référence.
- Cette carte sert uniquement à **affecter chaque pixel de la référence** à un calque ; le ciel/boréal du haut est séparé programmatiquement (détection d'aurore saturée), la région de glace est découpée terrain/bordure/cliff par la carte. Les pixels des calques sont donc ceux de la référence : **le composite recompose exactement `layout_guide.png`** (vérifié, `reconstruction_exact: true`), géométrie jamais régénérée.

Calques livrés (`exports/ice_arena_multicalques_v2/layers/`) : `ciel` (ciel+étoiles+horizon), `boreal` (aurores), `terrain` (neige praticable/clairière/chemin), `bordure` (anneau de rochers+fractures), `cliff` (pics et parois de glace). Comptes de pixels dans `verification.json`.

Boréal animé : cyclage de teinte (1 tour/boucle) + ondulation transversale légère (amplitude ≤2 px, périodes entières, boucle fermée, frame 0 = aurore de la référence). 24 frames @120 ms, WebP sans perte + GIF + `scene_animee.gif`. C'est une animation d'art généré, pas le cycle officiel du jeu.

Aperçu autonome `apercu_arene_glace_calques_v2.html` : cases d'activation des 5 calques + animation. ZIP livré à côté.

Contrôles (`test_build.py`, 6 PASS) : reconstruction exacte, partition disjointe couvrant tous les pixels, pixels des calques = pixels de la référence, alpha binaire, frame0=boreal et changement de couleur, amplitude d'ondulation ≤2 px. **Pas de test navigateur interactif ni d'import/runtime PMDO.**

Reconstruire : `.venv/bin/python source/ice_arena_multicalques_v2/build.py` puis `test_build.py`.
