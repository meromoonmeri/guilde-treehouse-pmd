# Métano — trois grandes extensions de falaises

Trois **layouts originaux de 2048 × 1536 px**, soit **256 × 192 cellules de 8 px** et **49 152 cases par carte**. Ils sont composés dans la continuité visuelle de Métano Town, avec les textures natives de Palika/Halcyon. Aucun bâtiment ni personnage n'est imposé.

## Les trois propositions

| Dossier | Composition | Parois | Accès visuels |
|---|---|---|---|
| `01_paroi/` | Grande paroi traversant le paysage, plateau ouvert au nord, trois sources et bassin inférieur | 320 px de hauteur de face | 3 cascades, 2 escaliers |
| `02_plateau/` | Grand massif central, contour rocheux, trois sources et espace libre au centre | 256 px de hauteur de face | 3 cascades, 2 escaliers |
| `03_terrasses/` | Trois plateaux superposés, chaîne de chutes centrales et chute latérale | 160 px par face | 4 cascades, 3 escaliers |

Ces cartes sont **trois propositions indépendantes**, pas trois morceaux automatiquement raccordés entre eux. Le raccord à une Ground existante de Métano n'a pas été placé. Dans cette perspective, les grandes faces rocheuses visibles sont orientées vers le sud ; le contour arrière d'un plateau est une lèvre courte, pas une grande face vue de dos.

## Respect de l'échelle Métano

- Roche, herbe, bordure, pied de falaise, sable et escaliers : échantillons natifs de `Metano_Town_Base` et `Metano_Town_Cliffs`.
- Sources : [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`.
- Les textures sont répétées **à leur taille native**, jamais grossies pour obtenir la taille du décor.
- Les grandes cascades conservent la largeur originale de **64 px** et utilisent les quatre frames de Métano. Leur couronne et leur bas sont préservés, leur milieu est prolongé par répétition de bandes. **Ces cascades longues ne sont donc pas des extractions intactes de 64 × 136 px.** Les extractions intactes restent dans `sprites/eau_metano/`.
- La géométrie du terrain, les contours des nouveaux cours d'eau et les petites vaguelettes sont nouvellement composés. Les couleurs principales de l'eau proviennent de la rivière originale. Ce ne sont pas des extensions officielles ni des copies pixel pour pixel d'une zone existante.
- Aucun générateur d'image n'a redessiné les textures. Les fichiers `source/falaises_metano/patches/` et `provenance.json` conservent les échantillons et leurs coordonnées source.

## Dans chaque dossier

- `terrain.png` : fond fixe complet, falaises, plateaux, chemins et escaliers, **2048 × 1536 px**.
- `eau_1.png` … `eau_4.png` : quatre calques d'eau RGBA transparents, mêmes dimensions et positions.
- `layout_1.png` … `layout_4.png` : quatre vues composées en résolution native, **sans grille peinte**.
- `layout.tmj` : carte **Tiled** orthogonale, 256 × 192 cellules, deux calques : terrain et eau animée.
- `layout.json` : polygones, hauteurs, positions des chutes et des escaliers.
- `apercu.png` : réduction ×0,5 pour inspection rapide, **pas** une texture de jeu.

## Atlas commun

- `Extension_Metano.png` : banque de tuiles de **8 × 8 px** commune aux trois cartes. Les tuiles identiques sont mutualisées.
- `Extension_Metano.tsj` : tileset Tiled avec animations déjà définies.
- `Extension_Metano.tile` : ressource native **PMDO/RogueEssence**. Les PNG internes, offsets et dimensions sont contrôlés par relecture.
- `kit.json` : liste des cartes, caractéristiques et `Frames / TexLoc / FrameLength` pour l'animation native PMDO.
- `planche.png` : présentation légendée des trois propositions, **pas un atlas**.
- `verification.json` : résultat des contrôles.

Les 181 séquences animées de cellules sont synchronisées sur quatre phases, `FrameLength = 10` ticks. À 60 Hz cela correspond à environ 166,67 ms par phase ; Tiled utilise 167 ms, approximation à la milliseconde entière. La cadence de rivière est issue de Métano ; celle des cascades longues est un choix d'aperçu, pas une cadence originale prouvée pour ces nouveaux assemblages.

## Édition

### Tiled

Ouvrir l'un des `layout.tmj` **en conservant son dossier et l'atlas dans le dossier parent**. Le chemin relatif vers `../Extension_Metano.tsj` est déjà défini. Toutes les cartes font bien 256 × 192 cellules de 8 px. Les deux calques restent séparés ; vous pouvez masquer l'eau et éditer le terrain.

### PMDO

Ajouter `Extension_Metano.tile` à `Content/Tile/` du mod et **réindexer les ressources** avec l'éditeur ou les outils du dépôt. Ne pas remplacer un index global par un index partiel. Cette ressource est prévue pour une **Ground à TexSize = 1**, pas pour une grille de donjon de 24 px.

Les TMJ ne sont pas des `.rsground`. Le placement natif doit passer par votre importeur de carte ou être refait dans la Ground avec l'atlas et les coordonnées du manifeste. Pour traduire un GID Tiled : retirer 1, puis calculer `X = tileid % columns`, `Y = tileid // columns` ; les représentants animés possèdent leurs Frames dans `kit.json`.

**Pas de `.rsground` ni de script de transitions livré.** Les collisions, chemins réellement praticables, franchissements de cours d'eau, zones d'entrée et calques d'occlusion ne sont pas configurés. Les chemins et escaliers sont des indications visuelles. Vérifier les traversées et raccords dans l'éditeur avant de jouer.

## Aperçu autonome

Ouvrir `../../apercu_falaises_metano.html` : choisir une des trois cartes, animer/arrêter l'eau, afficher la grille, passer au zoom natif ou ×2 et exporter la vue affichée. Le bouton PNG inclut la grille seulement si elle est activée. Les PNG du pack n'en contiennent jamais.

## Reconstruction et tests

```sh
python source/build_cliff_layouts.py
python source/verify_cliff_layouts.py
```

Pillow requis. La reconstruction réutilise les patches sauvegardés et les frames de cascade du pack eau ; elle ne dépend pas d'un téléchargement réseau. Le vérificateur recompose les **trois cartes Tiled aux quatre phases**, compare aux PNG et relit le `.tile` natif. Résultat : **zéro différence entre les recompositions et les fichiers livrés**. Cela ne signifie pas que les nouveaux layouts seraient des cartes originales du jeu. Ouverture dans le moteur PMDO et dans l'interface Tiled non testée.

## Attribution

Textures de Métano Town : **Palika / Halcyon** et les artistes crédités par le projet. Le [README de Halcyon](https://github.com/Palikadude/Halcyon#credits) cite notamment **Jaifain pour les animations de rivière de Métano**. La géométrie des trois layouts et leur assemblage ont été réalisés ici. Aucune nouvelle licence n'est accordée sur les ressources tierces ; vérifier les autorisations des auteurs avant redistribution publique.
