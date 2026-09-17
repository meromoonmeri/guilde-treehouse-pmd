# Structures — premier lot V1

Demande : produire les structures de guilde avant d’auditer les derniers ajouts de zones et préparer des relayouts aux textures canoniques.

Livré : 5 nouvelles propositions — QG treehouse, dortoir, réfectoire, infirmerie, atelier/réserve. QG256×256, annexes128×128, grille8px, PNG transparents et galerie à calques. Ponts `sprites/ponts_pmdo` et végétation `exports/vegetation_treehouse_v1` déjà disponibles, non recréés ni déclarés nouvellement approuvés. Les autres éléments du programme retenu ne sont pas annulés.

Méthode : deux générations sur magenta référencées au vrai arbre et aux maisons Métano ; détourage, suppression des petites poussières, réduction nearest-neighbor et palette RGB native issue de Métano et du deuxième étage de guilde. **Textures architecturales générées, pas une reconstruction pixel-exacte des matériaux canoniques.** Cette distinction est explicite dans la galerie. Pour les maps suivantes, seuls de vrais pixels canoniques doivent fournir les textures finales.

Calques : ombre au sol (alpha85), architecture visible, toiture/feuillage visible, fumée fixe du réfectoire. Les calques optionnels vides sont déclarés dans le manifeste. Séparation des surfaces visibles uniquement : masquer un toit ne révèle PAS un intérieur reconstruit. Fumée non animée. Entrées indicatives ; aucune collision, occlusion ou transition PMDO validée.

Sources/références : `source/amp_plains_fleurie_v1/references/Metano_Town_Objects.png`, provenance Halcyon working-copy1522c7a8 dans le manifeste d’origine ; recadrages arbre590,640,900,910 et maisons190,550,425,675. Palette complémentaire : `source/cafe_multietage_v3/references/guild_second_floor_reference.png`. Ressources natives attribuées aux créateurs PMD/Halcyon ; ne pas les présenter comme créations originales ou licence accordée ici.

89 tests de régression PASS, dont7 nouveaux pour structures/audit. Recomposition exacte, grille, alpha/palette, préservation des sources et statuts contrôlés. Art à examiner ; runtime NOT TESTED. ZIP et galerie autonome disponibles.
