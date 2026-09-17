# Audit : rendu des zones Métano après import en jeu

## Conclusion

**Un défaut de reconstruction est confirmé dans les assets. Une réduction d’échelle au moment de l’import n’est pas encore démontrée.** Les paramètres et le fichier réellement importé par l’utilisateur ne sont pas disponibles.

Le pipeline a conservé les pixels de petites tuiles natives, mais pas les assemblages complets qui donnent aux falaises leurs volumes, leurs couronnes, leurs pieds et leurs retours. Il peut donc livrer une falaise morcelée, avec des colonnes très fines et une répétition excessive, malgré un contrôle « zéro différence de pixel » réussi.

Cette validation était insuffisante : elle prouvait l’origine des pixels et la fidélité des exports au rendu produit, **pas la qualité de la reconstruction par rapport à Métano, ni son échelle apparente en jeu**.

Aucune composition validée, aucun calque, atlas ou fichier Aseprite/Tiled n’a été modifié pendant cet audit.

## Pièces de preuve

- `comparaison_echelle.png` : extrait de terrain original, guide généré et reconstruction livrée. Extraits de 320 × 224 px, affichés à **×2 entier**, sans lissage. Les lieux diffèrent : comparaison de construction et de densité, pas mesure du zoom du jeu utilisateur.
- `mesures.json` : dimensions, paramètres de grille, empreintes, références au Ground original et indices d’adjacence.
- Script : `source/audit_zones_metano.py`. Ne pas importer le builder pour auditer : son exécution reconstruirait les assets.

## 1. Pas de réduction des tuiles détectée dans les exports

| Élément mesuré | Valeur |
|---|---|
| Tuiles sources natives | 8 × 8 px |
| PNG canoniques et calques contrôlés | 2048 × 1536 px |
| Cartes Tiled | 256 × 192 cellules de 8 px |
| Aseprite animé | 2048 × 1536, RGBA 32 bits, 4 frames |
| Guide généré | 1200 × 896 px |
| Adaptation du guide à la carte | ×1,7067 horizontal ; ×1,7143 vertical |

L’adaptation du guide sert à analyser la silhouette ; ce ne sont pas les textures natives qui sont redimensionnées. Le choix arbitraire d’un canevas 2048 × 1536 n’est toutefois **pas un étalonnage de la taille des falaises par rapport à un Pokémon ou à une carte en jeu**.

La carte originale `metano_town.rsground` a été relue, avec blob vérifié `38d178520e95d2b1f17d57c12682579d9e37bbae` :

- `TexSize = 1` ; grilles de terrain 189 × 189 ;
- 35 646 cellules Base et 2 169 cellules Cliffs placées aux mêmes coordonnées que leurs références source ;
- les cellules natives de 8 px ne sont pas agrandies individuellement dans ces couches originales.

Cela **ne permet pas de mesurer la caméra ni l’import de la carte cible de l’utilisateur**. La valeur `TexSize` du Ground original ne doit pas être interprétée isolément comme un réglage de zoom caméra.

Les hauteurs des bandes rocheuses retenues aux passages de cascade sont de 128–216 px selon la zone. Ce ne sont ni les hauteurs de toutes les falaises, ni une preuve que leur volume apparent est correct. Aucun facteur global « tout est deux ou huit fois trop petit » n’est établi.

## 2. Cause confirmée : assemblage à trop petite unité

Dans `source/build_zones_guidees.py`, boucle de reconstruction :

- L’unité de choix est une cellule **8 × 8**, et non un module complet de falaise.
- Les corps sont remplis par un motif natif de **64 × 48 px**, répété suivant les coordonnées globales de la carte.
- Les ombres sont approximées par le choix des colonnes sources **85, 86 ou 92**, chacune large de **8 px**, répétées horizontalement. Cela réutilise une tranche de retour rocheux au lieu de son ensemble cohérent.
- Les bordures sont choisies cellule par cellule selon un masque de couleur et une pénalité locale de raccord. Il n’y a pas de règles garantissant une couronne continue, un pied correctement orienté, ou une succession cohérente de faces et de retours.
- Le vocabulaire du reconstructeur ne contient que 148 motifs RGBA distincts autorisés, sur 381 motifs distincts dans la feuille Cliffs complète. La restriction exclut notamment des éléments indésirables ; ce n’est pas en soi une faute, mais elle réduit les possibilités d’assemblage.

**Effet visible dans le comparatif :** relief original plus continu ; reconstruction composée de fragments, colonnes répétitives et bordures irrégulières. Les pixels des pierres ne sont pas nécessairement plus petits ; c’est notamment le volume d’ensemble qui se décompose en petits morceaux.

### Indice quantifié de modification des raccords

Le script compare les paires de tuiles voisines, par contenu RGBA, à celles présentes dans la feuille native placée dans Métano :

| Zone | Paires horizontales absentes du modèle natif | Paires verticales absentes |
|---|---:|---:|
| Cirque | 54,65 % | 43,17 % |
| Terrasses | 42,98 % | 32,00 % |

**Attention : ces pourcentages ne sont pas des taux de défaut.** Une nouvelle disposition légitime ou une répétition peut créer une paire absente de la référence. Ils établissent seulement que copier les bonnes tuiles n’a pas préservé leur grammaire d’assemblage.

## 3. Les calques n’ont pas causé une réduction supplémentaire

Le découpage multicalques déplace des cellules entières entre des couches disjointes. Les empreintes des compositions de référence sont inchangées. Le contrôle précédent a relu PNG, Aseprite et Tiled et obtenu les mêmes images.

Cependant, le calque de bordure est simplement une **bande périphérique d’une cellule, donc 8 px**. Il ne restitue pas, à lui seul, un module natif complet de rebord. Si on l’utilise isolément en jeu, ce n’est pas une falaise complète.

Pour reconstituer une scène sèche, il faut les trois couches **sol + parois + bordures**, au même canevas et à la même origine. La version humide ajoute **berges + rivière + cascades**. Une omission ou une mise à l’échelle indépendante reste une hypothèse à vérifier dans le projet cible.

## 4. L’aperçu pouvait masquer le problème

- Une carte de 2048 px affichée entière dans un panneau beaucoup plus petit est réduite à un facteur généralement non entier.
- Le nearest-neighbor conserve des bords nets mais ne rend pas un facteur fractionnaire fidèle : des détails peuvent disparaître ou être surreprésentés.
- Les comparatifs réduits et les GIF ne sont pas des textures d’import.
- Les sorties du générateur n’étaient pas étalonnées à la densité de détail native. Leur relief séduisant ne constituait donc pas une garantie que le convertisseur de tuiles produirait le même rendu au zoom du jeu.

La comparaison doit se faire à **100 % natif ou ×2 entier**, puis dans le moteur avec un repère de taille, pas uniquement en vue entière.

## 5. Hypothèses d’import encore ouvertes

Sans capture et sans fichier importé, il serait incorrect d’attribuer le problème à un réglage précis du moteur.

| Symptôme | Vérification utile |
|---|---|
| Toute l’image est plus petite, pas seulement le relief | Dimensions après import, facteur d’échelle, caméra, unités du moteur |
| Flou général ou pixels irréguliers | Rééchantillonnage, filtrage, zoom fractionnaire ; limite de résolution ou compression si l’importeur en utilise |
| Motifs coupés/décalés | Découpe de l’atlas à 8 px, marges, espacement, coordonnées et index des tuiles |
| Falaises réduites à des contours minces | Présence du calque parois, ordre des couches et échelles identiques |
| Halos ou ombres anormales | Traitement alpha droit/prémultiplié, surtout sur l’eau ; pas de diagnostic confirmé ici |
| Très mauvais détail partout | Vérifier qu’il ne s’agit pas d’un GIF réduit, d’une planche comparative, d’une capture ou du prototype généré |

### Informations nécessaires pour terminer l’audit moteur

1. Le **chemin ou nom exact du PNG/atlas importé** ; idéalement le fichier tel qu’il est dans le projet après import.
2. Une capture en jeu avec un Pokémon visible, et une capture de Métano au même zoom avec le même repère si possible.
3. L’outil et les réglages utilisés pour l’import : taille de cellule, échelle/zoom, dimensions de la texture obtenue, ordre des calques.

Une comparaison du rapport `largeur du même module / hauteur du même sprite Pokémon` aidera à distinguer taille du décor et zoom de caméra. Aucun facteur de correction ne doit être choisi à l’aveugle.

## 6. Correction recommandée — pas encore appliquée

**Conserver le générateur et les compositions approuvées, corriger la reconstruction.**

1. Relever dans Métano des modules entiers : face, sommet, pied, retour gauche/droit, courbe et raccord de cascade.
2. Mesurer leur taille native et les comparer à un repère en jeu. Ne pas confondre cellule moteur de 8 px et taille du module graphique.
3. Adapter les silhouettes du guide à ces modules, plutôt que remplir chaque petite cellule indépendamment. Les déformations doivent porter sur la géométrie de placement, pas sur les pixels natifs.
4. Conserver les groupes de cellules et les ombres continues. N’allonger les faces qu’avec des bandes explicitement répétables et des raccords validés.
5. Décliner ensuite en calques sans modifier les groupes ; garder la méthode générateur → ressources Métano.
6. Tester **un seul échantillon en jeu** avant de refaire toutes les zones. Valider taille, détails, alpha, bords et ordre des couches.

**Ne pas agrandir tous les PNG ×2 ou ×3 pour masquer le défaut** : cela agrandirait également l’herbe et l’eau, sans réparer les raccords et sans prouver une correspondance avec Métano.

## Reproduire cet audit

```sh
.venv/bin/python source/audit_zones_metano.py /chemin/metano_town_palika.rsground
```

Sans le Ground original, le script audite les assets disponibles et signale son absence. Les sources natives sont épinglées dans la provenance du pack. Les résultats ne sont pas un test exécuté dans la carte cible de l’utilisateur.
