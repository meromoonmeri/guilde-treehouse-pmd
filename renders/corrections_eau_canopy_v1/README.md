# Corrections : eau intégrale et cadre de canopée

Ces trois scènes remplacent les propositions mal interprétées, sans supprimer les anciens fichiers.

- **eau_integrale_rochers_gris** — 456×384. Toute la surface anciennement sableuse devient de l’eau. Les anciens calques de sol, raccord jaune et ombres sur sable ne sont pas utilisés. Rochers gris bleutés en trois calques, ombres sur eau séparées. Surface d’eau : 12 PNG à 120 ms ; siphons : 6 PNG à 60 ms. Boucle commune : 1440 ms, 24 compositions PNG à 60 ms et WebP animé.
- **foret_mousse_canopy**, **foret_emeraude_canopy** — 504×480. Masses de feuillage au premier plan sur toute la périphérie latérale, et non les anciens petits rameaux. Deux calques gauche/droite au-dessus des cinq calques de base. Bande centrale de 100 px libre sur toute la hauteur ; accès et chemin existants conservés.

## Origines et méthode

Les quatre layouts antérieurs issus de référence → génération sur magenta → alpha → calques ne sont pas régénérés. Cette correction réutilise leurs calques.

Pour le cadre, la référence nouvellement fournie `Southern_Jungle_entrance_S.png` au commit `46e93da` permet une extraction directe, plus fidèle qu’une nouvelle génération : deux tons sombres (7,31,23 / 7,39,23), composantes reliées aux bords, alpha puis contrôle sur magenta. Hauteur adaptée de 432 à 480 px en nearest-neighbor ; couleurs légèrement accordées aux deux palettes. `canopy_source_alpha.png` conserve la découpe aux dimensions source. Pas une bibliothèque d’arbres complets ni une nouvelle illustration officielle.

La plaque `bruts/eau_surface.png` est générée par IA, guidée par la palette et le style de `Underground_Lake_shore_TDS.png`, également fourni au commit `46e93da`. Elle couvre toute la scène : aucune clé magenta n’est nécessaire pour ce fond opaque. Réduction nearest-neighbor, palette limitée, nouvelle modulation douce des reflets en 12 phases. Les 6 phases des siphons sont les adaptations déjà créées à partir du cycle natif de sable, copiées sans changement. **Ce ne sont pas des animations natives d’eau récupérées.** Les animations restent séparées des rochers et des ombres.

## Fichiers et utilisation

Chaque scène contient `COMPOSITION.png`, un `.ora` multicouche et des PNG aux noms uniques. Les ORA contiennent la phase zéro de chaque groupe animé ; toutes les phases séparées sont disponibles en PNG. L’ordre de composition est : surface d’eau → siphons → ombres → rochers ; pour la forêt : cinq calques de base → canopée gauche → canopée droite.

Galerie autonome : `apercu_corrections_eau_canopy_v1.html` à la racine, avec animation, pause et sélection des calques. ZIP : `CORRECTIONS_EAU_CANOPY_calques.zip`, limité à ces trois scènes, aux deux découpes du cadre et aux documents. Les précédentes variantes, les nouvelles références et Sakura sont conservées.

## Vérifications et limites

`source/corrections_eau_canopy_v1/build.py` reconstruit les livrables (Pillow, numpy, scipy). Tests : opacité, recomposition ORA exacte, 24 compositions animées distinctes, corridor libre. `verify.py` vérifie aussi la recomposition de chaque phase depuis les PNG sauvegardés, la conservation des siphons, l’absence de pixels sableux chauds et la continuité de la modulation d’eau, y compris à la jonction de boucle.

Pas de test PMDO, collisions, gameplay, import tileset ou GPU. L’animation est un effet visuel adapté/reconstruit. Les références de jeu restent soumises aux droits de leurs ayants droit ; aucune attribution des dérivés comme sprites officiels nouveaux.
