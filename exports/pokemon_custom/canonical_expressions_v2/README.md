# Expressions canoniques V2 — Carapagos : seize expressions de face

## Ce qui a été produit dans ce lot

Huit nouvelles générations individuelles de Carapagos : Crying, Teary-Eyed, Determined, Joyous, Inspired, Dizzy, Sigh, Stunned. Elles sont dérivées du **Normal approuvé**, puis limitées à la région de l’œil : le bec, la narine, la silhouette et les marquages hors de cette région restent identiques. Le fond de chaque nouvelle expression vient de sa case exacte dans `template.png`, sans recoloration.

La planche de Carapagos contient maintenant les **16 émotions de face** :
- **6 originaux préservés octet pour octet** : Normal, Happy, Angry, Sad, Shouting, Surprised. Leur approbation antérieure n’est pas étendue aux nouvelles propositions.
- **10 propositions de la nouvelle méthode** : Pain et Worried du lot précédent, plus les huit nouvelles expressions.

Les nouvelles expressions passent les précontrôles40×40, alpha opaque,15couleurs maximum (fond compris), fond canonique exact et préservation des traits hors région d’expression. La planche200×160 passe le profil technique `full`. Aucun des dix nouveaux sujets n’est un doublon exact : ce contrôle est fait avant composition des fonds.

**Format complet de face ≠ approbation artistique, vues inverses ou validation PMDO.** Les vues inverses ne sont pas produites. La justesse de l’expression à l’intérieur du masque reste soumise à revue visuelle. Les anciens portraits approuvés sont étiquetés « conserve » dans l’aperçu pour les distinguer des nouvelles propositions.

## Fichiers

- `tirtouga/portraits_individual/` : les16fichiers nommés par émotion.
- `tirtouga/portraits.png` : planche200×160 contenant les16émotions requises de face ; les4Special facultatifs sont transparents. `portraits_partial.png` est sa copie au nom hérité du générateur de lots.
- `tirtouga/editable/` : sujets et fonds des10nouvelles propositions séparés.
- `tirtouga/review/expressions_x4.png` : revue4×4 à agrandissement net.
- `verification.json` : validation complète de face, hashes des originaux, sources et vérifications de doublons.
- Galerie à la racine : `apercu_expressions_canoniques_v2.html`.

Les sections Méga-Raichu X/Y reprennent le lot précédent **sans nouvelles créations Raichu dans ce tour** : X comporte5propositions valides, Y3. Colère et Surprise de MégaY sont toujours bloquées à16couleurs et restent hors `portraits_individual`. Ne pas annoncer ces lots Raichu complets.

Les portraits Terapagos Stellaire restent suspendus sur demande utilisateur. L’objectif global SpriteCollab est inchangé ; ce lot ne comble qu’une partie locale du travail et ne constitue pas une contribution upstream acceptée.

Reconstruction : `.venv/bin/python source/pokemon_custom/next_species/build_canonical_expressions_v2.py`.
