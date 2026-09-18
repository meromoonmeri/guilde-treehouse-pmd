# Glacier Cliff Aurora v2 — guide de composition en couches

Ce dossier est un **guide visuel généré**, pas un tileset PMDO et pas une
texture native. Le fond magenta `#ff00ff` sert uniquement à séparer les
couches avant une composition ou une retouche manuelle.

La scène suit le layout demandé :

1. ciel nocturne ;
2. aurore boréale ;
3. montagnes enneigées au loin ;
4. forêt et arbres enneigés en contrebas ;
5. arène de glace au sommet ;
6. falaises et rebords au premier plan ;
7. chemin d’accès sud.

Les images de référence canoniques ont été fournies au générateur :
`iceroadpmdsky.png`, `pmdskyicearena.png`, `path.png`, `snow.png`,
`bgnightbackgroundpmdskyda.png`, `aurorepmdsky.png` et
`forêtglomypmdsky.png`.

Les fichiers de `layers/` peuvent servir à vérifier la composition et les
masques, mais **ne doivent pas remplacer** `VastIceMountain.tile` ni les
`.dir` canoniques du package PMDO. La carte jouable et ses collisions restent
dans `exports/glacier_cliff_aurora_pmdo_v1/`.
