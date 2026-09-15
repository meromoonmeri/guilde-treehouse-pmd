# Falinks #0870 — PMD portraits

Lot au format SpriteCollab/SpriteBot : **16 émotions** et leurs 16 miroirs.

- portraits individuels : `Emotion.png` et `Emotion^.png` ;
- planche importable : `Sheet.png`, 200 × 320 px ;
- fond canonique : `template.png` ;
- chaque case est 40 × 40 px, opaque, 15 couleurs maximum.

## Règles propres au personnage

- **Falinks n'a pas de bouche.** La plaque faciale est lisse : toute l'émotion
  passe par les yeux et les sourcils. Un nettoyage automatique efface toute
  bouche que le générateur aurait dessinée sur la plaque.
- Expressions **sobres et disciplinées**, dans le registre des portraits PMD
  officiels. Pas de grimaces grotesques ni de déformation comique.
- Les personnage est détouré sur clé magenta pure, donc **aucun fond généré ne
  peut baver** sur le fond canonique du template.

## Slots Special laissés vides

Le FAQ SpriteCollab exige qu'un Special soit réellement unique et refuse tout
ce qui se décrit comme « une autre émotion sur un autre fond ». Mes essais
précédents ne faisaient que recycler Determined, Happy, Sigh et Shouting : ils
sont retirés plutôt que soumis en l'état.

Versions précédentes conservées : `portrait/0870_v1_derive/` (dérivée du
portrait publié) et `portrait/0870_v2_generateur/`.
