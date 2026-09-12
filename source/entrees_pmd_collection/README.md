# Collection de propositions PMD — 13 septembre 2026

## Décision utilisateur
Textures nouvelles autorisées pour des entrées indépendantes dans la DA PMD. Métano exact uniquement pour étendre Métano. Première livraison : 12 compositions originales générées et 12 variantes filtrées Abyss, plus les 40 compositions PNG du mod existant, séparées.

## Références examinées
- `meromoonmeri/PMD-SKY-PMDO-PORT`, arbre `d62110a00269bdc861b8fe41b077607a80f50978` : 460 fichiers `.rsground` recensés, pas 460 cartes inspectées visuellement. Le fichier `output/Grounds/aegis_cave_entrance.rsground` a été téléchargé et décodé (TexSize 1, une couche Base, largeur 126 cellules). Son aperçu versionné est conservé ici. Il montre des couloirs intérieurs séparés par du vide noir ; il n’est donc pas employé comme modèle d’une façade extérieure. Les noms entrance/floor01/floor02 partagent le même aperçu dans cet arbre. Pins et empreintes dans `references.json`. La copie brute de travail du Ground est en cache, pas redistribuée dans cette collection.
- Compositions réellement décodées précédemment : `source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_composition.png`, `ExplorersOfSkyOrigins__drenched_bluff_entrance_composition.png`, `ExplorersOfSkyOrigins__Brine_Cave_Entrance_composition.png`. Provenance détaillée : `source/cote_v5_expeditions/references/provenance.json`.
- Références envoyées au générateur : Crooked Cavern pour 04–09 et 11–12 ; Drenched Bluff aussi pour 04/09, et seule pour 10. Pour 01–03 : Crooked Cavern et composition native `sprites/cote_v4_abyss/07_balcon_haut/jour_composition.png`. La proposition 09 a ensuite été éditée au générateur pour rendre la bouche de grotte plus explicite.

## Réalisation et limites
Les originaux PNG proviennent du générateur d’images. `catalogue.py` ne les recrée pas : il produit la planche, le manifeste, la galerie, le catalogue et les variantes nocturnes à partir de ces originaux. Le filtre est importé directement de `source/cote_v4_abyss/night.py`, validé précédemment contre la source Abyss épinglée. Ne pas appliquer à nouveau le filtre aux variantes déjà nocturnes.

Les images ont des dimensions variables et ne sont pas toutes divisibles par 8. Aucun redimensionnement des originaux, aucune reconstruction native, séparation de calques, animation ou collision n’a été réalisée pour cette collection. La planche seule utilise des miniatures nearest-neighbor. Le n°12 est déjà crépusculaire dans son original : son export Abyss est donc plus sombre.

Le n°03 initialement demandé comme défilé ouvert comporte finalement une grotte : le résultat est documenté, pas présenté comme une réalisation exacte du prompt. Les premières images sont aussi préservées à leur chemin initial `renders/entrees_halcyon_generees/`.

## Vérification
`verification.json` : 40 exports du mod comparés octet pour octet à leurs compositions sources, présence de 36 plans et trois terrains sans fonds, décodage de tous les PNG. Inspection visuelle de la planche et correction de l’entrée cascade. Aucun nouveau test moteur requis ni revendiqué : le mod livré reste inchangé.

Recréer le catalogue : `.venv/bin/python source/entrees_pmd_collection/catalogue.py`.

Les dépôts de référence conservent leurs droits et conditions respectifs. Leur consultation ne constitue pas une affirmation de licence libre sur tous leurs contenus.
