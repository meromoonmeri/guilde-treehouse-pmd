# Antre — bassin animé V4, petite plateforme native

Correction de la V3. Le choix explicite de l’utilisateur est de garder les pierres **immobiles** et d’animer les rides/reflets de l’eau autour d’elles.

## Changements
- Le disque central généré de 160 × 106 px est remplacé par le **disque natif de 72 × 53 px**, sans redimensionnement. Il est ancré au-dessus des trois pas japonais, conservés à leur échelle native.
- Les parois et bordures Crooked de la V3 sont conservées pixel pour pixel.
- Le bassin est **régénéré en quatre poses distinctes** avec de petites rides. Il ne s’agit plus de répéter un carré d’eau essentiellement uni. Les poses partagent une palette de 12 couleurs pour éviter les variations de teinte.
- Les cascades sont **régénérées en quatre poses**, guidées par les références natives. Leur pied s’élargit légèrement et chevauche l’écume pour supprimer la rupture entre les deux effets.
- Le cycle complet de **8 poses natives** de l’eau autour du disque et des trois pas japonais est récupéré et séparé des pierres.

## Référence native importante
Dans la carte `altere_pond.rsground`, la couche Objects utilise huit frames de `Metano_Town_Animation_Tileset` pour le disque et les pas japonais, avec `FrameLength=10`. Elles sont disposées sur deux rangées de quatre dans l’atlas : pas horizontal de 112 px et vertical de 144 px, rectangles de 112 × 144 à partir de (0,984).

La V3 avait extrait les pierres à la première pose sans réutiliser ce cycle complet. La V4 corrige cette omission. **Les pixels des pierres sont identiques dans les huit poses** : les changements concernent l’eau et ses reflets/ombres. Les quatre calques d’eau autour des pierres et les quatre calques de pierres se recomposent exactement en chaque sprite natif, à l’échelle 1, après placement et occultation par les roches.

Source Halcyon : Altere Pond, commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51`, carte archivée dans `source/antre_harmonie_v3/references/`. Atlas Métano archivé dans `source/eau_metano/natifs/`. Le manifeste contient la preuve de séquence issue de la carte, les rectangles source et le SHA256 du fichier `.tile` utilisé.

## Animation et provenance honnête
Cadence : 10 frames de jeu par pose (1/6 s à 60 Hz).
- Bassin : **4 poses générées**, dans le style de l’eau d’Altere. Ce ne sont pas des frames natives retrouvées.
- Cascades : **4 poses régénérées/adaptées**. La silhouette et la jonction claire au pied viennent de la nouvelle génération ; la matière du corps mélange 70 % de détail natif avec 30 % de la pose générée, puis est ramenée à la palette native cascade/écume. Cette contribution native diminue au pied pour conserver le raccord généré. Elles ne sont donc **pas des sprites canoniques intacts**.
- Écumes : **3 poses natives Métano**, récupérées dans la carte Altere, ajustées à 50 % au plus proche voisin comme dans V3. Elles restent indépendantes des cascades.
- Eau autour des pierres : **8 poses natives exactes**, sans recoloration ni redimensionnement.

La boucle commune fait **24 poses**, soit **240 frames de jeu / 4 secondes**. Le WebP utilise des durées de 167/166/167 ms calculées à partir des horodatages cumulés, sans dérive. Les textures de chute ne sont pas simplement scrollées. Les poses du bassin constituent une animation artistique, pas une simulation physique d’écoulement ou des vitesses hydrodynamiques.

## 25 calques alignés — 480 × 312
**8 statiques** : paroi du fond, bordures gauche/droite, rebord bas, disque natif, trois pas japonais.

**17 animés** : bassin ; rides/reflets du disque ; rides/reflets des trois pas ; six cascades ; six écumes.

Les effets aquatiques sont masqués contre les rochers et les pierres sèches. Les chutes gardent les ouvertures et les pieds ajustés de V3 ; leur largeur augmente localement au contact. Chaque cascade possède une zone de recouvrement réelle avec son écume à chaque état temporel.

## Fichiers
- `../../apercu_antre_bassin_v4.html` : galerie animée autonome, sélection de chaque calque.
- `antre/COMPOSITION.png`, `antre/ANIMATION.webp` : état initial et boucle complète.
- `antre/antre_bassin_v4.ora` : 25 calques, état initial.
- `antre/bassin4_*.png` : 24 compositions et toutes les phases plein cadre alignées. Les cycles courts sont répétés pour une chronologie commune.
- `sprites/plateforme_native_complete_*.png` : huit poses natives complètes avant séparation.
- `sprites/bassin_regenere_*.png` : quatre matériaux de bassin finaux.
- `sprites/cascade_generee_pose_*.png` : poses détourées, avant projection du matériau et adaptation au layout.
- `bruts/` : les deux nouvelles générations, conservées.
- `antre_bassin_v4.zip` : paquet avec scripts et toutes les dépendances de reconstruction.

## Vérifications
`verify.py` contrôle : recomposition exacte des 24 scènes opaques ; conservation des parois ; pixels de pierres inchangés ; recomposition exacte des huit poses natives de plateforme/eau ; cycles 4/3/8 ; quatre matériaux de bassin distincts ; absence d’effets sur le sec ; chevauchement de chaque chute et de son écume dans chaque phase ; ORA identique au PNG initial ; WebP à 24 phases.

Ces contrôles ne valent **pas test dans PMDO**. Pas de vérification de collisions, de mouvement du joueur, de combat ou d’import moteur. Les anciennes versions restent intactes. Les ressources natives restent soumises aux droits de leurs ayants droit.

Reconstruction depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/antre_bassin_v4/build.py
.venv/bin/python source/antre_bassin_v4/verify.py
.venv/bin/python source/antre_bassin_v4/package.py
```
