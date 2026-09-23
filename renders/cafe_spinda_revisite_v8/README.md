# Spinda V8 — lot 1 assorti et mode nuit

**Livraison partielle**, pas une collection Halcyon achevée. Choix confirmés : élargir aux intérieurs pertinents et faire **une collection commune**, plutôt que trois gammes séparées : bois miel Spinda, sauge/végétal Kirlia, crème/rose Charmilly.

## État réel
Le générateur a imposé une **limite de dix images sur ce tour**. Dix adaptations ont été produites ; **neuf retenues pour examen**. La table vide est exclue du pack car la caméra montre son dessous. Ce n’est pas une approbation artistique utilisateur.

Lot livré : paire de tonneaux, plante haute, chevalet de menu, petit tapis, table avec tasses, caisses, étagère, bar à jus et tabouret. Tous sont passés au générateur à partir de leur référence Halcyon et de la pièce Spinda. Ce ne sont ni des pixels natifs ni une simple recoloration de la feuille d’origine.

Plan élargi : 23 objets de la feuille Halcyon V7 + 12 compléments des banques de réserve, chambre et salon de guilde + 1 applique de création. **27 objets restent à générer ou reprendre.** Les compléments sont référencés, pas encore générés. `audit/coverage.json` distingue sans ambiguïté objets retenus, rejetés et en attente. Périmètre ciblé d’intérieurs, pas inventaire exhaustif de tout Halcyon.

## Fenêtres / rubans — NON LIVRÉS dans cette passe
- Les nouvelles fenêtres intégrées au mur n’ont pas encore pu être générées. Les fenêtres V7 de32×32 restent temporairement visibles, sur leurs anciens calques.
- Les rubans muraux assortis n’ont pas encore été générés. Aucun calque vide ou ruban natif recopié n’est présenté comme leur livraison.
- La nouvelle applique est en attente ; aucune flamme n’est inventée ou placée.

Les guides de travail et emplacements futurs se reconstruisent avec `source/cafe_spinda_revisite_v8/prepare_guides.py`. Ils ne modifient pas les pièces livrées.

## Nuit tamisée — LIVRÉE sur les cinq salles
L’architecture de jour reste **RGBA identique à V7**, accès N/S compris. La nuit conserve exactement l’alpha et la géométrie ; elle réduit les couleurs via facteurs RGB [0.42,0.35,0.40], atténue les anciens motifs lumineux à18% d’alpha et ajoute un calque séparé de lumière ambrée très diffuse, limité à la silhouette de la pièce. C’est un éclairage **indirect, statique**, pas une animation de flamme ni un éclairage moteur simulé comme réel. Aucun meuble posé.

Chaque calque jour/nuit est exportable. Les neuf meubles ont également une variante nocturne assortie. Les deux tilesheets sont des versions jour/nuit de **la même collection**, pas deux lots d’objets différents.

## Fichiers
- `SpindaV8_atelier_lot1.zip` : atelier autonome,57 calques PNG (jour+nuit),9 objets en deux ambiances,2 feuilles, références comparatives et inventaire. Extraire entièrement.
- `SpindaV8_mobilier_lot1.zip` : uniquement mobilier/feuilles jour+nuit et suivi.
- Le dépôt lit les calques dans le ZIP pour éviter les doublons. Les PNG individuels de meubles restent accessibles dans `assets/`.
- `.venv/bin/python source/cafe_spinda_revisite_v8/build.py` reconstruit les livrables ; `python source/cafe_spinda_revisite_v8/serve.py --port 8008` ouvre l’atelier par HTTP.

Canevas Ground divisibles par8 ; normalisation nearest avec proportions conservées sur le généré seulement. Les fenêtres, marches et calques historiques ne sont pas régénérés silencieusement. Aucun asset natif antérieur modifié.

## Conservation et limites
Les dix grands originaux générés et les cinq nouvelles banques de référence sont conservés sans perte dans l’historique Git, indexés dans `source/cafe_spinda_revisite_v8/raws/archive.json`. Les cinq masters V4 encore sur disque ont rejoint leur archive déjà utilisée pour les études ; lecteurs et restauration sont vérifiés, anciens rendus/ZIP inchangés. Garder un historique Git complet pour reconstruire.

Tests de pixels, formes alpha, atlas, ZIP et interactions en DOM simulé. **Pas de navigateur graphique ou PMDO validé.** Les prochaines générations doivent traiter le reste de l’inventaire, puis les fenêtres en contexte et les rubans conformés aux murs.
