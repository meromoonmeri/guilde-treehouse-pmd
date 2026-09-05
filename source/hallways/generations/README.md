# Nouvelle méthode : génération d’images, pas dessin procédural

**Statut : première galerie générée traitée selon le workflow du kit d’origine.** Son natif, ses 11 emplacements de calques (5 utiles), ses versions jour/nuit et ses exports sont dans `tilesheets/generes/galerie_est_ouest/`. Les huit autres modules ne sont pas encore remplacés.

Le choix de fabriquer les décors par `build_hallways.py` a été rejeté par l’utilisateur. Ce constructeur correspond désormais à l’ancienne approche ; ne pas le réutiliser pour prétendre produire les nouveaux couloirs générés.

## Images réellement générées

- `galerie_est_ouest_brute.png` : première génération avec les intérieurs natifs 05/12 comme références de DA. Elle comporte un petit podium et une bordure trop massive.
- `galerie_est_ouest_retenue.png` : correction **par le générateur d’images** ; podium supprimé, plancher continu, branches périphériques réduites. C’est la proposition affichée, pas une validation utilisateur acquise.
- `provenance.json` : outils, références, prompts et statut des essais.

Une tentative de planche de neuf modules et un essai de coude ont été écartés : leurs sorties ne respectaient pas suffisamment la géométrie demandée. Ils ne sont pas intégrés aux livrables.

## Post-traitement limité à l’export

`exporter_proposition.py` retire le fond magenta et prépare un aperçu sur fond sombre. Il ne dessine ni plancher, ni mur, ni végétation, ne redimensionne pas l’image et ne repeint pas les pixels conservés.

Fichiers affichables :

- `tilesheets/propositions_generees/galerie_est_ouest.png` : image détourée ;
- `tilesheets/propositions_generees/galerie_est_ouest_apercu.png` : aperçu de la génération ;
- `tilesheets/propositions_generees/controle_proposition.json` : traitements effectivement réalisés.

Le traitement de la première galerie est maintenant assuré par `exporter_methode_origine.py` : natif indexé, détourage, segmentation et masques de sélection figés, extraction d’une partie des ombres existantes, nuit par palette et exports Aseprite/Tiled 8 px. `verifier_methode_origine.py` relit les fichiers. Les masques ne servent jamais à dessiner le décor. Les autres formes de couloirs et leur intégration au pack restent à faire.
