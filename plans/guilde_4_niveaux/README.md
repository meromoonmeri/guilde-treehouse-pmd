# Plan canonique et audit — formes arrondies

**[Ouvrir le rapport interactif](index.html)** · [PDF](rapport.pdf) · [Plan complet PNG](plan_canonique.png) · [Plan SVG](plan_canonique.svg)

## Décisions de référence

- **RDC + 3 étages**, trois pièces existantes par niveau.
- Entrée historique **terrasse nord ↔ 01**, conservée au niveau supérieur.
- Chaîne héritée **01 → 02 → 03**, rendue explicite par les paliers et leurs trémies.
- Une seule porte : **02 nord ↔ 12 sud**.
- **Contours arrondis et organiques** : varier largeur, profondeur, taille et alcôves courbes, pas passer à des pièces polygonales.

| Niveau | Pièces |
| --- | --- |
| R+3 | 01 accueil, 06 veilleur, 11 éclaireurs |
| R+2 | 02 missions, 12 chef, 07 résidents |
| R+1 | 03 commune, 04 cantine, 05 équipe |
| RDC | 08 apprentis, 09 grand dortoir, 10 explorateurs |

## Données utilisables

- `plan_canonique.json` : 22 zones, 22 liaisons réciproques, formes et ports.
- `transitions_a_integrer.json` : 44 directions de transition et leurs unités ; ce ne sont pas des triggers moteur installés.
- `controle_plan.json` : connexions, niveaux, trémies, arrondis, gabarits et tests négatifs.
- `mesures_assets.json` : mesures effectuées sur les images et masques actuels.
- `prototype_tremie/` : ouverture ovale réellement générée, trois plans, jour/nuit et masque non praticable.

Les trois petits recalages de points et les trois rectangles d’action corrigés figurent dans le plan. Les pixels des douze pièces n’ont pas été changés pour faire passer le test.

**Statut : plan complet, pack d’assets et moteur encore incomplets.** Sept zones de circulation attendent un master conforme ; deux autres peuvent partir de la galerie générée avec adaptation de raccord. Trois trémies supérieures et l’échelle basse de P0 restent à intégrer. La terrasse jouable, le personnage, les collisions de mobilier et la logique moteur ne sont pas fournis ici.

Méthodes et commandes : `source/audit_jouabilite/README.md`.
