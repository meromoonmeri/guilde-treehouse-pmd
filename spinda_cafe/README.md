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

## Fichiers produits

| Fichier | Taille | Usage |
|---|---|---|
| `spinda_cafe_taille_halcyon.png` | 221 × 131 | image complète (tapis compris) à la bonne échelle |
| `spinda_cafe_batiment.png` | **208 × 93** | bâtiment seul, recadré — la façade à la taille de Halcyon |
| `spinda_cafe_pmdo_grille8.png` | 208 × 96 | calé sur la grille 8 px → **26 × 12 cellules**, prêt à découper en `.tile` |
| `spinda_cafe_comparaison.png` | — | côte à côte avec la référence |
| `cafe_halcyon_reference.png` | 208 × 101 | la façade Halcyon extraite, pour contrôle |

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
python3 ../tileset_pmd/redim_spinda_cafe.py spindacafevFINAL.png
```
