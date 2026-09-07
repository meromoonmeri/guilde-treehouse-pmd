# Personnages PMD — sources

- `reference/0870/0002/` : sprite du **Brass** de Falinks publié sur PMDCollab (◥θ┴θ◤, PMDCollab_1), **inchangé** : `AnimData.xml`, `credits.txt`, 11 animations × Anim / Offsets / Shadow.
- `reference/0870/0003/` : sprite du **Trooper** (baronessfaron, CC BY-NC 4.0), **inchangé**, même structure.
- `build_falinks_sprite.py` : compose l'escouade complète (1 brass + 5 troopers) à partir des deux unités — lecture par rapport aux ancres, plan de formation par direction, pistes temporelles par unité, réassemblage des feuilles, `AnimData.xml`, Aseprite, variantes nuit, aperçus, `kit.json`, `credits.txt`.
- `verify_falinks_sprite.py` : relecture indépendante (règles du SpriteBot et de l'import SkyTemple + contrôles de composition), écrit `controle_qualite.json`.
- `reference/0812/` : sprite de **Rillaboom** publié sur PMDCollab (baronessfaron, CC BY-NC 4.0), **inchangé** : sert de squelette d'animation à Zarude (cases, durées, déplacements d'ancre, gabarit d'ombre).
- `zarude_pieces.py` : pièces de pixel art de **Zarude** (palette de 13 couleurs, bitmaps ASCII 1:1 pour cinq orientations, variantes de bras, effets).
- `build_zarude_sprite.py` : assemble les pièces en poses, applique le squelette de Rillaboom image par image, réassemble feuilles, `AnimData.xml`, Aseprite, nuit, aperçus, `kit.json`, `credits.txt`.
- `verify_zarude_sprite.py` : relecture indépendante (règles SpriteBot + squelette identique à la référence, miroirs exacts, rotation de Swing/Rotate, palette), écrit `controle_qualite.json`.

- `pmd_sprite.py` : **briques communes du format SpriteCollab** (lecture d'un dossier de sprite en cases repérées par rapport à l'ancre, écriture des feuilles, d'`AnimData.xml` et de l'Aseprite, index officiels, set complet). Partagé par les constructeurs ci-dessous.
- `reference/0186, 0241, 0282, 0297, 0424, 0443, 0674, 0685, 0702, 0923/` : sprites officiels des dix Pokémon demandés, **inchangés**, avec leurs `credits.txt`.
- `reference/0155/` : **Bayleef**, jeu Chunsoft complet — squelette de temps des animations de scène (durées, déplacements d'ancre, créneaux). `reference/0025/` : Pikachu, gardé comme second exemple de jeu complet.
- `build_animations_scenes.py` : ajoute aux dix Pokémon les **22 animations de scène** manquantes (Eat, Wake, Sit, Sink, Faint…) en replaçant leurs propres cases officielles sur le squelette de Bayleef. Sorties dans `personnages/<nom>/animations_scenes/`.
- `verify_animations_scenes.py` : relecture indépendante (règles SpriteBot + squelette identique, palette incluse dans celle du sprite d'origine, animations d'origine octet pour octet), écrit `controle_qualite.json`.
- `reference/zarude_fourni.png` : **planche fournie par l'utilisateur** (`IMG_4840.png`), 4 orientations × 4 images de 64 × 64, **inchangée**.
- `build_zarude_fourni.py` / `verify_zarude_fourni.py` : mise au format SpriteCollab de cette planche sur le squelette de Rillaboom, et son contrôle (chaque silhouette produite doit être une pose fournie au pixel près). Sortie dans `personnages/zarude_fourni/`.

- `METHODE_SPRITES_PMD.md` : **guide de méthode pour le prochain sprite** (format, récupération des références, ce qui a marché et échoué pour Falinks, exports attendus, marche à suivre pour un personnage sans base d'après Zarude, **§ 8 compléter un sprite officiel, § 9 compléter des portraits, § 10 intégrer un dessin fourni**).

Sorties dans `personnages/falinks/`, `personnages/zarude/`, `personnages/zarude_fourni/` et les dix `personnages/<nom>/animations_scenes/`. Voir leurs README pour la méthode, les cases et la licence.
