# Brief de génération archivé — Grotte glaciaire boréale V1

## Intention

- Vue PMD en trois-quarts, zone de **768 × 640 px** une fois normalisée.
- Un chemin de neige clair entre au bord **sud**, se resserre dans la ravine et atteint une grande bouche de grotte glacée creusée dans la falaise **nord**.
- Falaises glacées bleu-blanc à gauche/droite, rebords, crevasses, cristaux et premier plan lisibles ; aucun personnage, bâtiment, interface ou texte.
- Le terrain est généré isolément sur magenta, sans ciel. Le ciel nocturne est généré séparément, sans aurore. Une planche 2×4 de rubans d’aurore est générée sur magenta, sans sol ni ciel.

## Références de direction artistique utilisées par le générateur

- `pmdskyicearena.png`
- `iceroadpmdsky.png`
- `aurorepmdsky.png`

Elles servent à cadrer la DA et la lecture, pas à extraire/dupliquer un layout ou à affirmer une origine canonique des nouveaux pixels. Les réponses brutes du générateur sont dans `generation/` et sont recopiées sans modification dans le pack sous `bruts/`.

## Décision de sélection des poses boréales

La planche demandée comporte huit cases. L’audit conservé dans `manifest.json` compare leur recouvrement alpha. Les cellules 0–3 gardent la famille de rubans et les points d’ancrage requis ; les cellules 4–7 changent davantage de silhouette/couleur. Le cycle final emploie les quatre premières, avec trois intercalaires alpha-prémultipliés entre chaque paire, dont la paire 3 → 0. Les autres restent visibles dans le brut pour éviter de les faire passer artificiellement pour des frames retenues.
