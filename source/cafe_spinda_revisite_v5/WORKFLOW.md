# Spinda V5 — travail en cours, correction de style prioritaire

## Demande utilisateur active

Générer des fenêtres, escaliers et meubles ASSORTIS aux nouvelles maps, à partir des références natives : ne plus simplement coller les sprites natifs V4. Adapter les rubans aux pans des murs. Préparer une bibliothèque de tapis rouges et de décorations pour un café Spinda revisité, objets séparés pour l’éditeur.

Le choix latéral initial a été remplacé par la correction **nord/sud selon l’étage**. Plan actif : accueil0 N→café+1 et S→casino−1 ; casino−1 N→accueil0 ; café+1 S→accueil0. Les passages E/O restent au même niveau. Le prototype latéral et les anciens guides ne doivent plus servir de placement. Aucun warp moteur n’est installé.

Deux corrections supplémentaires interrompent la génération :
1. garder le MÊME escalier que la sortie sud de l’accueil, adapté à la direction et à son éclairage entrée/sortie ;
2. l’utilisateur montre le petit seuil précis et dit « dans ce style là ».

Référence PRIORITAIRE : marches gris-brun peu profondes, nez de marche chauds, roche sombre recourbée, lumière dorée depuis le plancher qui décroît vers l’extérieur. Pas de grandes marches en bois, de rampe blanche, de portail rectangulaire ou de spirale. Les essais latéraux précédents deviennent trop hauts et ressemblent à des barrières : **ils ne constituent pas une livraison validée**.

`references/escalier_entree_accueil.png` est un crop sans redimensionnement du brut généré de l’accueil V4 choisi (448,624–760,800), correspondant au seuil montré. Ce n’est pas un sprite natif certifié. La pièce jointe annoncée `/home/user/uploads/image-1.png` était absente du filesystem ; ne pas prétendre avoir décodé ses octets. L’image était visible dans la conversation.

## Résultat actuel : audit N/S et prototypes historiques, pas V5 complète

- `renders/cafe_spinda_revisite_v5/prototypes/SpindaV5_escalier_O_descente_etude.png` : **128×72**, transparent, nouveau sprite généré à partir du seuil et d’un guide de direction. Descente à gauche, seuil éclairé à droite, rebords recourbés ; aperçu4× sur magenta séparé. **Abandonné après la correction N/S, conservé uniquement comme historique.**
- `SpindaV5_fenetre_generee_etude.png` : **56×64**, prototype généré à partir de la map et de la fenêtre native. Non approuvé/non placé.
- Aucun mobilier, tapis ou ruban V5 généré/livré à ce stade. Aucun pack final V5, aucun nouvel atelier, aucune liaison PMDO.

Les PNG des deux prototypes ont un alpha binaire et des dimensions divisibles par8. Le redimensionnement NN concerne uniquement ces créations générées, pas des pixels natifs. La provenance du seuil et son hash sont enregistrés. L’inspection du grand sprite a été faite visuellement ; pas de validation PMDO, collision ou intégration de bordure.

Les premières générations de salles et les bruts haute résolution V5 sont des **intermédiaires de recherche non retenus** dans `.cache/spinda5/generations/`. Ils sont exclus de la livraison et ne sont pas garantis conservés dans les snapshots. Leurs empreintes sont dans `etudes.json`. Les PNG normalisés et la référence utile sont conservés dans le dépôt. **Toutes les livraisons V4 et antérieures restent intactes**, ainsi que leurs bruts déjà archivés.

## Audit N/S effectué — référence conservée

`audit_escaliers.py` reprend exactement les marches de l’accueil V4, sans rotation, étirement ou recoloration supplémentaire. Il ajoute les portes nord à l’accueil et au casino, la porte sud au café, garde toute l’ancienne sortie sud de l’accueil. Ces corrections locales utilisent les bases générées V4 ; les nouvelles générations d’essai ne sont pas retenues.

Plan annoté, rapport et coordonnées : `renders/cafe_spinda_revisite_v5/audit/`. Quatre positions vérifiées, deux liens réciproques, marches pixel-identiques, bandes centrales40px sans trou alpha, raccord nord au sol original, empreintes raster16px et contre-tests PASS. L’ancien évidement nord jusqu’à136 laissait un trou sous les marches ; il s’arrête maintenant à128. Au sud du café, la coupe est limitée à la bande centrale pour préserver les épaules rocheuses.

Exporter les PNG : `.venv/bin/python source/cafe_spinda_revisite_v5/audit_escaliers.py`. Les copies `audit/exports/` sont ignorées/reconstructibles ; sources V4, script, plan et illustration sont conservés. **Pas de collision/warp PMDO testé ; une bande opaque n’est pas une collision moteur.** Les deux sorties de l’accueil sont désormais internes : accès extérieur non défini, ne pas ajouter une troisième sortie sans accord.

## À poursuivre

Conserver ce plan nord/sud et le dessin du seuil choisi. Finir l’intégration/import moteur si demandé, sans revenir au prototype latéral. Les décors sont omis de l’audit pour lire l’architecture.

Ensuite : fenêtres générées harmonisées, mobilier/kiosques générés et vides, rubans ajustés aux murs droits/obliques, tapis rouges modulaires et décorations sur feuilles transparentes. Les décors restent indépendants, aucun Pokémon cuit. Distinguer les générations inspirées du canon des vraies poses natives du feu.

Le projet a de nouveau été restauré au commit3d4ea6f0 au début de la continuation : état local préservé dans le stash « Preserve restored workspace before Spinda V5 continuation », puis fast-forward vers854d7c87 sur la même branche. Ne pas réappliquer le stash automatiquement.
