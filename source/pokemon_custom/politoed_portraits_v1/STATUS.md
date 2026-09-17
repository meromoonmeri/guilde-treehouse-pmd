# Tarpaud — workflow magenta, puis fonds canoniques

- `generation/Happy.png` : **REJETÉ**, ancien essai avant correction de workflow. Fond non magenta et sourire supplémentaire dans la mâchoire jaune, trop humain. Ne pas exporter.
- `generation/*_magenta.png` : dix nouvelles études individuelles effectivement reçues sur fond magenta. Inspection initiale et nettoyage anatomique effectués ; pas d’approbation artistique utilisateur.
- `Sigh_magenta.png`, `Stunned_magenta.png` : demandes bloquées par la limite de10générations. Fichiers absents ; aucune expression de remplacement inventée.

## Méthode exécutée

Normal natif0186→sujet isolé sur magenta pour la référence ; source générée magenta→détourage alpha→nettoyage40×40 limité à l’œil et à la petite région de larmes→composition sur la case exacte du fond canonique. Le sujet natif hors de cette région reste inchangé. La bouche de ce lot fermé reste la jonction du vert et du jaune, pas une ligne de sourire humaine dessinée dans la mâchoire jaune. Les portraits natifs ouverts ne sont pas remplacés.

Le détourage du Normal utilise la connexité au bord pour ne pas effacer l’iris crème qui partage une couleur avec le fond. Le creux de l’antenne est traité séparément. Le code reproductible est `build.py`.

**Livrable local partiel :**14portraits de face (4originaux natifs préservés : Normal, Inspired, Shouting, Surprised ;10candidats nouveaux). Sigh et Stunned restent absents. Pas de vues inverses, de validation PMDO ni de contribution upstream acceptée. Les scènes des autres membres n’ont pas été produites pendant ce lot ; ne pas commencer Team Dazzling avant de finir les manques prioritaires.

Fichiers : `exports/pokemon_custom/politoed_portraits_v1/`, galerie racine `apercu_tarpaud_portraits_v1.html`. Les étapes magenta/alpha/fond sont montrées séparément. Les expressions et la lisibilité des larmes restent à apprécier visuellement : tests techniques ≠ qualité artistique acquise.
