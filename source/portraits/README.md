# Portraits PMD — sources

- `reference/0870_Normal.png` : portrait Normal de Falinks publié sur PMDCollab (Emmuffin, PMDCollab_2), **inchangé**. `0870_credits.txt` est le fichier de crédits d'origine.
- `reference/0870_0001_Normal.png` et `0870_0001_Normal^.png` : forme chromatique et sa version retournée officielle, gardées comme référence de la convention `^` (le miroir y corrige le reflet du protège-nez).
- `build_portraits_falinks.py` : construit les 16 émotions par retouche pixel de la base, la planche SpriteBot 200 × 320, l'aperçu et le kit.
- `verify_portraits_falinks.py` : relecture indépendante (format, palette, conservation, miroirs, planche).

Sorties dans `portraits/falinks/`. Voir son README pour la méthode et la licence.
