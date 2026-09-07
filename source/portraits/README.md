# Portraits PMD — sources

- `reference/0870_Normal.png` : portrait Normal de Falinks publié sur PMDCollab (Emmuffin, PMDCollab_2), **inchangé**. `0870_credits.txt` est le fichier de crédits d'origine.
- `reference/0870_0001_Normal.png` et `0870_0001_Normal^.png` : forme chromatique et sa version retournée officielle, gardées comme référence de la convention `^` (le miroir y corrige le reflet du protège-nez).
- `build_portraits_falinks.py` : construit les 16 émotions par retouche pixel de la base, la planche SpriteBot 200 × 320, l'aperçu et le kit.
- `verify_portraits_falinks.py` : relecture indépendante (format, palette, conservation, miroirs, planche).

- `reference/0186, 0297, 0424, 0923/` : portraits officiels de Politoed, Hariyama, Ambipom et Pawmot publiés sur PMDCollab, **inchangés**, avec leurs `credits.txt`.
- `build_portraits_manquants.py` : complète leurs planches à 16 émotions — fond Chunsoft repeint par détection du décor, yeux transformés par opérations sur leurs propres couleurs, effets de la palette du kit ; produit les versions `^`, la planche SpriteBot 200 × 320, l'aperçu, les repères et le kit.
- `verify_portraits_manquants.py` : relecture indépendante (format, 15 couleurs, planche, miroirs exacts, émotions officielles reprises à l'identique, personnage inchangé hors des zones déclarées).

Sorties dans `portraits/falinks/`, `portraits/politoed/`, `portraits/hariyama/`, `portraits/ambipom/` et `portraits/pawmot/`. Voir leurs README pour la méthode et la licence.
