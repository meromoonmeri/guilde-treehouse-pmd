# Entrées glacées — trois chemins sud → grotte au nord

**[Planche jour/nuit](PLANCHE_ENTREES_GLACE.png)** · **[Atelier animé, calques activables](index.html)** · **[Kit PNG / ORA / frames](ICE_ENTRY_V1_pack.zip)**

## Les trois layouts

| Zone | Composition | Scène de jour |
|---|---|---|
| **Seuil du Givre** | Approche directe, clairière large, grotte centrale au nord | [PNG](01_seuil_du_givre/ICE_ENTRY_V1_01_seuil_du_givre_scene_jour.png) |
| **Anse des Neiges** | Chemin courbe autour d’un massif central, grotte au nord-est | [PNG](02_anse_des_neiges/ICE_ENTRY_V1_02_anse_des_neiges_scene_jour.png) |
| **Col des Aiguilles** | Approche en S, grande aiguille à droite, grotte au nord-ouest | [PNG](03_col_des_aiguilles/ICE_ENTRY_V1_03_col_des_aiguilles_scene_jour.png) |

**768 × 640 px**, jour/nuit. Les trois chemins partent du bord sud et atteignent le seuil d’une vraie bouche de grotte dessinée. Les trajets sont indiqués dans le manifest et peuvent être affichés en vert dans l’atelier. Le cyan est un **chemin de glace compactée**, pas une rivière ; aucune eau animée n’y est ajoutée.

Les images initiales et toutes les corrections restent dans `bruts/`. Le troisième chemin a été prolongé jusqu’au sud ; le sommet de son aiguille a été repris pour supprimer sa coupure horizontale. Le premier essai de sous-couche neige trop granuleuse est conservé mais **non utilisé** ; la livraison emploie `sol_neige_doux.png`.

## Calques réellement séparés

Chaque zone dispose de **cinq PNG de terrain par ambiance** :

1. `01_sol_avec_chemin` — sol complet reconstitué sous les reliefs, avec le chemin visible ;
2. `02_profondeur_grotte` — intérieur sombre de la bouche, indépendant de son encadrement rocheux ;
3. `03_cliffs_reliefs` — falaises, encadrement de grotte et massifs ;
4. `04_immersion_gauche` — bordure rocheuse du premier plan gauche ;
5. `05_immersion_droite` — bordure rocheuse du premier plan droit.

Les calques partagés sont dans `climat/` : **ciel jour/nuit, étoiles jour/nuit, bande de nuages jour/nuit, 10 frames d’onde canonique, 8 frames alternatives V12**. Les `.ora` assemblent **neuf plans** : ciel, étoiles, onde phase0, cinq plans de terrain, nuages phase0. Les ORA sont des projets statiques éditables, pas un format d’animation moteur.

Tous les plans, sauf les bandes de nuages (1440 × 208) et l’alternative V12 (768 × 256), sont alignés en **768 × 640, position `(0,0)`**. Les bandes se placent en `(0,0)` également ; aucune mise à l’échelle nécessaire.

**Limite des découpes :** les surfaces visibles sont conservées après quantification et recomposent exactement le terrain. Le sol caché est une sous-couche générée, pas un sol authentique retrouvé. Les faces cachées des reliefs ne sont pas reconstruites : ce sont des plans de scène, pas une banque d’objets complets déplaçables arbitrairement.

## Ciels et nuages : les sources validées, pas celles de Caps/Terrasses

Référence correcte retrouvée : **Guilde/Sharpedo, commit `c16efe12d74361df5ba8625abb68260f5f8fc6dd`**, conservée dans `source/cote_dix_zones/reference_autre_agent/`.

- **Ciel jour/nuit :** moitié gauche sans lune incrustée, répétée en miroir suivant la méthode déjà employée par Dix Zones. Aucun resampling ; lignes inférieures prolongées si nécessaire.
- **Six familles de nuages :** rectangles natifs complets réespacés sur **1440 × 208**, ni redessinés ni agrandis. La nuit emploie la formule Guilde/Sharpedo validée, pas un filtre Abyss rajouté.
- **Étoiles :** extraites du plan `astres_nuit_native`, moitié sans lune répétée à sa taille native. Plan statique indépendant. Le plan étoiles de jour est transparent.
- Les aurores ne sont jamais incrustées dans ces ciels.

Le lot précédent de falaises Métano a également été **corrigé avec ces mêmes bonnes sources**, sans changer ses terrains.

## Nuages en wrap overlay

Déplacement horizontal vers la gauche à **4 px/s**. Période de **1440 / 4 = 360 s**.

```text
décalage = floor(temps_ms × 4 / 1000) modulo 1440
x des copies = −décalage, 1440−décalage, …
```

Le lecteur affiche les copies jointives nécessaires, sans ping-pong ni fondu pour cacher un saut. C’est un **overlay indépendant** dessiné après les reliefs. Le ciel et le terrain ne défilent pas. Le raccord modulo est testé à plusieurs décalages, y compris 1439 → 0.

## Onde boréale : deux choix, sans wrap

### Choix par défaut — texture canonique, 10 frames

Les dix poses de `renders/effet_boreale_canonique_v10/couches/` sont réutilisées : texture issue de `aurorepmdsky.png`, mouvement d’onde adapté dans le lot V10. Les petites composantes détachées de moins de 40 pixels sont retirées pour ne pas garder les points étoilés résiduels dans l’onde. Pas de ciel derrière, pas de redessin ni de resampling. Pose centrée à `(120,0)` sur le canevas complet.

**10 PNG RGBA × 160 ms = 1,6 s**, plus WebP transparent sans perte. Ce mouvement est une adaptation déjà produite, **pas un cycle officiel extrait du jeu**. Le dessin peut être masqué par les falaises comme un phénomène situé derrière elles.

### Alternative — palette cycling V12

Les huit PNG du dernier lot V12 sont copiés **byte pour byte** : silhouette fixe et palette qui circule, **8 × 120 ms = 0,96 s**. Aucun ciel V3 ne les accompagne. C’est un **dessin généré**, pas une extraction native. Cette alternative se choisit dans l’atelier ; les ORA et les scènes PNG montrent le choix canonique par défaut.

Les deux cycles divisent exactement les 360 secondes de la boucle nuages : pas de rupture supplémentaire au retour de l’horloge commune.

**GIF/WebP de scène :** dix frames pour montrer l’onde, **nuages fixes à la phase0**. Le wrap indépendant se voit dans le lecteur HTML et se configure avec la recette du manifest ; aucun film de six minutes redondant n’est livré.

## Matières canoniques et génération : distinction

Références réellement données au générateur : `iceroadpmdsky.png` et `pmdskyicearena.png`. Les nouvelles compositions ont été générées sur magenta, détourées, puis ramenées à la palette RGB réunie de ces deux références. **Les couleurs viennent des références, mais les motifs de glace et les grottes sont redessinés, pas des tuiles natives certifiées.** Aucun assemblage de morceaux de captures n’a été utilisé pour construire ces nouvelles zones.

Terrain généré **1264 × 848**, normalisé uniformément en nearest-neighbor vers **763 × 512**, posé à `(2,128)` dans un canevas **768 × 640**. Les 128 pixels supplémentaires en haut sont réservés au ciel indépendant. Les petites marges latérales restent transparentes, sans étirement anisotrope. Nuit terrain : formule Abyss habituelle ; le climat garde ses propres sources nuit validées.

## Import et contrôles

- `PNG to Tileset` : grille **8 px**, 96 × 80 cellules pour les plans 768 × 640, marge/espacement zéro, pas de lissage.
- Utiliser les PNG de calques, **pas** la planche ni les images `scene`, les masques de contrôle ou les bruts magenta.
- Bande de nuages : ressource de fond/overlay répétée horizontalement, **pas** un tileset de terrain. Adapter sa vitesse aux unités du moteur.
- Les noms `ICE_ENTRY_V1_*` sont uniques pour éviter les écrasements par basename.
- Définir collisions, entrée de carte, seuil et destination du donjon dans votre projet. Aucun `.rsground`, `.tile`, warp ou script natif n’est fourni.

**140 contrôles de fichiers PASS** : références/palette, alpha, recomposition, neuf plans des ORA, nuit, 10 frames d’onde, WebP sans perte, sources V12 intactes, ciel/étoiles/nuages exacts, wrap et connexité des trois corridors de **13 px de large** jusqu’au seuil. Les tracés verts sont des contrôles géométriques sur les masques, **pas** des collisions validées dans le moteur.

Ces trois propositions attendent l’examen utilisateur. Aucune validation de rendu GPU, d’échelle en jeu, de navigation PMDO ni d’intégration de donjon n’est revendiquée.

[Manifest et recette des animations](manifest.json) · [Scripts, reproduction et vérifications](../../source/entrees_glace_v1/README.md).
