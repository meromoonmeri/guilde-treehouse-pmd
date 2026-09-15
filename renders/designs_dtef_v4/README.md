# Designs originaux — ruines, glace, château, forêt sombre

Quatre familles nouvellement dessinées par le générateur, et non de simples recolorations :
- **Ruines** : monolithes cendrés sculptés, mousse olive, fragments de dallage ancien.
- **Château** : maçonnerie ardoise bleu-gris, petits détails bordeaux, dalles et marques héraldiques usées.
- **Glace** : facettes turquoise laiteuses, ombres lavande, givre et branches prises dans la glace.
- **Forêt sombre** : feuillage d’if profond, racines noueuses, champignons discrets, terre moussue.

Les deux planches générées de `bruts/` fournissent quatre matières de mur et quatre matières de sol. Elles sont intégrées à des **géométries d’autotiles PMDO existantes** (Sealed Ruin, Vast Ice Mountain, Murky Forest), pas à des formes de raccord inventées au hasard. Les motifs mur/sol sont remplacés par les donneurs générés, avec une petite modulation d’ombre issue de la tuile de base pour garder le volume.

Trois variantes complètes par famille. La bordure4px partage le même échantillon entre variantes ; les intérieurs changent. Les silhouettes alpha viennent de la variante native0. Le terrain Secondary et ses éventuelles animations restent issus de la source et sont copiés aux trois variantes pour ne pas figer l’eau quand une autre variante est choisie. La forêt sombre conserve ainsi ses séquences d’eau natives ; les trois autres familles utilisent les terrains secondaires statiques de leur source.

**Ce sont des designs personnalisés, pas des tilesets canoniques intacts.** La géométrie empruntée, les matières générées et les animations natives sont des provenances différentes.

## DTEF
`RAW/TileDtef/d4_<famille>_<jour|nuit>/` contient les PNG DTEF432×192 : Wall / Secondary / Floor,6×8cases par type,47cases utiles +1vide, tuiles24px. Même mapping que l’audit Sakura. `tileset_0/1/2.png` sont des variantes, les fichiers `frame<couche>_<index>.<duree>.png` sont les couches d’animation ; durées en frames de jeu.

Sur une copie de test de PMDO :
```
./PMDO -raw "/chemin/vers/le/pack/RAW/" -convert autotile
```
Commande documentée, **non exécutée**. Ne pas importer ces DTEF comme une feuille PNG8px ni aplatir leurs dossiers. Les préfixes `d4_` évitent de remplacer les ressources originales. Les collisions et règles de génération de donjon ne sont pas configurées.

84PNG DTEF,4familles ×jour/nuit. Nuit exacte Abyss. Les WebP de démonstration sont des extraits répétés de2s ; les fichiers DTEF conservent les durées sources. Les animations complètes sont prévisualisées dans la galerie calculée.

Références de géométrie et provenance : `source/donjons_dtef_v2/references/` ; source native DumpAsset pin `3e767571f9dd94270b848b3a73de9bec2553a2eb0`. Droits des ressources natives conservés à leurs auteurs/contributeurs et ayants droit. Scripts : `source/designs_dtef_v4/build.py` et outils communs `source/tours_saisons_v1/`.
