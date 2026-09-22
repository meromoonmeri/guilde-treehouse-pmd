# Installation PMDO (mod)
Copier dans le dossier du mod :
- `Data/Map/frozen_crucible.rsmap`
- `Content/Object/Ice_Peak_*.dir` (4 fichiers)
Prérequis : le tileset `Content/Tile/VastIceMountainPeak.tile` (asset PMDO de base, DumpAsset) et le BG `Steam.dir` (déjà dans le jeu / New-Era V5).
Puis dans un script : `GAME:EnterGroundMap("frozen_crucible", "entrance")` ou via l'éditeur de sol (Ground Editor → Load frozen_crucible).
Seuls les TileTex, les AnimIndex des 8 décorations, la couleur de brume et le nom changent par rapport à `searing_crucible.rsmap` ; entrée, équipes, musique, scripts intacts. Non testé en moteur.
