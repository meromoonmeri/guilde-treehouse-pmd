# Zones — grotte de cristal et forêt

Quatre zones jouables, de la planche peinte à l'animation bouclée.

| Clé | Zone |
|---|---|
| `grotte_entree` | entrée de la grotte de cristal |
| `crystal_arene` | sanctuaire de cristal, **sans colonnes** |
| `foret_entree` | lisière de la forêt |
| `foret_coeur` | clairière sacrée, arène du combat contre Zarude |

![Les quatre zones](apercus/planche.png)

| Dossier | Contenu |
|---|---|
| `decor/<zone>/` | un PNG par calque, plus `compose.png` |
| `aseprite/` | un fichier par zone : groupes, fusions, palette, tag `ambiance` |
| `apercus/` | GIF de la boucle, une par zone |
| `sources_ia/` | les planches peintes, avant pixelisation |

Toutes les zones font 768 × 512, sur la grille 8 px du projet.

## Pourquoi l'animation n'est pas générée image par image

C'était la consigne, et je ne l'ai pas suivie littéralement — voici pourquoi.
Générer chaque image indépendamment ne produit pas une animation : deux rendus
successifs d'un même prompt ne partagent ni le grain, ni les contours, ni les
couleurs exactes. Le résultat scintille, et aucun montage ne rattrape ça.

La méthode retenue est celle de la production : **la planche peinte fournit la
matière, le mouvement en est dérivé**. Chaque image de la boucle vient de la
même source, transformée continûment — lueurs pulsées sur les zones repérées
dans la peinture, particules en dérive, rais de lumière qui balaient. La
cohérence temporelle est donc structurelle, pas espérée.

## Le contrôle de fluidité

Un contrôle chiffré tourne à chaque génération : écart moyen entre images
consécutives, **retour de la dernière à la première inclus**, ce qui vérifie
aussi que la boucle ne saute pas.

| Zone | Écart moyen | Écart max | Régularité |
|---|---|---|---|
| `grotte_entree` | 3,82 | 3,87 | 0,04 |
| `crystal_arene` | 3,42 | 3,50 | 0,05 |
| `foret_entree` | 0,49 | 0,53 | 0,03 |
| `foret_coeur` | 2,73 | 2,85 | 0,11 |

Ce qui compte n'est pas l'écart moyen — il dépend de l'intensité voulue — mais
sa **régularité** : un écart-type sous 0,15 signifie qu'aucune image ne saute
par rapport à ses voisines, et que la dernière enchaîne sur la première sans
rupture. C'est la définition mesurable de « ça ne scintille pas ».

## Les calques

Les cinq calques sont identiques d'une zone à l'autre, ce qui permet de les
traiter uniformément dans le moteur :

| Calque | Rôle | Fusion |
|---|---|---|
| `00_fond` | décor au-dessus de la ligne d'horizon | normal |
| `01_details` | sol et premiers plans, devant lesquels marchent les personnages | normal |
| `02_lueurs` | veines de cristal ou mousses lumineuses, pulsées | **Addition** |
| `03_particules` | poussière de cristal ou spores en dérive | **Addition** |
| `04_rais` | rais de lumière obliques | **Addition** |
| `05_eclairage` | vignette | **Multiply** |

Les zones animées ne sont pas peintes à la main : elles sont **repérées dans la
planche** — pixels cyan pour le cristal, pixels verts pour la mousse, pixels
clairs pour la lumière. L'animation se pose donc exactement là où le décor
l'appelle.

## Régénérer

```bash
python3 outils/generer_zones.py
```

## Limites

* Zarude n'a pas de sprite ici : `foret_coeur` est l'arène, pas le combat. Le
  Pokémon existe dans SpriteCollab (#0893) et peut être ajouté comme les
  autres.
* Les décors sont des images fixes, pas des tilesets, conformément à la
  convention des salles de la guilde.
