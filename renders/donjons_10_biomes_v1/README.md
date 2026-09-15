# Dix biomes de donjon — planches personnalisées V1

Forêt, jungle, marais, grotte rocheuse, cristal, glace, volcan, désert, ruines et grotte vapeur Steam Cave. Chaque biome possède ses **matières propres**, pas une simple recoloration d’un même dessin.

## Par biome
- 12 variantes de sol24×24.
- 47 cas de voisinage de murs ×2 variantes de bordure/matière =94 cellules24×24.
- 47 cas de terrain animé ×4 phases. Eau pour plusieurs biomes ; magma pour volcan ; terrain mouvant stylisé pour désert. Animations procédurales, pas des cycles natifs récupérés.
- 1 obstacle48×48 et son miroir horizontal : **2 orientations, pas deux objets distincts**.
- Versions jour et nuit exacte Abyss.
- Démonstration576×432, quatre salles reliées,4calques alignés,4poses, PNG/WebP/ORA.

Les dix démonstrations emploient volontairement le même plan pour comparer les matières. Ce sont des cartes de test, **pas dix zones complètes aux layouts différents**. La zone Steam Cave avec geysers est une livraison séparée.

## Provenance
Neuf planches originales générées en pixel art PMD, puis matières réduites au plus proche voisin et assemblées en variantes de connectivité. Les bruts sont dans `bruts/` ; les trois matières96×96 utilisées sont conservées dans chaque dossier biome.

Le générateur a atteint sa limite de10images pour ce tour (une réparation Waterfall Lake + neuf biomes). Le dixième biome, vapeur, utilise des **crops non redimensionnés** de `Steam_Cave_Peak_TDS.png` : sol(280,360–376,456), sommet(16,128–112,224), face(32,256–128,352). La bouche de geyser est dessinée séparément. Références également inspectées : `Steam_Cave_entrance_TDS.png`.

Ces planches personnalisées **ne sont pas des tilesets canoniques extraits du jeu**. Les matières générées ne doivent pas être présentées comme des pixels natifs. Les bords/raccords sont construits par masques, même pour vapeur.

## Organisation/import
- Noms uniques `d10_<biome>_<jour|nuit>_*` pour éviter les collisions de basenames.
- Un module logique fait24×24pixels, soit3×3tuiles PMDO de8px. Dans PNG to Tileset, choisir **8px** ; garder l’assemblage logique24px documenté.
- Feuilles sur8colonnes : index de cellule = ligne×8+colonne. Les cas muraux sont ordonnés par `connectivite_47.json`, première variante aux indices0–46, seconde47–93. Les cellules restantes d’une dernière ligne sont vides.
- Bits N1,E2,S4,W8,NE16,SE32,SW64,NW128. Une diagonale n’est retenue que si ses deux voisins cardinaux existent. Le JSON fournit les47masques et leur ordre.
- `layout_demo.json` documente le sol logique et les terrains à risque. Les obstacles nécessitent leurs collisions dédiées.

**La configuration d’autotiles, d’animation et de collisions dans PMDO n’est pas installée par ce pack.** Le mapping JSON sert de documentation, ce n’est pas un fichier DTEF/PMDO prêt à charger. Les compositions de test utilisent le générateur de variantes Python fourni.

## Contrôles
`verification.json` :80compositions de biomes,20ORA, dimensions divisibles par8,94cellules murales présentes par biome, raccords alpha partagés vérifiés sur les47cas dans les deux variantes, filtre nocturne exact et sol logique de démonstration connecté hors dangers. Cela ne constitue pas une preuve de perfection artistique des jointures ni de collisions des objets.

**Aucun lancement PMDO ni test d’échelle moteur réalisé.** L’importeur et les collisions restent à valider dans l’éditeur.

Scripts : `source/donjons_10_biomes_v1/{build,verify_all,package}.py`. Dépendances Pillow/NumPy/SciPy. Reconstruction depuis le dépôt ; le ZIP compact contient les exports utiles, la galerie à liens relatifs et les scripts. Les bruts et séquences PNG aplaties complètes restent dans le dépôt ; le ZIP conserve les animations, compositions principales et tous les calques, mais pas toutes les anciennes références/dépendances.
