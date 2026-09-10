# Café Spinda — mis à l'échelle du café de Halcyon

## La mesure de référence

La taille cible n'a pas été estimée à l'œil : elle a été obtenue en reconstruisant
réellement les assets de `Palikadude/Halcyon`.

1. `Data/Ground/metano_town.rsground` — la carte de Metano Town (189 × 189 cellules).
2. Le café y est localisé par son objet `Cafe_Entrance`, en `X=1144 Y=592`.
3. Les calques `Objects*` ont été rendus sur cette zone avec les tuiles de
   `Content/Tile/Metano_Town_Objects.tile`, puis la plus grande composante
   connexe a été isolée pour ne garder que le bâtiment.

> À noter : `Metano_Town_Cafe*.tile` et `metano_cafe.rsground` sont **l'intérieur**
> du café (456 × 320 px). La façade recherchée est dans les objets de la ville.

**Façade du café de Halcyon : 208 × 101 px**, soit 26 cellules de 8 px de large.

## Le calcul

| | Largeur | Hauteur |
|---|---|---|
| Bâtiment source (`spindacafevFINAL.png`, tapis exclu) | 400 px | 179 px |
| Référence Halcyon | 208 px | 101 px |
| **Facteur appliqué** | **0,52** | — |

L'échelle est **uniforme** (0,52 sur les deux axes) : les proportions du dessin
sont conservées. La largeur tombe exactement sur 208 px. La hauteur donne 93 px,
soit 8 px de moins que les 101 px de la référence — c'est normal, ton bâtiment est
un peu moins haut *proportionnellement*. Le forcer à 101 px l'aurait étiré
verticalement et déformé.

## Jeu d'ombre et de lumière sur la porte

L'entrée principale est désormais **fermée visuellement** : on ne voit plus le mur
du fond ni le tapis spiralé à travers l'embrasure. L'ouverture est remplie d'une
ombre noire qui se réchauffe légèrement vers le sol, et une rangée de **petits
demi-cercles dorés** déborde sur le seuil, comme la lumière de l'intérieur qui se
répand devant la porte. C'est le même traitement que la porte du café de Halcyon.

Cette version a été produite par le générateur d'image à partir de
`spindacafevFINAL.png`, puis remise au format exact de la source.

## Unification du style

Le kiosque de gauche était dessiné dans un style plus doux que l'aile droite :
dégradés marqués, bois flou, tons beiges éteints, alors que l'aile droite a des
aplats francs, des tuiles nettes et des contours appuyés. **Ce décalage était
déjà présent dans le fichier d'origine**, il ne venait pas de la retouche de la
porte.

Le kiosque a donc été redessiné dans le style de l'aile droite : mêmes tuiles
rouge/orange saturées, même liseré doré net, aplats au lieu de dégradés. La
silhouette, la tête de Spinda, le comptoir, les fioles, le panier, les mâts et
le tapis gardent leurs positions.

### Affinage du lineart

Le kiosque était cerné de gros traits noirs épais — chaque planche du comptoir
et chaque tuile étaient soulignées — alors que l'aile droite sépare ses formes
par contraste de couleur, avec des traits fins voire absents. Mesuré : 25,8 %
de pixels sombres à gauche contre 20,8 % à droite, et surtout 1 429 segments de
trait à gauche contre 253 à droite.

Le kiosque a été redessiné avec des traits d'1 px dans une teinte plus foncée
de la couleur de l'objet (brun sombre pour le bois, rouge sombre pour le toit)
au lieu du noir.

### Détourage du fond, en qualité pixel-art

Le générateur rend en ~1327×784 pour une cible de 425×251. Réduire en LANCZOS
**moyenne** les pixels : les bords deviennent flous et les couleurs se délavent
(les fioles viraient au sépia). Comparaison avec la référence Halcyon :

| | bords semi-transparents | gradient interne moyen |
|---|---|---|
| Référence Halcyon | **0** | 15,3 |
| Réduction LANCZOS | 2 467 (4,3 %) | 10,2 |
| **Rendu final** | **0** | **12,6** |

La génération est dessinée sur une grille régulière d'environ 3,1 px.
`../tileset_pmd/detourer_magenta.py` rééchantillonne donc par **couleur
majoritaire** de chaque bloc : chaque pixel de sortie reprend une teinte
réellement présente dans la source, jamais une moyenne. Les aplats restent
purs, les bords tranchés, et l'alpha est binaire comme sur un vrai sprite.

Réduire la palette (quantification à 48 couleurs) a été essayé et **écarté** :
cela tuait les couleurs des fioles et faisait virer l'ensemble au sépia.

## Fichiers produits

| Fichier | Taille | Usage |
|---|---|---|
| `spindacafevFINAL_porte.png` | 425 × 251 | **source retravaillée** : porte assombrie + festons |
| `spinda_cafe_taille_halcyon.png` | 221 × 131 | image complète (tapis compris) à la bonne échelle |
| `spinda_cafe_batiment.png` | **208 × 93** | bâtiment seul, recadré — la façade à la taille de Halcyon |
| `spinda_cafe_pmdo_grille8.png` | 208 × 96 | calé sur la grille 8 px → **26 × 12 cellules**, prêt à découper en `.tile` |
| `spinda_cafe_comparaison.png` | — | côte à côte avec la référence |
| `cafe_halcyon_reference.png` | 208 × 101 | la façade Halcyon extraite, pour contrôle |
| `spindacafevFINAL.png` | 425 × 251 | l'original intact, conservé |
| `_generation_brute.png` | 1327 × 784 | sortie brute du générateur, avant détourage |

## Pourquoi LANCZOS et pas NEAREST

`spindacafevFINAL.png` n'est pas du pixel-art 1:1 : il contient **44 971 couleurs
distinctes** et un canal alpha sur 256 niveaux (bords déjà lissés). Les plages de
pixels identiques font majoritairement 1 px de long, donc il n'y a pas de « gros
pixel » logique à préserver.

Dans ce cas `NEAREST` produirait des escaliers irréguliers sans gagner en netteté.
`LANCZOS` conserve mieux le dessin. Si tu repars un jour d'une source réellement
pixel-art (palette réduite, alpha binaire), c'est `NEAREST` qu'il faudrait utiliser.

## Régénérer

```bash
# 1. détourer le fond magenta et remettre au format source
python3 ../tileset_pmd/detourer_magenta.py \
    spindacafevFINAL.png _generation_brute.png spindacafevFINAL_porte.png

# 2. remettre à l'échelle du café de Halcyon
python3 ../tileset_pmd/redim_spinda_cafe.py spindacafevFINAL_porte.png
```
