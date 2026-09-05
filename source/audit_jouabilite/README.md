# Audit de jouabilité et plan arrondi

## Décisions utilisateur

- RDC + trois étages.
- Conserver les accès extérieurs déjà prévus.
- Garder les contours **arrondis et organiques**, y compris dans les variantes.
- Les décors sont produits par le générateur d’images ; les scripts ne servent qu’aux plans techniques, mesures et post-traitements.

La proposition de chambre en L a été écartée après la correction utilisateur. Aucun natif de salle n’a été remplacé. La première trémie rectangulaire est conservée uniquement comme référence intermédiaire de la génération arrondie ; ne pas l’importer comme décor retenu.

## Reproduire l’audit

Depuis la racine du dépôt, avec les dépendances existantes :

```bash
python source/audit_jouabilite/mesurer_assets.py
python source/audit_jouabilite/etablir_plan.py
python source/audit_jouabilite/verifier_plan.py
python source/audit_jouabilite/preparer_tremie.py
python source/audit_jouabilite/construire_rapport.py
```

Avec Playwright et Chromium :

```bash
python source/audit_jouabilite/verifier_rapport.py
```

`PMD_CHROMIUM` permet d’utiliser un navigateur existant. Le dernier contrôle produit aussi le PDF et la planche PNG du schéma.

## Ce que ces scripts font — et ne font pas

- `mesurer_assets.py` : gabarits de pieds 16/24/32 px sur les masques existants, ombres/reflets présents et similarité des silhouettes. Aucune image de jeu modifiée.
- `etablir_plan.py` : affectation des 12 pièces aux quatre niveaux, neuf zones de circulation et 22 liaisons. Les trois recalages de points et trois recentrages de rectangles sont écrits **dans le plan**, pas appliqués silencieusement aux anciens fichiers.
- `verifier_plan.py` : unicité et réciprocité des accès, niveaux voisins, trémies complètes, arrivées sûres, points dans les zones d’action, conservation des arrondis et refus des anciens constructeurs procéduraux par défaut.
- `preparer_tremie.py` : post-traitement du prototype réellement généré, natif indexé, calques et masque de vide. Les ellipses servent à sélectionner des pixels et à définir une collision indicative, pas à peindre la trémie.
- `construire_rapport.py` : schémas SVG, rapport HTML hors ligne et laboratoire de gabarit. Les positions du schéma ne sont pas des coordonnées moteur.
- `verifier_rapport.py` : navigation, trajets, contrôle des trois recalages dans l’interface, gabarit déplaçable, mobile et fonctionnement en iframe.

Les résultats sont dans `plans/guilde_4_niveaux/`. Le graphe est validé ; les paliers/couloirs incomplets, l’extérieur jouable et l’intégration au moteur restent signalés comme travaux à réaliser.
