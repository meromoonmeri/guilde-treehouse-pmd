# Zones approuvées — exports multicalques comme pour la guilde

## Méthode conservée

L’utilisateur a approuvé les deux compositions et demandé de conserver la méthode **générateur pour la composition → reconstruction en tuiles Métano natives**. Cette préférence est enregistrée dans `AGENTS.md`.

Après `git fetch origin`, le dernier commit de `main` consulté est `6c4ac5a` (guilde : 12 salles, passages ouverts, calques PNG, Aseprite et Tiled). Le dernier commit local de cette branche est `7f1e82b` (kits Métano et grands layouts). Aucun changement de branche ni de géométrie des zones approuvées n’a été effectué.

L’export reprend les conventions du kit de la guilde : calques nommés et ordonnés, canevas commun, PNG RGBA, fichiers Aseprite éditables, grilles de 8 px, cartes Tiled et contrôle par recomposition. Les calques de fenêtres/portes propres aux intérieurs ne sont pas artificiellement ajoutés au terrain.

## Voir et éditer

**`apercu_zones_multicalques.html`**, à la racine : aperçu autonome avec six cases de visibilité, boutons « Seul », tout afficher/masquer, version sèche/animée, quatre phases, pause, zoom 100 % / 200 %, grille et export des calques visibles en PNG transparent.

**`planche_multicalques.png`** : vue des six calques de chaque zone, réduits sur un fond vert de contrôle.

Dans **`01_cirque/multicalques/`** et **`02_terrasses/multicalques/`** :

| Ordre | Calque | Fichiers PNG |
|---|---|---|
| 1 | Sol : herbe Métano | `01_sol.png` |
| 2 | Parois rocheuses | `02_parois.png` |
| 3 | Bordures et retours de falaises | `03_bordures.png` |
| 4 | Berges et fond statique de rivière | `04_berges.png` |
| 5 | Surface de rivière animée | `05_riviere_phase_1.png` à `4.png` |
| 6 | Cascades animées | `06_cascades_phase_1.png` à `4.png` |

Tous les PNG partagent le canevas **2048 × 1536 px** et l’origine **(0, 0)**. Les calques supérieurs sont transparents hors de leur contenu ; le sol forme le fond opaque. Aucun décalage manuel n’est nécessaire.

- `zone_seche.aseprite` : 3 calques, **1 frame fixe**.
- `zone_eau_animee.aseprite` : 6 calques, **4 frames de 167 ms**, avec cels liés à la première frame pour les calques fixes.
- `zone_seche.tmj` : 3 couches de tuiles.
- `zone_eau.tmj` : 6 couches de tuiles, animation via l’atlas canonique existant.

Les cartes Tiled emploient des données base64/zlib standard. Conserver le dossier parent `sprites/zones_guidees/` avec `Zones_Guidees_Canon_8px.tsj` et `.png`, car les cartes les référencent par un chemin relatif. Le `.tile` PMDO et les métadonnées d’animation existants sont réutilisés, sans nouvel atlas.

Les anciens exports et archives restent inchangés. **Le ZIP précédent ne contient pas cet ajout multicalques** : utiliser les nouveaux dossiers et l’aperçu dédiés.

## Découpage et fidélité

Le découpage déplace des **cellules entières de 8 × 8 px** vers des couches disjointes. Il ne redessine aucun pixel.

- Les bordures sont la bande périphérique d’une cellule autour du masque de falaises, incluant sommets, pieds et retours. Ce n’est pas une classification d’autotiles ni une carte d’occlusion pour les personnages.
- Les tuiles de cascade sont distinguées des tuiles de rivière par leur feuille source canonique, pas par une retouche de couleur.
- Les berges contiennent des pixels d’eau statiques présents dans Métano. Pour retrouver la version sèche, désactiver **les trois** calques aquatiques.
- Les ombres restent intégrées aux tuiles originales ; pas de nouvelle ombre peinte sur un calque artificiel. Pas de variante nuit recolorée.
- La réunion des couches donne exactement les PNG approuvés ; leurs empreintes SHA-256 sont conservées dans `multicalques.json`.

## Reconstruction et contrôles

```sh
.venv/bin/python source/build_zones_multicalques.py
.venv/bin/python source/verify_zones_multicalques.py
.venv/bin/python source/package_zones_multicalques.py
```

Ces commandes ne rappellent pas le générateur et ne reconstruisent pas les silhouettes. Elles utilisent les zones existantes validées. Les dépendances de production restent Pillow et numpy, avec scipy pour le pipeline de génération de terrain initial.

`verification_multicalques.json` confirme :

- contrôle préalable des 7 sources natives et des 9 731 entrées d’atlas ;
- aucune cellule perdue ou dupliquée lors des séparations parois/bordures et rivière/cascades ;
- aucune modification des PNG approuvés ;
- relecture indépendante des fichiers Aseprite, y compris les cels liés ;
- relecture et décompression des cartes Tiled ;
- **0 différence de pixel**, pour chaque calque PNG/Aseprite/Tiled et les compositions sèches / quatre phases humides.

Le JavaScript du visualiseur a passé le contrôle syntaxique Node. Le test dans Chromium n’a pas pu être exécuté : téléchargement du navigateur bloqué par une erreur réseau TLS. Pas de validation interactive dans les applications Aseprite/Tiled ni de test d’intégration PMDO. Les collisions et transitions restent à configurer.

## Crédits

Palika et contributeurs de **Palikadude/Halcyon**, commit source `da6c2130d641507447e6386a5e47a296e8cb4c71`. Animations de rivière créditées à **Jaifain**. Compositions nouvelles et non officielles ; respecter les droits et conditions des ressources originales. Voir également le README et la provenance du pack initial.
