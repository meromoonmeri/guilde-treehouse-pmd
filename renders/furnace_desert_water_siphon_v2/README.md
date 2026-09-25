# Furnace Desert — massif spacieux, bassin et siphon V2

## Correction artistique

Le premier essai est rejeté : il redessinait trop librement la roche et agrandissait excessivement le siphon.

Cette V2 conserve réellement le cœur de la référence : **89 858 pixels non-sable de la roche, de la grotte/ouverture, des coulées et des rochers avant sont protégés sans aucune différence**. La montagne est rendue plus spacieuse uniquement par prolongement latéral sur une toile plus large.

Le sable est remplacé par un bassin d'eau bleu. Le tourbillon de sable devient un siphon d'eau compact, centré en `(384,222)` et ciblé autour de 90 px de diamètre.

## Livrables

- `COMPOSITION.png` — scène corrigée 768×480, compatible grille 8 px ;
- `REFERENCE.png` — référence utilisée ;
- `GUIDE_MAGENTA.png` — référence protégée sur la toile d'extension ;
- `COMPARAISON.png` — référence et nouvelle composition côte à côte ;
- `manifest.json` et `verification.json`.

## Portée honnête

Les prolongements latéraux, l'eau et le siphon sont générés en suivant la référence. Le cœur rocheux central est protégé pixel pour pixel. Ce rendu n'est pas encore un Ground PMDO, ne contient pas de collisions et n'a pas été testé en runtime. L'approbation artistique reste à faire.
