# Provenance des nouvelles références

## Synchronisation

Le travail part des derniers commits de la branche fixe `arena/01a082db-guilde-treehouse-pmd` :

- `0ebe42c` : reprise entière de la guilde au générateur, rêve 3D plein viewport et premiers GIFs déjà présents ;
- `6cf427c` : références `232024.png` et `2cwdrrs469f61.gif` ;
- `bc3afc6` : autre falaise littorale, version nocturne du poste Bekipan et planche de l’étang.

L’ancien état local a été sauvegardé avant l’avance rapide sur ces commits. Les ajouts distants n’ont pas été écrasés. Les références utilisateur d’origine restent intactes à la racine du dépôt.

## Dessins générés

Quatre compositions de jour ont été redessinées au générateur, à partir des références fournies, en demandant explicitement l’absence de structures et d’objets artificiels. Une cinquième génération produit le fond de nuit du littoral, sans terre ni bâtiment : ciel étoilé, pleine lune et mer avec réflexion.

Les fichiers `generation_jour.png` et `generation_fond_nuit.png` conservent les sorties retenues, réduites au plus proche voisin au format natif puis limitées à une palette de 256 couleurs. Les sorties brutes grand format et les guides de travail ne sont pas requis pour reconstruire les exports.

- **Littoral** : les deux références de 3840 × 2400 sont adaptées en 512 × 320. Le guide retire déjà le grand bâtiment pour ne pas le réintroduire par imitation. Le générateur enlève aussi panneaux, clôtures, poteaux et souches. Le chemin et le cap restent lisibles.
- **Plateaux** : la première image du GIF 504 × 504 fournit les terrasses latérales, les fleurs, le passage central et les montagnes dans la mer de nuages. Aucun élément artificiel n’a été ajouté.
- **Étang** : la zone de jeu `(8,8)-(464,632)` de la planche est isolée, sans sa palette ni son pied de page. Les couleurs de cycle non rendues sont remplacées par de l’eau et de l’écume naturelles. La plateforme, ses pas et les poteaux sont retirés.
- **Cascades** : seule la première composition de la planche est prise comme guide, puis adaptée en 592 × 448. Pas de colonnes de comparaison, de magenta ou de panneaux de palette dans le décor livré.

Ces nouvelles illustrations sont des réinterprétations de références PMD, pas une promesse d’identité pixel pour pixel ni un tileset officiel.

## Séparation et palettes

`prepare_paysages_nouveaux.py` utilise masques colorimétriques, cadrages d’auteur et GrabCut avec graine fixe pour séparer fond, eau et terrain. Les cascades ont des zones de flux définies ; les régions rocheuses sont protégées contre une découpe erronée en eau. Les masques d’eau, de fond et de terrain restent disponibles dans les sources.

Les trois plans partitionnent la composition. Les reflets sont extraits de l’eau, le fond sous eux est estimé par inpainting, et leur réintégration retrouve **exactement la composition de jour normalisée**. Les dessins ne sont pas reconstruits en assemblant des fragments de sols de référence.

Le littoral dispose d’une pleine lune et d’étoiles réellement séparées en RGBA du ciel nocturne généré. Le reflet de lune est également séparé de l’eau. Pour les autres cadrages montrant du ciel, les astres de la banque existante sont repositionnés et réduits uniformément, sans aplatir la lune. Les nuits de terrain sont dérivées de la palette du projet ; elles ne sont pas présentées comme trois nouvelles générations de nuit.

Les arbres et les roches du premier plan sont regroupés avec le terrain. Le ciel peint et ses nuages peuvent être regroupés dans le fond. Ces limites sont indiquées pour ne pas laisser croire que chaque objet ou nuage est un sprite indépendant.

## Exports et contrôles

`rebuild_paysages_nouveaux.py` emploie le même exporteur Aseprite/Tiled que les falaises existantes, avec cels liés et courtes phases d’effets. Le contrôleur de l’aperçu lit les mêmes données. Les vérifications couvrent les deux palettes, les recompositions, les couches masquables, les liens d’exports, la lune fixe, le hors-ligne et plusieurs largeurs mobiles. L’absence de structures est vérifiée visuellement, pas par un détecteur automatique.

Les quatre GIFs proviennent des vrais calques composés, pas d’une vidéo de référence réutilisée. Le GIF du rêve et la reprise EoS de guilde déjà présents sont conservés et leurs modules ont été revérifiés.
