# Méthode pour la suite des donjons

Demande utilisateur : examiner le format PMDO/Audinowho et produire des variantes de tilesets existants ainsi que des matières inédites dans la même DA, notamment forêt/eau/sakura, avec leurs frames. Continuer la méthode référence réelle → génération guidée → reconstruction contrôlée, ne pas livrer des images de salles à la place des feuilles d’autotiles.

Audit effectué sur DtefImportHelper, AutoTileAdjacent, TileLayer/FrameTick, GraphicsManager et Program. Important : DTEF, pas EDTF ;47 cas en6×8 par type ; variantes0/1/2 distinctes des animations ; index de couche DTEF global à attribuer par cadence/type/index local, sinon collisions silencieuses avec Beach Cave. Alpha, coins et bordures protégés. Aucun import moteur exécuté.

Premier lot :6 prototypes,204 feuilles PNG importables via route DTEF selon le code audité. Trois recolorations natives et trois matières issues du générateur, intégrées dans les intérieurs de tuiles sur géométrie native conservée. Ce ne sont pas six tilesets entièrement originaux redessinés. Animations sources conservées (pas de nouvel effet de pétales/lucioles animé). Voir README rendu pour limites.

Galerie principale `apercu_dungeon_autotiles_v1.html` : animation live des piles indépendantes sur carte et gabarit, variantes, inspection frame individuelle. Archive RAW/TileDtef fournie. Tests fichiers/pixels et DOM simulé réussis. La prochaine étape est l’import dans une copie PMDO de test, puis les corrections artistiques avant d’étendre les matières inédites.
