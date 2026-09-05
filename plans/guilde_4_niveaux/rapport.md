# Guilde Treehouse — audit et plan canonique interne

**6 septembre 2026 · RDC + trois étages · contours arrondis conservés**

## Verdict

**Le plan de connexions est complet et vérifié ; le pack n’est pas encore prêt à être déclaré jouable dans un moteur.**

Les douze pièces sont affectées, les 19 accès actuels ont une destination unique, la porte du chef reste au bon endroit et les trois liaisons verticales ont un haut et un bas explicites. En revanche, plusieurs circulations n’ont pas encore de décor généré conforme, les trois trémies supérieures ne sont pas intégrées, et le dépôt ne contient ni moteur, ni personnage final, ni logique de transition installée.

**Arrondi ne veut pas dire identique.** On garde les courbes du langage PMD et du bois de notre guilde. Les différences viennent de la largeur, de la profondeur, de la taille et de petites alcôves courbes — pas de chambres en L anguleux, de rectangles ni de pans coupés. La proposition en L a été écartée ; aucun natif de salle n’a été remplacé par cette proposition.

## 1. Ce qui existe réellement

| Élément | État constaté |
| --- | --- |
| 12 pièces | Présentes, avec bases et calques jour/nuit |
| 24 Aseprite des pièces | Fichiers fixes, 11 emplacements de calques |
| 19 repères d’accès | Reliés au sol principal avec une empreinte de pieds de 16 px |
| 6 panoramas | Présents ; ce sont des fonds de fenêtres, pas une terrasse jouable |
| Banque originale | 135 sprites, gardés séparés des pièces vides |
| Nouvelle banque | 20 objets, 32 tuiles de parquet, 16 spirales |
| Couloir réellement généré | Une galerie est-ouest traitée, avec PNG, calques, Aseprite et Tiled 8 px |
| Anciennes circulations procédurales | Rejetées ; ne sont pas comptées comme nouveaux décors conformes |
| Trémie arrondie | Nouveau prototype réellement généré, détouré et réparti en trois plans ; pas encore posé dans les paliers |
| Collisions, transitions et PNJ | Aucun moteur fourni dans ce dépôt ; intégration non réalisée |

Le mobilier n’est pas « oublié » dans les pièces : leur état vide était voulu. Il faut toutefois poser les objets et définir leurs empreintes avant de valider la circulation meublée. Les anciennes paillasses de 78 × 56 px et les nouvelles de 48 × 32 px ne doivent pas être mélangées sans choix d’échelle.

## 2. Référence canonique du projet

Le plan ci-dessous est **le canon interne proposé pour notre guilde**, pas une reproduction officielle à quatre niveaux de la guilde de Grodoudou. La référence PMD sert à la lecture des passages, des courbes, des profondeurs et des échelles. Dans le jeu d’origine, l’entrée mène par échelle à un premier sous-niveau, puis à un second ; le projet Treehouse reste sa propre architecture. [4](https://m.bulbapedia.bulbagarden.net/wiki/Wigglytuff%27s_Guild)

### Ordre des sources

1. Choix utilisateur : **RDC + 3 étages**, conserver les accès extérieurs existants, **formes arrondies**.
2. `source/regles_acces.json` et `kit.json` : ouvertures et porte autorisées aujourd’hui.
3. `source/base_kit.json` : historique des destinations.

L’historique décrit **01 N → terrasse**, **01 S → 02**, **02 échelle N → 01**, **02 S → 03** et **03 échelle N → 02**. Il contient aussi l’ancienne porte 03 NE → 12, devenue obsolète : la règle actuelle impose **02 porte N ↔ 12 S**. C’est cette dernière qui prévaut.

Pour respecter cette chaîne, l’accueil reste au niveau supérieur, côté terrasse. **Aucune nouvelle entrée extérieure au RDC n’est inventée.** Le RDC désigne ici le niveau intérieur le plus bas.

## 3. Répartition des quatre niveaux

| Niveau | Fonction | Pièces |
| --- | --- | --- |
| **R+3** | Accueil et surveillance | **01** accueil · **06** veilleur · **11** éclaireurs |
| **R+2** | Missions et administration | **02** hall des missions · **12** chef · **07** résidents |
| **R+1** | Vie commune et équipe | **03** salle commune · **04** cantine · **05** chambre de l’équipe |
| **RDC** | Dortoirs | **08** apprentis · **09** grand dortoir · **10** explorateurs |

Trois pièces par niveau, quatre paliers et cinq instances de couloirs. Les codes C/P sont des espaces de circulation, pas des pièces oubliées ni des nouveaux accès extérieurs.

### R+3 — accueil

- Terrasse sud ↔ **01 nord**.
- **01 sud ↔ P3 nord**, palier d’accueil arrondi.
- **P3 ouest ↔ C3O est**, puis **C3O nord ↔ 06 sud** : retour courbe vers le veilleur.
- **P3 est ↔ C3E ouest**, puis **C3E est ↔ 11 ouest** : galerie vers les éclaireurs.
- **P3 trémie ↓ ↔ 02 échelle nord ↑**, au R+2.

### R+2 — missions

- **02 porte nord ↔ 12 sud** : la seule porte visible. Fermée visuellement ne veut pas dire verrouillée par défaut ; l’interaction peut déclencher le passage sans inventer une seconde porte dans le bureau.
- **02 ouest ↔ C2R est-bas**, puis **C2R est-haut ↔ 07 ouest**.
- C2R est un **retour courbe à deux bouches est distinctes**, pas deux destinations sur un même port.
- **02 sud ↔ P2 nord**, puis **P2 trémie ↓ ↔ 03 échelle nord ↑**, au R+1.

### R+1 — vie commune

- **03 ouest ↔ C1O est**, puis **C1O ouest ↔ 04 est** : cantine.
- **03 sud ↔ P1 nord**, puis **P1 ouest ↔ 05 est** : trajet court vers la chambre de l’équipe.
- **03 est ↔ C1R ouest-haut**, puis **C1R ouest-bas ↔ P1 est** : petite boucle alternative, entièrement courbe.
- **P1 trémie ↓ ↔ P0 échelle ↑**, au RDC.

La boucle n’impose aucun détour : le passage sud direct reste disponible pour les trajets quotidiens.

### RDC — dortoirs

- **P0 ouest ↔ 08 est**.
- **P0 est ↔ 10 ouest**.
- **P0 sud ↔ 09 nord**.
- **P0 échelle ↑ ↔ P1 trémie ↓**.

La salle 09 garde son passage nord en retrait ; il ne devient pas une échelle. La salle 12 garde son seul accès sud et son tronc architectural sans fausse échelle nord.

## 4. Trémies : ce qui doit être dessiné et ce qui doit être bloqué

Trois descentes hautes sont requises : **P3 vers 02**, **P2 vers 03**, **P1 vers P0**. Les échelles de 02 et 03 sont déjà des extrémités basses montantes. La troisième échelle basse, en P0, manque encore.

Une descente conforme doit montrer :

- une **ouverture arrondie réellement découpée dans le plancher** ;
- l’épaisseur du bois et les parois intérieures plus sombres ;
- les premiers barreaux **sous le niveau du sol**, puis leur disparition dans l’ombre ;
- un rebord avant pouvant passer devant le personnage ;
- une zone d’approche libre, sans plante ni meuble sur le déclencheur.

Le vide n’est pas un sol praticable. L’action « Descendre » se lance depuis le palier, pas en marchant librement dans le trou. À l’autre extrémité, le personnage apparaît sur le sol sûr, **hors déclencheur**. Réarmement seulement après sortie de zone, relâchement de la touche et temporisation de 300 ms : pas d’aller-retour instantané.

Le [prototype généré arrondi](prototype_tremie/apercu_4x.png) fournit un exemple concret, une zone non praticable et trois calques : parquet évidé, puits/échelle, rebord avant. Sa recomposition est exacte. Ses deux points de pieds ont été contrôlés à **16 px**, mais ses coordonnées sont locales : **il ne remplace pas les trois paliers manquants**.

## 5. Jouabilité mesurée, pas supposée

### Gabarits

Les masques de sol réels ont été testés avec des empreintes carrées de 16, 24 et 32 px, sans mobilier. Un repère doit appartenir à une composante praticable reliée au sol principal.

| Pieds | Repères actuels reliés au sol principal |
| --- | ---: |
| **16 × 16 px** | **19 / 19** |
| **24 × 24 px** | **16 / 19** avant recalage |
| **32 × 32 px** | **14 / 19** |

Les trois échecs à 24 px se corrigent **dans les rectangles existants**, sans changer les formes :

| Repère | Ancien point | Point retenu dans le plan | Correction |
| --- | --- | --- | --- |
| 03 ouest | (8, 263) | **(8, 265)** | +2 px en y |
| 03 échelle nord | (324, 220) | **(324, 221)** | +1 px en y |
| 04 est | (639, 270) | **(639, 267)** | −3 px en y |

Les **19 repères du nouveau plan et ses 19 points d’arrivée** passent alors le contrôle en 24 px. Ces coordonnées sont ajoutées au plan d’intégration ; les métadonnées et pixels des anciens assets n’ont pas été modifiés silencieusement.

Trois rectangles historiques ne contenaient pas le point de pieds retenu. Ils sont **recentrés dans le plan canonique**, sans déplacer le dessin :

| Zone | Ancien rectangle x, y, largeur, hauteur | Rectangle canonique |
| --- | --- | --- |
| 01 nord | (300, 141, 48, 24) | **(300, 166, 48, 24)** |
| 09 nord | (300, 141, 48, 24) | **(300, 166, 48, 24)** |
| Porte du chef en 02 | (1031, 212, 52, 16) | **(1031, 225, 52, 16)** |

Le vérificateur impose désormais que le point d’interaction soit dans son rectangle canonique et que l’arrivée soit à l’extérieur. Ce sont de nouveaux contrats d’intégration, pas des triggers déjà actifs dans le jeu.

À 32 px, il faut davantage que déplacer trois points : les cols latéraux de 03/04 ne permettent pas de rejoindre le corps principal avec ce gabarit. Les zones d’action des échelles 02/03 seraient également à étendre ou recaler. Cela ne signifie pas que les salles doivent devenir anguleuses : au besoin, on **élargit les raccords courbes par génération**, ou on calibre l’empreinte réelle du personnage.

### Confort

- Hypothèse de travail : pieds de **16 px**, dessin du personnage autour de 32 px, à vérifier avec le sprite final.
- Cible confortable : passages de **48 px** et zone libre de **32 px** devant les accès.
- Les bords latéraux de 03/04 ne font que **37/36 px** dans les repères visuels : ils fonctionnent pour un petit gabarit, mais n’offrent pas le même confort de croisement avec un PNJ.
- Ne placer aucun PNJ stationnaire sur un seuil, devant une échelle ou dans un palier d’arrivée.
- Valider à nouveau après pose des lits, tables, coffres et plantes ; un fond vide ne prouve pas la jouabilité meublée.

### Trajets quotidiens

Assembler idéalement **une scène par étage**, avec ses pièces et couloirs. Les modules ne doivent pas provoquer un chargement à chaque raccord.

- Équipe **05 → missions 02** : un changement d’étage.
- Équipe **05 → cantine 04** : même étage.
- Missions **02 → chef 12** : même étage, une interaction de porte.
- Équipe **05 → terrasse** : deux échelles et la sortie extérieure, soit **trois changements de scène cibles** avec l’organisation recommandée.

Ce sont des budgets topologiques, pas des temps de parcours mesurés. Il manque le moteur, la vitesse et le personnage final pour certifier l’agrément en jeu.

## 6. Formes arrondies : varier sans changer la DA

La mesure compare la silhouette extérieure à taille égale, en comblant les fenêtres **pour l’analyse uniquement**, et retient le meilleur score normal/miroir.

- **05 / 07 / 11 : silhouette identique, IoU 1,00**, à miroir près.
- **08 / 10 : silhouette identique, IoU 1,00**, à miroir près.
- **01 / 06 : IoU ≈ 0,996**.

Le problème n’est donc pas leur rondeur, mais leur répétition. Le plan garde douze profils arrondis différenciés : accueil court, grand hall très large, salle commune souple, cantine allongée, chambre d’équipe à alcôve courbe, veilleur quasi rond, résidents asymétriques, apprentis à niches douces, grand dortoir évasé, explorateurs en profondeur, éclaireurs compacts et bureau autour du tronc.

Ces profils sont des **briefs de génération**, pas l’affirmation que les douze nouvelles images sont déjà produites. Les axes et dimensions exacts doivent être réglés en gardant la même caméra et l’échelle du parquet, pas par étirement arbitraire d’un PNG.

## 7. Ombres et lumière des accès

Les contrôles existants des douze pièces passent : ombres et reflets présents, effets localisés, centre des passages dégagé et reflets nocturnes atténués. Cela valide des propriétés des fichiers, **pas une certification artistique officielle PMD**.

Règles à appliquer aussi aux futurs couloirs et trémies :

- contacts au pied des retours, joues et rebords ;
- léger rebond chaud sur l’arête éclairée ;
- nord en retrait : profondeur sombre et sol continu, pas une fausse porte ;
- trémie : intérieur plus sombre, épaisseur lisible et barreaux en profondeur ;
- nuit : même géométrie, reflets réduits, sans halo uniforme ;
- **aucune barre noire traversant tout le chemin**.

La galerie générée conserve une partie de son ambiance dans les textures ; son calque d’éclairage supplémentaire est vide. Elle ne doit pas être comptée comme un modèle entièrement rééclairable. Les interfaces entre modules doivent encore être harmonisées à la pose.

## 8. Priorités avant de dire « prêt en jeu »

| Priorité | À faire | Pourquoi |
| --- | --- | --- |
| **P0** | Générer P3, P2, P1 avec trémies et P0 avec échelle basse | Les liaisons verticales n’ont pas encore tous leurs décors |
| **P0** | Générer les retours courbes C3O/C2R/C1R | Leur topologie est définie, pas leur image conforme |
| **P0** | Adapter la galerie générée aux deux instances C3E/C1O | Gabarits de raccord, ombres et jonctions à vérifier |
| **P0** | Installer collisions, interactions et réarmement des transitions | Le plan n’est pas un moteur |
| **P0** | Fournir/brancher la carte jouable de terrasse | Les panoramas ne sont pas une carte de navigation |
| **P1** | Appliquer les trois recalages de points, les trois rectangles et choisir le gabarit final | Empêcher un mauvais point d’interaction sans déformer les salles |
| **P1** | Différencier les quasi-doublons par proportions et courbes | Garder l’identité arrondie sans tout répéter |
| **P1** | Poser le mobilier et ses collisions, tester les PNJ | Valider les passages réels, pas seulement les fonds vides |
| **P1** | Tester la lecture jour/nuit et l’occultation du personnage | Vérifier murs, rebords, trémies et grandes silhouettes |

Infirmerie, stockage, bibliothèque ou services de boutique ne sont pas ajoutés arbitrairement comme nouvelles pièces : aucune demande de gameplay ne les fixe dans ce dépôt. Si nécessaires, les intégrer comme zones fonctionnelles des pièces existantes ou les décider séparément.

## Contrôles et livrables

- `plan_canonique.json` : référence des quatre niveaux, formes, ports et liaisons.
- `transitions_a_integrer.json` : 44 sens de transition, explicitement **à intégrer**.
- `controle_plan.json` : 22 zones connectées, 22 liaisons réciproques, trois paires verticales, aucun accès orphelin ; six tests négatifs détectent les plans invalides.
- `mesures_assets.json` : mesures des silhouettes, repères et trois gabarits sur les images actuelles.
- `prototype_tremie/` : prototype réellement généré, natif, calques, masques et contrôles.
- `source/regles_direction_artistique.json` : arrondis et génération d’images explicitement imposés.

Les anciens constructeurs de décors procéduraux sont maintenant **bloqués par défaut** pour éviter de réintroduire la méthode et les formes rejetées. Une reproduction historique reste possible uniquement avec `GUILDE_REPRODUIRE_LEGACY=1`. Le traitement des images réellement générées reste disponible via `source/hallways/generations/exporter_methode_origine.py`.

Les natifs, les douze images de salles, leurs calques et les banques de sprites restent inchangés par cet audit. Les scripts dessinent le **schéma technique**, jamais de nouveaux décors de jeu.
