# Végétation animée pour les structures / QG treehouse

Dernière demande utilisateur : tilesheets de végétation animée comme Halcyon, en complément de plusieurs structures PMD et d’un QG treehouse. Les questions précédentes de composition ont été passées : ce premier lot prend une ambiance forestière cohérente sans considérer un dessin de QG comme approuvé.

Premier lot : herbe fine, fougère, fleurs violettes, fleurs dorées, buisson rond, buisson à baies, branche feuillue et lierre suspendu. Bases/pivots fixes, animation discrète de vent, alpha transparent, palette PMD, grille de placement8px et empreintes32×32. Phases PNG séparées, atlas animé et GIFs ; pas d’import/runtime PMDO revendiqué.

Références déjà conservées dans le dépôt : Halcyon working-copy1522c7a8b7a34d70078e11ed605b21d563b0dc51, Vast_Steppe_Objects et Vast_Steppe_Flower_Animations. Le vrai groupe de fleurs emploie trois dessins24×24, séquence0/1/0/2 à14ticks par étape (TexLoc0/3/0/6 sur grille8px). Les références restent attribuées à Halcyon et à leurs auteurs ; elles ne deviennent pas nos créations.

Générateur sur magenta → alpha → taille native / nettoyage / palette → pivots fixes → assemblage de phases. Inspecter le layout réel : le générateur n’a pas toujours respecté trois colonnes. Les branches présentent des inversions de topologie ; utiliser le dessin neutre et réarticuler le feuillage plutôt qu’accepter des branches miroitées comme animation.

Ce lot n’est pas le pack de bâtiments : QG treehouse et annexes restent à dessiner. La demande ouvre un kit environnemental en parallèle ; elle n’annule pas les animations de guilde encore manquantes.
