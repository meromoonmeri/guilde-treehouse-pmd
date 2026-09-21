# WP1 — Plaines sauvages, entrée + finale

Deux nouvelles zones de **H06P01** : prairie vert-jaune ouverte, collines et ciel bleu conservés dans les deux cartes, petits rochers ocre. Pas de murs/terrasses qui enferment la prairie, pas de forêt ajoutée, pas de Pokémon ou personnage.

## Cinq groupes par carte — 456×336 / Ground8

1. **Ciel et nuages natifs**,18phases indépendantes du terrain.
2. **Collines et lointain natifs**,18phases sur le même compteur BPL que le ciel.
3. **Prairie générée continue**, opaque partout dèsy112, sous rochers et herbes.
4. **Rochers générés**, deux petits groupes latéraux à l’entrée ; repère plus grand au nord de la clairière finale, petit groupe de galets sur le côté.
5. **Herbes basses générées**, éparses aux bords, sud dégagé.

Deux compositions-guides puis six générations de plans distincts. Les guides ne sont pas découpés en partitions visibles pour fabriquer des faux calques. Le sol existe derrière les décors, il chevauche le plan lointain entrey112 et128. Le ciel/collines vient de la référence native partagée, pas de nouvelles générations prétendument natives.

Entrée : progression depuis le sud vers le haut de la prairie. Finale : grand espace dégagé216×88 devant les rochers-repères, retour au sud. L’horizon est un décor lointain, **pas un passage moteur au bord nord**. Les points d’accès/warps restent à définir dans PMDO. Contrôle conservateur de dégagement8px, pas une validation de collisions, combats ou pathfinding moteur.

## Créations et pixels natifs : séparation explicite

Les six plans générés sont détourés du magenta, normalisés nearest à456×336 et rapprochés de la palette native. Entre les lignes112 et159, seules les couleurs du **nouveau sol** sont alignées progressivement sur les moyennes de couleur du lointain ; la référence native n’est ni recolorée, ni redimensionnée. Les groupes complets de rochers générés sont réduits proportionnellement et déplacés, sans rotation ni miroir ; tailles/rectangles et positions dans le manifeste. Aucun fragment de carte natif n’est transformé pour servir de rocher nouveau.

Le fond natif est séparé par un masque fixe : pixels du ciel bleu/blanc repérés sur l’ensemble des18phases ; complément pour les collines/lointain dans les128premières lignes. Chaque pixel opaque de ces deux banques reste **exactement à sa coordonnée et à son échelle1× d’origine**. Les deux plans recomposent ensemble exactement le haut de H06P01. Ce sont des fonds ancrés au cadre, pas des objets dont le hors-champ est reconstruit. Les18références complètes sont également incluses.

## Animation réelle de palette — boucle1,2s

H06P01 n’a pas de BPA ni de météo externe. Sa BPL déclare banque0:10phases×4ticks, banques1/7:18phases×4ticks. Les10entrées de la banque0 sont **identiques** ; elles n’ajoutent pas d’animation visible. La période visuelle est donc **72ticks =1,2s**, vérifiée sur les90états du cycle déclaré global360ticks.

18phases sources produisent17états RGBA distincts ; les poses répétées et leur durée restent présentes. Il s’agit du scintillement natif des couleurs du ciel et du lointain, pas de nuages déplacés artificiellement ni d’herbe animée inventée. Garder ciel et collines synchronisés. Trois WebP animés directs : entrée, finale, duo. Encodage **sans perte**, boucle complète1200ms ; l’encodeur peut fusionner des poses adjacentes identiques en conservant leur durée. Les PNG de toutes les phases restent séparés.

Sources publiques : PMD-Red-PC-Port cd07abc4307e67373a522941308a935bd15241b0 ; pret/pmd-red89c65d9c152b9aab37abe660c14e4505e9bd941a. Trois fichiers natifs, décodeur et SHA256 dans le ZIP. RGBA de palettes décodées, pas capture GPU.

## Import et reproduction

65PNG, dont les plans transparents ; banque native partagée entre les deux cartes, sans duplication de fichiers. Canevas divisibles par8 et basenames uniques. `python assemble.py --tick 28 --out assembled` après extraction (Pillow) recompose un état quelconque.

Depuis le dépôt, Pillow/NumPy/SciPy pour build/tests :
```
.venv/bin/python source/plaines_pmd_v1/restore.py --restore
.venv/bin/python source/plaines_pmd_v1/restore.py --build --verify
.venv/bin/python source/plaines_pmd_v1/restore.py --serve --port 8016
.venv/bin/python source/plaines_pmd_v1/restore.py --http-check --port 8016
```
Le lanceur épingle code, index et documentation dans l’historique Git ; bruts lossless et livraisons archivés, restitués avec contrôle SHA dans `.cache/plaines_pmd_v1/`. Un historique Git complet est nécessaire (pas seulement un clone shallow). Les gros fichiers ne sont pas conservés uniquement dans le cache. Les anciens exports publiés restent inchangés.

Tests : huit bruts exacts,18références décodées,36plans natifs exacts, période réelle sur90états, sol continu/chevauchements, chemins, Ground8, assembleur, WebP sans perte et durées. Tests techniques ≠ accord artistique ni validation PMDO.

## Suivi honnête

Ce lot ajoute deux cartes et porte la branche publiée à16cartes. Le Mont Discipline a été montré au tour précédent, mais son push avait échoué ; ses commits non publiés n’étaient pas dans le checkout restauré. Ne pas le compter comme poussé ni le remplacer silencieusement. Sa publication reste à récupérer séparément. Restent à créer les duos forêt secrète et plaines brûlées. Aucun nouveau mobilier dans ce lot.
