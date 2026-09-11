# Falaise côtière — prairie sur la mer

Seconde scène indépendante, **504 × 384 px**, grille **8 px**. Une prairie et son chemin dominent une **paroi rocheuse naturelle**, avec la mer en contrebas. Il n’y a plus de profil de requin, d’yeux, de bouche ni de mâchoire dans la falaise.

Le nom de dossier `sharpedo/` reste un identifiant historique pour préserver les liens. Dans l’aperçu, la scène s’appelle **Falaise côtière**. Sharpedo Bluff sert désormais de référence de cadrage et de mouvement de mer, pas de forme à reproduire dans la roche.

## Afficher

Ouvrir [`../apercu_falaise.html`](../apercu_falaise.html). L’aperçu s’ouvre sur **Falaise côtière** ; l’onglet **Prairie de la guilde** reste disponible. Choisir **Jour / Nuit**, activer la lecture ou parcourir les images. Le fichier est autonome et fonctionne hors ligne.

## Sept calques

1. `00_ciel` — ciel fixe.
2. `01_astres` — lune fixe et étoiles scintillantes la nuit.
3. `02_nuages` — six familles de nuages en défilement.
4. `03_mer` — profondeur et palette de l’eau, sans les anciens reflets figés.
5. `04_vagues` — **cycle de mer en 10 images adapté de la référence**, sur un overlay transparent.
6. `05_falaise` — nouvelle paroi naturelle, prairie et chemin fixes.
7. `06_decor` — emplacement de décor additionnel, vide.

Le chemin et l’intérieur de la prairie sont conservés pixel pour pixel ; les rives et leurs angles sont retouchés. La nouvelle paroi a été peinte au générateur et sa silhouette inférieure a été remplacée ; l’ancienne mâchoire n’est donc pas simplement masquée par une recoloration.

## Bordures PMD Sky redessinées

Les bordures du cap reprennent le langage des rives de PMD Explorateurs du Ciel : lèvres d’herbe irrégulières, contact de terre fin, pierre ocre fragmentée, angles entrants et sortants. La rive arrière possède son motif N ; les côtés, angles et diagonales sont adaptés au contour existant. L’emprise et le chemin ne changent pas, et aucune bordure ne ferme les prolongements droit/bas.

Le bouton **Tileset bordures PNG** de l’aperçu donne l’atlas de l’ambiance active. Le pack fournit, pour jour et nuit :

- `tilesets/bordures_pmd_*.png` : **20 motifs de 24 × 24 px** ;
- `tiled/bordures_pmd_*.tsj` : noms, familles et orientations des motifs ;
- `tiled/catalogue_bordures_pmd_*.tmj` : toutes les tuiles posées sur une grille de 24 px.

Le tileset est chargé dans la palette des cartes Tiled. Leur contour organique est adapté localement dans le PNG de falaise, pas reconstruit automatiquement en blocs de 24 px. C’est une bibliothèque pour pose manuelle, pas un autotile complet à 47 cases. Pour réutiliser ses motifs, employer une grille de 24 px ou des objets-tuiles. Voir [`../source/bordures_pmd/README.md`](../source/bordures_pmd/README.md).

## Mer : progression de référence, pas un va-et-vient

Les dix images du calque de mer de la carte fournie ont été relues. Le nouvel overlay reprend leur évolution : les bandes d’eau et les crêtes **progressent vers le bas de l’image**, au lieu de déplacer une image unique de quelques pixels dans les deux sens.

- Le témoin de référence ne contient que de l’océan : aucun fragment de falaise ou de créature.
- Sa largeur est prolongée par réflexion continue, pour remplir notre fond sans coupure de couleur. La paroi se superpose ensuite.
- Les variations du cycle sont adaptées au profil de profondeur et à la palette de notre mer générée.
- Le fond d’eau et l’overlay se recomposent sans perte supplémentaire ; leur animation reste indépendante du ciel et du terrain.

La référence indique `FrameLength: 10` en unités du moteur. Les livrables utilisent la cadence commune du kit, **250 ms par image** : **10 phases / 2,5 s**. Le mouvement vient de la référence, sans prétendre reproduire son horloge moteur.

## Boucles et formats

- Nuages : 504 phases à 250 ms, soit **126 s**.
- Étoiles : 24 phases, soit **6 s** ; la lune ne clignote pas.
- Mer : 10 phases, soit **2,5 s**.
- Boucle commune : **2 520 images / 630 s** (10 min 30 s), pour que tous les raccords reviennent exactement au même état. Les vagues n’attendent pas la fin de cette longue boucle : leur cycle court se répète continuellement.

Deux compositions PNG, 14 calques PNG RGBA, bases transparentes/magenta, deux **Aseprite animés** et deux **Tiled animés** sont fournis. Les cels liés évitent de dupliquer les mêmes phases sur toute la timeline. Conserver le dossier `animations/` avec les cartes Tiled ; il contient leurs atlas et les données techniques de source.

## Reconstruction et contrôles

Depuis la racine du dépôt :

```bash
python source/prepare_bordures_pmd.py
python source/prepare_sharpedo.py
python source/prepare_mer_reference.py
python source/rebuild_sharpedo.py
python source/build_preview_falaise.py
python source/verify_falaise.py
python source/verify_falaise_browser.py
```

L’aperçu attend aussi les exports de la première scène. Les préparateurs réutilisent les natives conservées, sans nouvel appel au générateur. Voir [`../source/sharpedo/PROVENANCE.md`](../source/sharpedo/PROVENANCE.md) pour les références et les retouches.

Les contrôles vérifient le chemin et les zones hors bordure conservés, les 20 motifs et leurs catalogues Tiled, la paroi remplacée, les dix phases distinctes de mer, les cycles, les recompositions PNG/Aseprite/Tiled et le rendu navigateur hors ligne/mobile. Les repères Tiled ne constituent **pas** des collisions ou des transitions PMDO intégrées. Aucun fichier `.rsground`/`.tile` n’est livré.
