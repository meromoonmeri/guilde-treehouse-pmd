# Sources du rêve plein écran

## Références de l’utilisateur

- `meromoonmeri/mypmdproject`, branche `arena/01a083a8-mypmdproject`, code consulté au commit `e3fa166525d08202503200c77482a2c1cc9cabad`.
- Commit artistique fourni : `319d10f69605331a07c817227c85ec8d0aba3dab`, contenant les images d’art direction et multiframe.
- `reference_portail.jpeg` correspond à `IMG_4861.jpeg` récupérée via le lien GitHub fourni (blob `bf208a45f4f1bd3d42155de080f64dfe1963bc1a`). La pièce jointe n’était pas présente dans le système de fichiers de ce checkout ; le lien a permis de retrouver la même référence.
- `reference_img_4871.jpeg` et `reference_img_4877.jpeg` sont les images de rêve aquarelle issues du commit artistique.

## Nouveaux dessins

Deux nouvelles images ont été produites au générateur à partir de ces références :

1. `nebuleuse_generee.png` : fond large multicolore, peint, avec une ouverture centrale calme, sans sphère ni interface. Même les zones sombres contiennent de la couleur.
2. `anneaux_generes.png` : matière annulaire circulaire aquarelle/irisée sur noir, sans sphère. Le noir central et extérieur est converti en transparence.

`prepare_reve.py` normalise la nébuleuse, prépare **36 phases de 256 × 256 px** pour l’anneau (variation circulaire, respiration radiale et couleur), puis les range dans un atlas 6 × 6 avec gouttières. Les bords et le centre de chaque phase sont transparents. Le rendu interpole les phases pour éviter un mouvement saccadé.

Le shader de fond superpose trois lectures de la nébuleuse à des profondeurs/vitesses différentes. Des plans d’anneaux sont distribués dans l’espace, un halo proche accompagne la sphère, et des poussières accentuent la profondeur. La sphère est un vrai maillage 3D éclairé, pas une image recadrée.

## Données et déroulé du quiz

`questions.json` et `natures.json` sont repris du projet de référence. La logique de pondération, le retour qui annule une réponse, les treize natures et le départage par ordre sont respectés. Le tirage est de huit questions sans répétition ; le PRNG du web n’est pas celui de NumPy.

La caméra change de côté et avance à chaque validation. Aucun timer ne fait avancer les questions. Les scores ne sont pas affichés ni retournés par l’API visible. Le mode capture permet des exports reproductibles en simulant explicitement des validations, sans changer cette règle dans le jeu normal.

## Portée de la livraison

La scène, les GIF et le module autonome sont livrés dans `guilde-treehouse-pmd`, sur la branche de cette session. Le dépôt de référence `mypmdproject` est resté en lecture seule. L’audit de ses dimensions est dans `reve/AUDIT_REFERENCE.md`.

Les tests du nouveau rendu ont été réalisés dans Chromium, hors ligne, en iframe opaque et sur six formats d’écran, avec vérification de la caméra, du déplacement, du résultat et du mouvement réduit. Ce n’est pas une validation d’intégration dans le moteur PMDO.
