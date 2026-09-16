# Méga-Évolution — travail en cours

Références conservées pour éviter une nouvelle perte entre étapes.
- SpriteCollab 3609a86be2a4c8ad7cf255bd2255f044daafe24f : sprite/0006 et sprite/0006/0001 (Dracaufeu → Méga X). Crédits originaux dans chaque dossier. Ces œuvres ne sont pas de nouvelles créations.
- audinowho/DumpAsset : Data/Skill/aurora_beam.json, Content/Beam/Column_Blue.beam, Column_Green.beam, Column_Pink.beam. Les colonnes sont la référence demandée ; Aurora_Beam_Custom.dir représente des anneaux.
- Animation custom indépendante des contraintes de palette/alpha des personnages.

Aucune intégration PMDO ni approbation artistique n'est encore validée. Les fichiers de référence de personnages ne contiennent que Idle (XML natif complet conservé comme référence, pas comme export jouable).

## Premier rendu reconstruit

Exécuter `.venv/bin/python source/mega_evolution_v1/build.py` (Pillow et NumPy).
Exports : `renders/mega_evolution_v1/`, 6 atlas RGBA 3072×3072, cellules 256×256, 12×12, lecture de gauche à droite puis ligne suivante, 2 ticks par phase. Noms uniques `MEGA_V1_*`. **Ce sont des atlas source VFX : ne pas importer via PNG to Tileset comme un décor.** Le format d'import d'animation et le raccordement moteur restent à réaliser.

Ordre : sol → éclairs arrière → personnage → sphère → éclairs avant → fragments → emblème. Le switch de forme est un événement de la timeline à la phase 66, pas inclus dans les atlas. La démo compose les véritables Idle natifs sans les recolorer. Calcul d'enveloppe depuis les marqueurs blancs de chaque frame ; couverture opaque testée pour les deux formes, les huit directions et les quatre poses Idle.

Points non terminés : emblème flamme/S redessiné (référence visuelle du motif dans un logo fan consulté, pas extraction officielle), raccord des fissures aux cellules de fracture à affiner, aucun test Ground/Dungeon, ni liste entière X/Y/Z-A mesurée. Les références Onde Boréale sont conservées mais les éclairs sont un dessin original, pas l'animation native réexportée. Ne pas annoncer ce prototype comme finition de l'ensemble du mandat.

## Correction après inspection

La sphère utilise maintenant des bandes arc-en-ciel avec ombrage de volume au lieu des secteurs angulaires. Les 20 fragments proviennent réellement des pixels de la coque opaque (partition de Voronoï), se séparent puis rétrécissent et perdent leur opacité. Des particules prennent le relais. L’emblème en simple double hélice du premier checkpoint a été remplacé par le motif flamme/S avec point inférieur, redessiné en pixels après inspection du symbole présent dans le logo fan `image-search/mega-evolution-icon-1.png`. Cette référence secondaire ne prouve pas une reproduction pixel-exacte de l’icône officielle.

`verify.py` contrôle les dimensions des six atlas, les débuts/fins transparents et les 144 phases des huit aperçus. Les assertions de couverture opaque sont exécutées dans `build.py`.
