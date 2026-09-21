# JG1 — Jungle, entrée + fin de donjon

Deux nouvelles zones de **la jungle H14P01**, pas une jungle générique : tronc violet/brun et racines dorées, eau turquoise, palmes retombantes, herbe verte, fleurs rouges et boutons jaunes. Aucun ciel, rayon lumineux ou temple ajouté. Les dix anciennes études V2 restent historiques, non utilisées pour produire ces calques. La finale ocre de l’étude est remplacée ici par une nouvelle proposition verte, sans supprimer l’ancienne.

## Cinq vrais groupes par carte — 456×336, Ground8

1. Sol herbeux **opaque et continu**, y compris sous tous les décors.
2. Bordures boisées / palmes, transparentes hors végétation.
3. Eau : une piste indépendante de13PNG,6ticks/phase (60Hz).
4. Grand tronc, racines et, pour l’entrée, ouverture de la grotte.
5. Fleurs et végétation basse sur leur propre plan transparent.

Ordre de recomposition :1→5. Les cartes n’ont pas été découpées en partitions d’une image aplatie : deux guides puis huit générations indépendantes de plans ont été réalisées. Sol et bordures sont partagés pour la continuité du lieu ; eau, arbre et fleurs diffèrent. Les scènes ont de réels chevauchements. Le ZIP inclut les PNG de chaque groupe, les indices d’eau, les aperçus, le manifeste, les références natives et un assembleur Pillow autonome.

Entrée : arrivée sud, approche sèche entre deux bassins, grotte au nord. Finale : large clairière, bassin et tronc fermé au nord, retour sud ouvert. Zone centrale200×88 sans décor dans la finale ; trajet sud→devant la grotte et dégagement conservateur8px contrôlés. Ce sont des indications visuelles, **pas** une validation de collisions ou warps PMDO. Aucun Pokémon ni combat préplacé.

## Ajustements des créations, jamais des natifs

Les sorties du générateur ne respectaient pas exactement les emplacements demandés. Les groupes complets ont donc été normalisés/replacés, pas des morceaux de cartes assemblés en remplacement de la génération : arbres ajustés en proportions préservées ; les deux nouvelles flaques de l’entrée tournées de90° puis réduites ; bassin final réduit sans rotation. Ces transformations concernent **uniquement des créations**, jamais les références natives.

La guirlande centrale indésirable de `fleurs_fin` est retirée comme composante entière ; les deux bordures inférieures sont conservées et normalisées. Les plantes centrales de `fond_palmes` ne sont pas utilisées, seules ses composantes de bordure le sont. Bboxes et choix de composantes sont consignés. Les bordures qui touchent le cadre ne sont pas présentées comme des objets mobiles dont le hors-champ aurait été reconstitué.

Les créations sont alignées sur les couleurs de la référence. Sol généré atténué RGB×0,86 puis quantifié sans tramage sur sept couleurs d’herbe du rectangle natif[144,176,312,264] ; autres plans fixes sur la palette visible native. Ce n’est pas une recoloration des sources canoniques.

## Vraie animation de palette, géométrie adaptée

H14P01 n’a pas de météo externe ni BPA. Sa BPL anime les banques2,4,8 : **13phases×6ticks =78ticks =1,3s**. La forme des nouveaux bassins est générée, puis indexée sur les couleurs1/4/6/9/11 de la banque4. Les valeurs et cadences de cette banque sont réemployées exactement dans les26PNG d’eau. Alpha et indices spatiaux restent fixes : cycle de palette, **pas** déformation d’onde ni défilement simulé. Ne pas annoncer ces bassins comme des pixels natifs à1×.

Les13références complètes H14P01,456×336, sont conservées sans rotation, redimensionnement ou recoloration, et comparées au décodage original. Trois fichiers natifs et leur décodeur sont dans le ZIP. Sources publiques épinglées : PMD-Red-PC-Port cd07abc4307e67373a522941308a935bd15241b0 ; pret/pmd-red89c65d9c152b9aab37abe660c14e4505e9bd941a. SHA dans `native/provenance.json`. RGBA issus des palettes, pas une capture du GPU.

Trois WebP directs : entrée, finale et duo, chacun13frames100ms, boucle complète1,3s. PNG d’import sans perte ; WebP de présentation avec compression. `python assemble.py --tick 0 --out assembled` après extraction recompose les deux cartes ; tick arbitraire accepté.

## Reproduction, publication, tests

Depuis la racine du dépôt :

```
.venv/bin/python source/jungle_pmd_v1/restore.py --restore
.venv/bin/python source/jungle_pmd_v1/restore.py --build --verify
.venv/bin/python source/jungle_pmd_v1/restore.py --serve --port 8014
.venv/bin/python source/jungle_pmd_v1/restore.py --http-check --port 8014
```

Dépendances de build : Pillow, NumPy, SciPy ; assemblage du pack : Pillow uniquement. Le lanceur charge la version épinglée du code complet depuis **l’historique Git local**. Pour respecter le budget de livraison déjà presque plein, sources complètes,10bruts lossless et gros rendus restent dans les commits d’archive, avec index/SHA ; ils ne sont ni perdus ni hébergés ailleurs. Garder l’historique Git complet (un clone shallow ne suffit pas). Cache restitué dans `.cache/jungle_pmd_v1/`, SHA vérifiés ; aucun ancien export retiré ou modifié.

Tests : provenance RGBA des10bruts ;13références natives identiques ;26frames adaptées conformes à la banque ; sol continu/chevauchements/cheminement ; basenames uniques et Ground8 ; recomposition autonome ; vraies boucles WebP ; conservation de tous les anciens rendus. Tests techniques ≠ validation artistique ou PMDO.

Ce lot apporte **2cartes**, soit14/22livrées, sans prétendre que les premières cartes ont rétroactivement les nouveaux sols continus. Restent quatre duos : Mont Discipline, plaines sauvages, forêt secrète, plaines brûlées. Forêt précédente, café, Beach et références préservés. Aucun nouveau mobilier dans ce lot.
