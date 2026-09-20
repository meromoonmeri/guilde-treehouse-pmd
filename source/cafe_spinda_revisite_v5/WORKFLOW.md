# Spinda V5 — travail en cours, correction de style prioritaire

## Demande utilisateur active

Générer des fenêtres, escaliers et meubles ASSORTIS aux nouvelles maps, à partir des références natives : ne plus simplement coller les sprites natifs V4. Adapter les rubans aux pans des murs. Préparer une bibliothèque de tapis rouges et de décorations pour un café Spinda revisité, objets séparés pour l’éditeur.

L’utilisateur a choisi **deux sorties latérales dans l’accueil**, une montée et une descente, en remplacement de la sortie sud. Le niveau souterrain doit avoir un retour montant ; l’étage supérieur un retour descendant. Le détail de la position des retours reste à caler, pas des warps moteur installés.

Deux corrections supplémentaires interrompent la génération :
1. garder le MÊME escalier que la sortie sud de l’accueil, adapté à la direction et à son éclairage entrée/sortie ;
2. l’utilisateur montre le petit seuil précis et dit « dans ce style là ».

Référence PRIORITAIRE : marches gris-brun peu profondes, nez de marche chauds, roche sombre recourbée, lumière dorée depuis le plancher qui décroît vers l’extérieur. Pas de grandes marches en bois, de rampe blanche, de portail rectangulaire ou de spirale. Les essais latéraux précédents deviennent trop hauts et ressemblent à des barrières : **ils ne constituent pas une livraison validée**.

`references/escalier_entree_accueil.png` est un crop sans redimensionnement du brut généré de l’accueil V4 choisi (448,624–760,800), correspondant au seuil montré. Ce n’est pas un sprite natif certifié. La pièce jointe annoncée `/home/user/uploads/image-1.png` était absente du filesystem ; ne pas prétendre avoir décodé ses octets. L’image était visible dans la conversation.

## Résultat actuel : prototypes, pas réseau V5 terminé

- `renders/cafe_spinda_revisite_v5/prototypes/SpindaV5_escalier_O_descente_etude.png` : **128×72**, transparent, nouveau sprite généré à partir du seuil et d’un guide de direction. Descente à gauche, seuil éclairé à droite, rebords recourbés ; aperçu4× sur magenta séparé. **Non approuvé par l’utilisateur, non placé dans les maps.**
- `SpindaV5_fenetre_generee_etude.png` : **56×64**, prototype généré à partir de la map et de la fenêtre native. Non approuvé/non placé.
- Aucun mobilier, tapis ou ruban V5 généré/livré à ce stade. Aucun pack final V5, aucun nouvel atelier, aucune liaison PMDO.

Les PNG des deux prototypes ont un alpha binaire et des dimensions divisibles par8. Le redimensionnement NN concerne uniquement ces créations générées, pas des pixels natifs. La provenance du seuil et son hash sont enregistrés. L’inspection du grand sprite a été faite visuellement ; pas de validation PMDO, collision ou intégration de bordure.

Les premières générations de salles et les bruts haute résolution V5 sont des **intermédiaires de recherche non retenus** dans `.cache/spinda5/generations/`. Ils sont exclus de la livraison et ne sont pas garantis conservés dans les snapshots. Leurs empreintes sont dans `etudes.json`. Les PNG normalisés et la référence utile sont conservés dans le dépôt. **Toutes les livraisons V4 et antérieures restent intactes**, ainsi que leurs bruts déjà archivés.

## À poursuivre

Valider visuellement le dessin des seuils, puis adapter la perspective et le raccord de lumière selon montée/descente. Pas une simple rotation qui transforme les treads en paroi. Intégrer les accès DANS les bordures, garder celles-ci basses, préserver la silhouette Spinda et les zones séparées.

Ensuite : fenêtres générées harmonisées, mobilier/kiosques générés et vides, rubans ajustés aux murs droits/obliques, tapis rouges modulaires et décorations sur feuilles transparentes. Les décors restent indépendants, aucun Pokémon cuit. Distinguer les générations inspirées du canon des vraies poses natives du feu.

Le projet a de nouveau été restauré au commit3d4ea6f0 au début de la continuation : état local préservé dans le stash « Preserve restored workspace before Spinda V5 continuation », puis fast-forward vers854d7c87 sur la même branche. Ne pas réappliquer le stash automatiquement.
