# Personnages PMD — sources

- `reference/0870/0002/` : sprite du **Brass** de Falinks publié sur PMDCollab (◥θ┴θ◤, PMDCollab_1), **inchangé** : `AnimData.xml`, `credits.txt`, 11 animations × Anim / Offsets / Shadow.
- `reference/0870/0003/` : sprite du **Trooper** (baronessfaron, CC BY-NC 4.0), **inchangé**, même structure.
- `build_falinks_sprite.py` : compose l'escouade complète (1 brass + 5 troopers) à partir des deux unités — lecture par rapport aux ancres, plan de formation par direction, pistes temporelles par unité, réassemblage des feuilles, `AnimData.xml`, Aseprite, variantes nuit, aperçus, `kit.json`, `credits.txt`.
- `verify_falinks_sprite.py` : relecture indépendante (règles du SpriteBot et de l'import SkyTemple + contrôles de composition), écrit `controle_qualite.json`.
- `reference/0812/` : sprite de **Rillaboom** publié sur PMDCollab (baronessfaron, CC BY-NC 4.0), **inchangé** : sert de squelette d'animation à Zarude (cases, durées, déplacements d'ancre, gabarit d'ombre).
- `reference/zarude/` : **planche de marche de Zarude fournie par le commanditaire** (`zarude_overworld_2x.png`, Game Character Hub, 4 directions × 4 images au double) et sa réduction 1:1 `zarude_overworld_1x.png`, **inchangées** : source du dessin.
- `zarude_pieces_from_sheet.py` : découpe la planche en pièces pixel-exactes (tables `R(y, x0, x1)`) et y ajoute les pièces dessinées (diagonales, bras des animations, sommeil, effets) ; écrit `zarude_pieces.py`.
- `zarude_pieces.py` : pièces de pixel art de **Zarude** (généré ; 11 couleurs, bitmaps ASCII 1:1).
- `build_zarude_sprite.py` : assemble les pièces en poses, applique le squelette de Rillaboom image par image, réassemble feuilles, `AnimData.xml`, Aseprite, nuit, aperçus, `kit.json`, `credits.txt`.
- `verify_zarude_sprite.py` : relecture indépendante (règles SpriteBot + squelette identique à la référence, miroirs exacts, rotation de Swing/Rotate, palette), écrit `controle_qualite.json`.

- `METHODE_SPRITES_PMD.md` : **guide de méthode pour le prochain sprite** (format, récupération des références, ce qui a marché et échoué pour Falinks, exports attendus, marche à suivre pour un personnage sans base d'après Zarude).

Sorties dans `personnages/falinks/` et `personnages/zarude/`. Voir leurs README pour la méthode, les cases et la licence. Les sprites **Dynamax** (toutes les espèces de SpriteCollab) et leur VFX de transformation sont un chantier à part : sources dans [`source/sprite/`](../sprite/README.md), sorties dans `sprite/`.
