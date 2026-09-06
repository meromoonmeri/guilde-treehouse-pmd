# Personnages PMD — sources

- `reference/0870/0002/` : sprite du **Brass** de Falinks publié sur PMDCollab (◥θ┴θ◤, PMDCollab_1), **inchangé** : `AnimData.xml`, `credits.txt`, 11 animations × Anim / Offsets / Shadow.
- `reference/0870/0003/` : sprite du **Trooper** (baronessfaron, CC BY-NC 4.0), **inchangé**, même structure.
- `build_falinks_sprite.py` : compose l'escouade complète (1 brass + 5 troopers) à partir des deux unités — lecture par rapport aux ancres, plan de formation par direction, pistes temporelles par unité, réassemblage des feuilles, `AnimData.xml`, Aseprite, variantes nuit, aperçus, `kit.json`, `credits.txt`.
- `verify_falinks_sprite.py` : relecture indépendante (règles du SpriteBot et de l'import SkyTemple + contrôles de composition), écrit `controle_qualite.json`.

- `METHODE_SPRITES_PMD.md` : **guide de méthode pour le prochain sprite** (format, récupération des références, ce qui a marché et échoué pour Falinks, exports attendus, plan pour un personnage sans base comme Zarude).

Sorties dans `personnages/falinks/`. Voir son README pour la méthode, les cases et la licence.
