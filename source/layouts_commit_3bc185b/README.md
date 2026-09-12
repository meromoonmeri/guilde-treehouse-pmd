# Reproduction des layouts réellement ajoutés par l’utilisateur

## Références retrouvées

Commit utilisateur **`3bc185bec2d5aa295f32825927db9d25bb936f75` — « Add files via upload »**, sur `arena/01a095e8-guilde-treehouse-pmd`.

Ce commit n’était pas sur `main`. Il a été récupéré explicitement depuis la branche distante puis intégré par fast-forward, sans écraser les travaux locaux.

- `IMG_4888.jpeg` : promontoire du bureau de Bekipan, ambiance coucher de soleil.
- `IMG_4889.png` : même promontoire, de nuit.
- `IMG_4890.png` : référence en planche de sprites du même lieu, avec mer/ciel.
- `IMG_4892.png` : autre zone, terrasse côtière avec arbres, campement, chemin, grotte et falaise.

Il y a donc **deux layouts distincts**, et plusieurs vues/références du premier. Ce ne sont pas les cirques abstraits et murs en paliers produits précédemment.

## Générations de cette passe

1. **`01_promontoire_bekipan.png`** : génération en journée avec les trois références `IMG_4888.jpeg`, `IMG_4890.png` et `source/falaises_generees/reference_canonique.png`. Consignes : conserver plateau à gauche, mer à droite, bureau de Bekipan, virage du chemin, panneau, arbres, clôtures et stumps ; remplacer l’aspect des parois grises par des roches dorées/rosées inspirées de Métano, avec des formes larges et lisibles.
2. **`02_terrasse_campement.png`** : génération en journée depuis `IMG_4892.png` et la référence Métano. Consignes : mer à gauche, plateau à droite, chemin horizontal, bannière, feu de camp, deux arbres, panneau, souche, clôture, rebord inférieur et grotte principale. Une seconde passe du générateur a corrigé une grande fissure noire parasite au pied de la falaise.

Les fichiers PNG sont les véritables sorties du générateur. Leur composition a été inspectée. Les formes suivent les références, mais leur reproduction n’est pas pixel-identique. La variante nocturne `IMG_4889.png` est conservée comme référence ; elle n’a pas été régénérée dans cette passe de deux scènes diurnes.

## Statut important pour PMDO

**Ce sont des reproductions générées de layout, pas des PNG canoniques certifiés pour l’import en jeu.** Une consigne et une référence ne garantissent pas la palette exacte, la netteté native, l’échelle des sprites ou les raccords. Ces sorties ne sont ni des extractions des tuiles Métano, ni des calques séparés, ni des animations.

Il ne faut pas confondre ces propositions avec le lot de calibration **`sprites/metano_import_png/`**, qui utilise des blocs natifs copiés et vérifiés. Le passage éventuel de ces layouts côtiers à un pack de jeu doit conserver leurs structures en reconstruisant les matériaux avec les sources appropriées, et être validé dans PMDO. Les tests des tuiles canoniques ne s’appliquent pas aux pixels de ces deux images générées.

Les originaux du commit utilisateur restent inchangés à la racine. Les dimensions et empreintes des entrées/sorties sont enregistrées dans `manifest.json`.
