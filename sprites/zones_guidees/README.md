# Deux zones guidées par le générateur, reconstruites en tuiles natives

## Voir le résultat

- `comparaison_generateur_canonique.png` : propositions générées à gauche, reconstructions à droite. Planche réduite, pas une texture à importer.
- À la racine du dépôt : **`apercu_zones_guidees.html`**, visualiseur autonome. Sélection des deux zones, prototype/sec/eau, quatre phases, pause, grille, zoom natif 100 % / 200 %, téléchargement PNG sans grille.
- `01_cirque/` : **Le cirque des sources** ; `02_terrasses/` : **Les trois gradins**.
- Dans chaque dossier : `canonique_sec.png`, `canonique_eau_1.png` à `canonique_eau_4.png`, quatre calques d’eau `eau_1.png` à `eau_4.png`, `herbe.png`, `falaises.png`, `berges.png`, `sec.tmj`, `eau.tmj`, `zone.json` et `apercu_eau.gif`.
- Les PNG canoniques font **2048 × 1536 px**, grille **8 × 8 px**. La version sèche contient uniquement herbe et falaises, aucune eau ni chemin. Le GIF est une prévisualisation réduite et quantifiée : ne pas l’importer comme source pixel-perfect.
- Atlas : `Zones_Guidees_Canon_8px.png`, `.tile` et `.tsj`. L’atlas conserve aussi des cellules de la bibliothèque candidate non placées dans les cartes.

## Ce qui a été adapté

Le modèle du générateur n’a pas été modifié. Ses **consignes et images de référence** ont été adaptées pour demander deux compositions sèches, une palette proche de Métano, des falaises organiques et aucun bâtiment, chemin ou eau. Référence utilisée : `source/falaises_generees/reference_canonique.png`.

Les deux vraies sorties du générateur sont conservées dans `source/zones_guidees/generateur_01.png` et `generateur_02.png`. Elles sont **des propositions non canoniques**. Le visualiseur en embarque des aperçus JPEG légers ; les PNG originaux restent dans le dépôt.

Le nouvel assembleur analyse ces propositions sur une grille 8 px :

1. Identification de la silhouette rocheuse et des zones herbeuses.
2. Pose du motif d’herbe natif. Remplissage des intérieurs rocheux avec des motifs natifs cohérents, sélection de variantes d’ombre d’après le guide, recherche de tuiles natives de bordure avec pénalité de raccord.
3. Aucun pixel du guide n’entre dans les textures finales. Aucun sprite source n’est repeint, recoloré, étiré, tourné ou retourné. Les calculs de lissage/couleur ne servent qu’à **choisir** des tuiles existantes.
4. Recherche d’un axe traversant trois bandes rocheuses, puis pose des berges, rivière et quatre phases de cascades natives. Les hauteurs de chute sont adaptées en répétant/omettant des rangées de tuiles sources, sans redessiner leurs pixels.
5. Export et vérification indépendante.

La reconstruction reprend les grandes silhouettes, **pas chaque détail ni chaque ombre** du dessin généré. Certains raccords de bordure sont approximatifs ; l’aspect des faces rocheuses est plus répétitif que le prototype. Ce sont des essais de composition en ressources canoniques, pas des cartes officielles ou une validation artistique automatique.

## Preuve de fidélité des tuiles

`provenance.json` associe chaque entrée d’atlas à sa feuille source et ses coordonnées. `verification.json` enregistre les contrôles :

- 7 fichiers sources vérifiés par leur identifiant de blob Git épinglé ;
- 9 731 entrées d’atlas identiques aux tuiles originales, **0 différence de pixel** ;
- conversion PNG à alpha droit réversible vers les pixels natifs prémultipliés, **0 différence** ;
- recomposition indépendante de tous les calques et PNG secs/animés, **0 différence** ;
- versions sèches limitées aux coordonnées autorisées d’herbe et de falaises ;
- quatre phases distinctes par zone et 1 377 animations natives dans l’atlas.

Les jointures, collisions, transitions, navigation et import dans PMDO **ne sont pas certifiés** par ce contrôle de pixels. Les `.tmj` s’ouvrent dans Tiled avec le `.tsj` adjacent. Les métadonnées natives d’animation sont fournies dans `provenance.json`, mais ne constituent pas à elles seules un fichier Ground prêt à jouer. Les cascades utilisent un rythme de quatre phases de 10 ticks ; leur placement et leur longueur sont choisis pour ces nouvelles compositions.

## Reconstruire dans le dépôt

Dépendances : Pillow, numpy, scipy (`source/zones_guidees/requirements.txt`). Les sept fichiers sources natifs référencés dans la provenance sont nécessaires ; ils sont déjà dans ce dépôt. Le ZIP est un pack d’assets et d’aperçu, pas un environnement de reconstruction autonome.

```sh
.venv/bin/python source/build_zones_guidees.py
.venv/bin/python source/verify_zones_guidees.py
.venv/bin/python source/package_zones_guidees.py
```

Le build réutilise les propositions PNG conservées ; il n’appelle pas le générateur d’images. Demander de nouvelles illustrations au générateur produirait une autre proposition.

## Origine et droits

Sources : **Palikadude/Halcyon**, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Crédit à Palika et aux contributeurs ; animations de rivière créditées à **Jaifain** dans Halcyon. Respecter les droits et conditions des ressources originales : leur disponibilité publique ne vaut pas autorisation universelle de redistribution. Les cartes sont de nouvelles compositions non officielles.
