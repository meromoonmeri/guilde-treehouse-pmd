# Grotte glaciaire boréale V1 — état de production

Mandat : une nouvelle zone glaciale avec falaise, grotte de glace au nord, chemin continu depuis le sud et ciel boréal animé, en suivant la méthode multicouche de la Guilde.

La livraison est `renders/grotte_glaciaire_boreale_v1/`, accompagnée de `apercu_grotte_glaciaire_boreale_v1.html` et de son ZIP. Les sources générées sont volontairement conservées dans `generation/` : terrain sur magenta, ciel sans aurore, planche 2×4 d’aurores sur magenta.

Règle de qualité : conserver une composition de terrain complète, pas une mosaïque de morceaux de maps. Détourer le magenta depuis le bord, conserver le ciel séparé, décomposer les surfaces visibles en calques alignés et conserver le passage Sud → seuil nord. Pour l’aurore, une animation en place à plusieurs phases est requise : ni scroll ni wrap ne doivent être vendus comme animation des rubans.

La planche d’aurore est une source de génération, pas une acceptation automatique des huit cases. Les quatre premières poses ont une silhouette suffisamment cohérente pour être ancrées et interpolées ; les poses 4–7 restent conservées dans le brut mais ne sont pas glissées dans le cycle avec une rupture visible. Le cycle final doit rester explicitement une proposition, pas un cycle PMD officiel retrouvé.

Ce rendu ne fournit pas de tile natif, `.rsground`, collision, warp, parallax PMDO ou test moteur. Les contrôles de la chaîne couvrent la partition/recomposition, le passage géométrique, les exports et le lecteur, pas une validation artistique ou runtime.
