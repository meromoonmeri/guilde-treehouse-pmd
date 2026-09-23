# Audit des escaliers — implantation nord/sud

**Périmètre : quatre accès entre trois niveaux.** Le plan ci-dessous remplace les propositions latérales et les anciens marqueurs d’escaliers au milieu des salles. Les V4 et prototypes sont conservés comme historiques ; ils ne définissent plus le plan V5 actif.

[Voir le plan annoté](Audit_escaliers_nord_sud.jpg) · [Coordonnées et destinations](plan_escaliers.json) · [Contrôles exécutés](verification.json)

## Placement retenu

| Salle | Escalier nord | Escalier sud |
|---|---|---|
| **Accueil — RDC / 0** | **Montée → café +1** | **Descente → casino −1** |
| **Casino — sous-sol / −1** | **Montée → accueil 0** | Aucun escalier |
| **Café — étage / +1** | Aucun escalier | **Descente → accueil 0** |

Retours réciproques :
- accueil **N** ↔ café **S** ;
- accueil **S** ↔ casino **N**.

Les passages **E/O restent au même niveau** : casino ↔ salon des jeux, café ↔ salon supérieur. Ils ne doivent pas recevoir d’escalier de changement d’étage.

## Problèmes relevés et corrections

1. **Ancien prototype latéral inadapté.** Les essais ouest/est et leurs guides ne correspondent plus à la consigne. Ils sont explicitement déclarés obsolètes. Aucun n’est utilisé par cet audit.
2. **Ancienne documentation encore latérale.** WORKFLOW et consignes de reprise sont corrigés ; `plan_escaliers.json` fait désormais foi pour les quatre accès.
3. **Joint sous les marches nord.** Un premier montage évidait jusqu’à y136 alors que le sprite finit vers y133 : cela laissait du magenta entre l’escalier et le sol. La découpe est arrêtée à y128 ; les marches recouvrent la découpe et rejoignent le sol conservé. Aucun trou sur la bande centrale contrôlée.
4. **Épaules de la sortie sud.** Une découpe trop large créait de petits trous dans les rochers du café. Elle est limitée à la bande de passage ; les rebords sont conservés autour du module.
5. **Retour de niveau obligatoire.** Le sous-sol ne descend pas davantage ; l’étage supérieur ne monte pas vers un étage inexistant. Les quatre destinations et les orientations d’arrivée sont explicites.

## Même escalier, pas un nouveau dessin

L’escalier est repris dans **l’accueil V4 choisi**, à l’échelle600×448 déjà utilisée par les maps. Crop architectural136×80 : `(232,316)–(368,396)`, avec les coins de sol extérieurs au passage masqués. **Les marches ne sont ni tournées, ni étirées, ni recolorées.**

Le cœur des marches `(268,338)–(336,392)` est comparé octet par octet dans les quatre emplacements. La lumière dorée et les ombres restent celles de cette référence. Cette référence provient d’une salle générée choisie par l’utilisateur : elle n’est pas présentée comme un sprite natif officiel.

- **Accueil S :** ancienne entrée entièrement inchangée ; nouvelle fonction de descente au−1.
- **Accueil N et casino N :** module posé en232,56 ; ouverture réelle dans le mur arrière, palier et bords rocheux prolongés jusqu’au bord nord avec des fragments de la même référence. Bas des marches raccordé au sol de la salle, pas posé au milieu de celle-ci.
- **Café S :** même module posé en232,324, décalé pour suivre la bordure avant de cette salle.

Ce sont des retouches locales d’accès sur les bases générées conservées, **pas un agrandissement de map par bandes**. Le reste de chaque salle, notamment les passages latéraux existants, est inchangé. Décor et fenêtres sont omis de la planche afin de lire les accès sans ambiguïté.

## Vérifications réalisées

- Nord : variation de niveau **+1** ; sud : **−1**.
- Deux liaisons d’escaliers bidirectionnelles, avec retour du bon côté.
- Quatre zones de marches RGBA identiques à la référence.
- Bande centrale de40px continûment opaque sur les trajets contrôlés.
- Contacts au pied nord identiques au sol original, sans liseré magenta.
- Empreintes raster16×16 aux déclencheurs et aux points d’arrivée ; coordonnées alignées sur8px.
- Aucune modification hors des trois zones de retouche d’entrée.
- Deux contre-tests : une montée inversée et un trou volontaire sous les marches sont bien rejetés.
- PNG transparents exportés puis redécodés : pixels identiques aux compositions auditées.

**Attention : opaque ne signifie pas automatiquement franchissable dans PMDO.** Le test porte sur l’image et le plan de liaison. Collisions, hauteur, taille des acteurs, triggers et warps restent à configurer puis tester en jeu. Les repères de l’illustration ne sont pas imprimés dans les PNG.

## Point encore ouvert

Les deux sorties de l’accueil sont maintenant des liaisons **internes entre étages**. **Aucune entrée extérieure au complexe n’est définie par ce plan.** Ne pas ajouter arbitrairement une troisième sortie : ce raccord doit être décidé séparément si nécessaire.

Le mobilier, les rubans adaptés et les tapis rouges demandés restent un chantier distinct ; cet audit ne prétend pas les avoir livrés.

## Reproduire / exporter

Depuis la racine du dépôt :

```sh
.venv/bin/python source/cafe_spinda_revisite_v5/audit_escaliers.py
```

La commande reconstruit les trois vues depuis les sources V4 conservées, exécute l’audit et produit dans `exports/` : trois PNG transparents, trois PNG magenta et le module d’escalier. Ces copies sont régénérables et exclues de Git pour ne pas dupliquer les images. Le plan annoté, le manifeste, le rapport et le script sont conservés.

**Aucun `.rsground`, collision, NPC ou warp n’est installé par cette commande.**
