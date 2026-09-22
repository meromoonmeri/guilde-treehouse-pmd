# Spinda — banderoles adaptées, tapis rouges, estrade et deux rideaux

## Images directement visibles, sans HTML
- `apercus/SpindaDecor_cafe_demonstration.png` : exemple dans le café, sur architecture V7 intacte. Estrade et tapis seulement posés pour cet aperçu.
- `apercus/SpindaDecor_collection.png` : planche PNG agrandie2×, sans lissage.
- `apercus/SpindaDecor_estrade_assemblee.png` : estrade + deux rideaux, fond transparent.
- `apercus/SpindaDecor_banderoles_5salles.webp` : contrôle des cinq implantations murales, image fixe (aucune animation demandée ici).

## Banderoles canoniques, réadaptées
La référence est le ruban de **SpindaCafe2, Explorers of Sky Origins**, déjà audité en V7 : nœuds/rubans rouge-orangé, fanions jaunes et cyan. La référence native est conservée sans changement dans `references/`, avec source, commit et hash dans le manifeste.

Les sorties adaptées sont **des créations générées référencées, pas des pixels canoniques inchangés**. Deux essais frontaux ont été exclus pour cadrage/dessin inadéquats. Les diagonales retenues ont été redressées, puis leur ligne d’attache conformée aux pans de mur : ces transformations concernent exclusivement les créations. Aucun fragment de comptoir ou personnage n’est utilisé sur les murs.

Calque dédié600×448 pour chacune des cinq salles, en jour/nuit. Bande sous les petites fenêtres ; raccords aux pans obliques ; interruption devant les montées N de l’accueil et du casino. Fenêtres et passages non recouverts. Aucun PNG d’architecture antérieur modifié. Les fenêtres elles-mêmes ne sont pas régénérées par cette livraison.

## Tapis et scène
Trois tapis rouges générés : rectangle, ovale, chemin de tapis. Motifs spirales crème, bordure dorée, palette café Spinda. Ils restent séparés et non préplacés dans les maps.

Estrade vide en bois miel, petit motif spiralé rouge, façade crème/bleu avec accents roses inspirés de Mime Jr. **Rideau gauche et rideau droit sur deux calques distincts**, rouge rosé, attaches bleues et broderies crème. Pas de Pokémon cuit dans le décor. Le générateur avait ajouté un morceau de salle à gauche de l’image du rideau droit : il est explicitement retiré par détourage, seul le rideau droit est conservé.

`estrade/` contient les trois PNG alignés sur le même canevas208×184 : plateforme, rideau gauche, rideau droit. Leur alpha-over dans cet ordre recompose l’aperçu transparent. `objets/` contient aussi les éléments autonomes. Variantes nuit adaptées, non natives, facteurs RGB[0.42,0.35,0.40]. Supports des rideaux inclus dans leur propre calque ; pas d’animation de tissu revendiquée.

## Import et préservation
ZIP : objets PNG transparents, modules et calques muraux, trois calques de scène, tilesheet/index8px, référence et manifeste. Dimensions divisibles par8 pour Ground ; collisions/warps non audités. Les rendus de démonstration ne remplacent pas les maps.

10sorties originales conservées sans perte dans l’historique Git via `source/spinda_decor_v1/raws/archive.json` ;8retenues. Lecteur/restauration `archive.py`. Trois anciens bruts Casino (ancienne estrade/anciens rideaux/première étude de terrain supplantée) sont également conservés dans Git avec lecteur et tests ; tous leurs anciens rendus/PNG/ZIP restent inchangés. L’historique complet est nécessaire pour reconstruire les bruts.

Reconstruction : `.venv/bin/python source/spinda_decor_v1/build.py`. Tests dans `verify.py`. **Aucune validation PMDO ni approbation artistique revendiquée.** Les autres meubles/fenêtres en attente de V8 restent en attente ; les torches précédemment livrées ne sont pas modifiées.
