# État courant

La demande précédente de copie fidèle est suivie d’une nouvelle autorisation : légères modifications de layout et ensembles de couleurs cohérents, avec générateur, magenta, couches et assemblage. Quatre références du commit8eb46bc sont utilisées : côte D25P11A, cristal D17P33A, forêt D24P31A, sables D14P11A.

Avant la fin du premier lot, l’utilisateur a ajouté : bordures de feuilles immersives en forêt ; version de sable avec siphons d’eau animés et petites modifications de calques ; reflets cristal bleu/rose/blanc ; côte roche cendrée (interprétation de « centre ») et lave. Les huit bases sont conservées et cinq variantes ajoutées, pas de remplacement d’anciens fichiers.

Bruts réellement générés : terrain sur magenta pour chaque référence, sols pour côte/cristal/forêt. Deux appels de sol de sable ont échoué sans image : reconstruction par échantillon24×24 du sable généré, explicitement documentée. Première génération de bordure trop chargée/non utilisée ; seconde feuille de deux rameaux isolés retenue, détourée et composée en bordures.

Cycles : côte30×130ms ; cristal12×160ms ; sables6×60ms ; forêt statique. Adaptations : siphons d’eau depuis les6 phases de sable ; lave depuis les30 phases d’eau. Nouveau reflet irisé24×80ms, RGB fixes et opacité variable. Lueur de berge30×130ms. Les anciennes variantes gardent les empreintes natives après harmonisation de palette ; les variantes adaptées ne sont pas décrites comme natives.

Galerie principale `apercu_variantes_magenta_v1.html` : treize choix (cinq ajouts et huit bases), toutes les couches et horloges indépendantes. PNG, ORA et WebP complets, archive des cinq ajouts. `verify.py` vérifie les96 frames de base, les102 PNG des groupes ajoutés, recompositions, couleurs fixes, masques et ORA. DOM simulé passé. Pas de PMDO/GPU.

Ne pas importer build.py/enhancements.py comme bibliothèques : leur exécution écrit les exports. Les fonctions de palette/détourage partagées sont dans palette.py.
