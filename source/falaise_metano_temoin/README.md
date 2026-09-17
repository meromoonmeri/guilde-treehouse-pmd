# Retour à la méthode approuvée — falaise Métano texturée sur magenta

Correction utilisateur : ne pas changer de méthode. Le générateur doit reprendre **la texture de roche et l’herbe Métano** pour générer la falaise sur **fond magenta**. Ni layout en aplats comme livrable final, ni nouvelle roche librement inventée.

Un seul témoin est produit avant de relancer toute la série : la crête du Sillage. Les dix retouches V6 et les cartes natives restent intactes. Les essais V7 de nouvelle roche et V8 de layouts plats ne sont pas la méthode à poursuivre.

## Entrées réellement fournies au générateur
1. `01_layout_metano_magenta.png` : composition native existante `renders/metano_expeditions_actuel/01_crete_sillage/jour.png`, dont seuls les pixels hors du masque `MASQUE_TERRE.png` sont remplacés par du magenta. Même canevas et terrain, pas de redimensionnement.
2. `source/falaises_generees/reference_canonique.png` : la référence Métano déjà utilisée par la méthode antérieure, avec herbe, faces, couronnes et retours.

Consigne : conserver le layout et les ouvertures ; réutiliser cette matière et ce grain, les ombres mauves/ocres et l’herbe jaune-verte ; corriger les raccords et la continuité des bordures sans remplacer la roche par du grès lisse, de gros blocs ou des contours noirs. Aucun ciel, océan, arbre, chemin ou structure. Tout l’espace hors terrain sur magenta pur.

## Résultats
Dans `renders/falaise_metano_temoin/` :
- `01_crete_sillage_magenta.png` : sortie originale du générateur, inchangée.
- `01_crete_sillage_fond_uniforme.png` : uniquement le chroma magenta normalisé.
- `01_crete_sillage_transparent.png` : chroma remplacé par alpha nul ; tous les autres pixels RGBA conservés à l’identique.

`export.py` reproduit les deux exports et le rapport. Il ne génère ni ne repeint la roche. Aucun redimensionnement. La génération est guidée par la texture canonique, mais n’est pas une copie pixel à pixel certifiée des tuiles. La continuité artistique des raccords reste à valider sur ce témoin avant d’en décliner toute la série.

La demande de ralentir et densifier le cycle océan reste en attente : aucune cadence ni ressource océan n’a été modifiée pendant ces essais interrompus. Ne pas annoncer cette animation comme réalisée.
