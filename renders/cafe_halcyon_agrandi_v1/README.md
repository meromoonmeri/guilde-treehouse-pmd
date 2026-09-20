# Grand Café Métano — Halcyon agrandi, terrain vide

[Atelier](index.html) · [Terrain magenta](CafeHalcyon_terrain_magenta.png) · [Terrain transparent](CafeHalcyon_terrain_transparent.png)

## Le vrai café, agrandi sans grossir ses pixels

Source : **Palikadude/Halcyon**, commit [`da6c2130d641507447e6386a5e47a296e8cb4c71`](https://github.com/Palikadude/Halcyon/tree/da6c2130d641507447e6386a5e47a296e8cb4c71), `Data/Ground/metano_cafe.rsground` et les cinq banques `Metano_Town_Cafe_*`.

| | Original | Nouvelle salle |
|---|---:|---:|
| Dimensions | 456 × 320 px | **840 × 576 px** |
| Grille de 8 px | 57 × 40 | **105 × 72** |
| Surface du canevas | 145 920 px² | 483 840 px², soit **× 3,32** |
| Échelle des pixels | 1× | **1×, inchangée** |

Ce n’est pas une réinterprétation générée des textures. **Chaque pixel visible du terrain provient directement de la banque native**, sans recoloration, rotation, miroir ou rééchantillonnage. Le nouveau plan est un assemblage original de ces pixels, pas une carte officielle déjà livrée par Halcyon.

L’agrandissement insère six bandes horizontales complètes de64px et quatre bandes verticales de64px. Les coins, la perspective, les panneaux et les motifs des rubans gardent leur taille native. Pas de colonnes aléatoires de8px pour construire les murs. La recette et les références sont dans `manifest.json` ; les sources et leurs SHA-256 sont conservés dans `source/cafe_multietage_v1/references/` du dépôt.

### Entrée et détourage

- Une seule entrée sud, **56px de plancher libre** (60px avec ses deux bordures), centrée en x484. Son décalage de64px par rapport au centre de la salle conserve celui de l’original.
- Ancien emplacement déplacé remplacé par une bordure native entière, sans seconde porte résiduelle.
- Une petite lacune alpha du seuil source est comblée avec la tuile de plancher native adjacente, pour éviter un trait magenta sur le passage. Cette retouche de disposition est documentée dans la recette, sans couleur inventée.
- L’aplat brun extérieur natif est détouré par connexité au bord ; les petites poussières de fond détachées sont retirées. Aucun pixel visible conservé n’est recoloré.

## Salle vide, décoration indépendante

**Aucune table, aucun comptoir, aucune plante, aucun brasero/fourneau et aucun Pokémon ne sont posés dans la nouvelle salle.** Aucun sprite de marchand n’est intégré. Les deux rectangles du viewer sont seulement des repères facultatifs pour le service et les places assises : ils ne sont jamais imprimés dans les PNG.

Les **rubans fixes des murs** font partie de l’illustration native `Base` et sont conservés pour rester fidèle à Halcyon. Ils ne constituent pas des instances de mobilier placées dans la salle. Cette livraison ne prétend pas fournir des murs originaux reconstruits derrière des rubans détachables.

### Terrain — cinq calques alignés

Tous les fichiers de `calques/` ont un canevas840×576 et une origine0,0 :
1. `CafeHalcyon_sol.png` — plancher et seuil ;
2. `CafeHalcyon_mur_fond.png` — paroi arrière ;
3. `CafeHalcyon_mur_gauche.png` — retour gauche ;
4. `CafeHalcyon_mur_droit.png` — retour droit ;
5. `CafeHalcyon_bord_avant.png` — bordure avant et entrée.

Les cinq plans recomposent exactement le PNG transparent. Ce sont des partitions des surfaces visibles, **pas des murs mobiles complets avec sol reconstruit derrière**. Déplacer une table n’abîme pas le terrain puisqu’aucun meuble n’y est intégré.

### Mobilier — planches séparées

`mobilier/CafeHalcyon_Objects*.png` : les **quatre vraies banques d’objets du café**, non redimensionnées. Elles contiennent comptoir, tables, plantes et accessoires d’Halcyon. Certains objets utilisent plusieurs plans Under/Objects/Over/Fringe : sélectionner leurs blocs correspondants, conserver leur alignement relatif et leur ordre de rendu dans l’éditeur.

Également inclus, sans placement :
- support de brasero natif, sans flamme ;
- corps de fourneau repris du kit casino précédent, **généré et non natif**, explicitement signalé dans le viewer ; flamme native indépendante à l’offset32,32.

La miniature `reference_halcyon.png` montre le café **original meublé**, seulement pour comparaison. Ce n’est pas le terrain à importer.

### Feu — quatre vraies poses, pas une image défilée

- `animations/CafeHalcyon_flamme_4poses.png` :128×40, quatre poses32×40, ordre gauche→droite ;
- `animations/CafeHalcyon_brasero_4poses.png` :128×64, quatre poses32×64 ;
- huit PNG individuels également fournis ;
- **6ticks par pose** dans le Ground Ledian ; aperçu à100ms/pose en supposant60Hz, boucle400ms.

Les poses sont vérifiées contre les pistes du vrai `ledian_dojo.rsground` et la banque `Ledian_Dojo_Animated.tile`. Le support + chaque flamme recomposent exactement le brasero source. Provenance complète : `flammes_provenance.json`. Aucune de ces animations n’est ajoutée au terrain automatiquement.

## Import dans PMDO Dev

1. Importer les PNG utiles de `calques/`, `mobilier/`, `animations/` avec **PNG to Tileset**, grille **8px** pour ces ressources Ground. Ce n’est pas une règle pour les DTEF.
2. Les basenames d’import sont préfixés `CafeHalcyon_` et uniques. Ne pas renommer plusieurs feuilles avec le même basename.
3. Recomposer les cinq plans du terrain à0,0, sans redimensionnement. Le PNG transparent complet sert aussi de référence.
4. Placer vous-même les meubles et Pokémon. Garder un poste libre derrière le comptoir et une approche client dégagée. Configurer l’ordre des éléments devant/derrière les personnages.
5. Pour l’atlas de feu : chaque pose commence4cellules de8px plus loin horizontalement ; largeur4cellules, hauteur5cellules pour la flamme,8pour le brasero. Reprendre la cadence native6ticks.
6. Définir et tester les collisions, la transition de l’entrée sud, les scripts et les interactions dans votre projet.

**Aucun `.rsground` nouveau, NPC, warp, collision moteur ou script de café n’est livré/configuré.** Le masque `guides/CafeHalcyon_surface_libre.png` est une aide de dessin et un contrôle de continuité, pas une carte de collision PMDO validée.

## Viewer et ZIP

Le ZIP est autonome : extraire tout son contenu puis ouvrir `index.html`. Aucun appel à localhost ni dépendance aux dossiers voisins. Pour servir les fichiers par HTTP : `python -m http.server 8004 --bind 0.0.0.0` depuis le dossier extrait.

Les cases masquent les calques uniquement pour la visualisation. Les liens de téléchargement du terrain donnent toujours la composition complète, les PNG individuels restant dans `calques/`. Les planches de mobilier et l’animation restent dans le catalogue, jamais sur la map.

## Reproduction et vérifications

Depuis la racine du dépôt, avec Pillow, NumPy et SciPy :

```sh
python source/cafe_halcyon_agrandi_v1/build.py
python source/cafe_halcyon_agrandi_v1/verify.py
python source/cafe_halcyon_agrandi_v1/package.py
node source/cafe_halcyon_agrandi_v1/test_viewer.cjs
python source/cafe_halcyon_agrandi_v1/package.py
```

`verification.json` : banques décodées et hashées, traçabilité de tous les pixels visibles, coins intacts, recomposition exacte, magenta pur, une entrée unique, continuité avec dégagement8px, zones libres, aucune décoration placée, poses natives réelles, compatibilité8px. `verification_viewer.json` : DOM simulé, calques/zoom/repères et animation, dépendances de la version normale et du ZIP extrait. Pas de navigateur graphique ou de PMDO exécuté : ces tests ne valent pas approbation artistique ou validation moteur.

Attribution : Palikadude/Halcyon, contributeurs et ayants droit Pokémon Mystery Dungeon. Les ressources publiques ne sont pas présentées comme libres de toute licence ; conserver les attributions et vérifier les conditions applicables avant redistribution de votre mod.
