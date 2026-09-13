# Références 54d3731 — entrées de zone, 10 scènes multicouches

## Ouvrir
**`apercu_references_54d3731.html`** à la racine : 10 scènes × 2 ambiances, calques masquables, téléchargement de chaque PNG et de la composition. Tous les rendus sont **statiques**.

[Planche des 10 scènes, base et nuit](PLANCHE_10_SCENES.png)

## Dernières consignes appliquées
- **Première génération** : aucun ajout décoratif demandé au générateur ; grotte replacée dans l’axe de l’accès central, feuillage vert, terre brune et roche gris-brun assortie. Pas de torche, bâtiment ou nouveau mobilier.
- **Friend Areas** : transformation en entrées naturelles tout en conservant leur disposition reconnaissable. Pas de nouvelles maisons, portes construites, ponts ou panneaux.

| Scène | Modification et calques principaux |
|---|---|
| [01 · Entrée forestière verte](01_murky_entree/jour/composition.png) | Sol terreux, roche/racines arrière, feuillage avant, grotte axiale séparée |
| [02 · Clairière Murky Forest](02_murky_clairiere/jour/composition.png) | Seconde disposition de la planche ; sol, arrière-plan, canopée, racines du fond |
| [03 · Armaldo intérieur](03_armaldo_interieur/jour/composition.png) | Sol, parois arrière/avant, foyer statique, mobilier/raccords |
| [04 · Plage](04_plage/jour/composition.png) | Sable, roches arrière, roches/palmiers avant, mer/écume, ciel et astres séparés |
| [05 · Chemin de plage](05_chemin_plage/jour/composition.png) | Chemin/sol visible, arbres arrière, arbres/rochers avant |
| [06 · Mont Foudre](06_mont_foudre/jour/composition.png) | Arène centrale, aiguilles rocheuses, paroi, nuages arrière/avant et ciel |
| [07 · Lisière Energetic Forest](07_foret_energetique/jour/composition.png) | Passage entre les racines face à la clairière ; sol, troncs et feuillage séparés |
| [08 · Entrée Mushroom Forest](08_foret_champignons/jour/composition.png) | Passage naturel sous le grand chapeau, clairière dégagée ; champignons arrière/avant, entrée et tronc séparés |
| [09 · Grotte Waterfall Lake](09_lac_cascade/jour/composition.png) | Ouverture derrière la cascade ; lac et îlot central conservés ; eau, berge, arbres, grotte, rideau d’eau et îlot séparés |
| [10 · Passage enneigé](10_foret_neige/jour/composition.png) | Chemin, montagnes/sapins arrière, sapins avant, ciel et astres séparés ; aucun portail/barrière ajouté |

Chaque dossier contient `jour/` et `nuit/`, les calques PNG et leur `composition.png`. Les dimensions et l’ordre exact figurent dans `manifest.json`. **104 calques exportés**, en toiles communes à chaque scène ; aucun décalage à appliquer pour recomposer une scène.

## Nature des calques
Les couches de terrain sont des **partitions de profondeur du dessin visible**, avec masques spécifiques à chaque scène. Leur recomposition est pixel-identique au terrain détouré. Certains groupes incluent leur raccord au sol ; ce ne sont pas tous des objets indépendants détourés pour un placement arbitraire.

Les surfaces cachées derrière la canopée, les rochers ou les meubles ne sont **pas reconstruites**. Masquer un calque montre donc la transparence sous sa zone ; cela ne signifie pas que la scène possède un sol complet peint sous tous les objets. `terrain_recompose.png` est le contrôle du terrain assemblé et `plan_calques.png` est un masque à indices de groupe, pas une image de jeu ni une carte de collisions.

Le ciel, la lune et les étoiles sont indépendants là où le ciel est visible (plage, Mont Foudre, forêt enneigée). Aucun astre n’est ajouté à l’intérieur Armaldo ou aux forêts fermées. Pour Mont Foudre, les nuages sont extraits de la référence, avec complétion locale du corps opaque pour supprimer les trous de détourage.

## Jour/base, nuit, animations
`jour` désigne le dessin de base : il conserve donc l’ambiance sombre de Murky Forest et la lumière intérieure d’Armaldo. Les terrains nocturnes utilisent exactement le filtre Abyss existant (`source/cote_v4_abyss/night.py`). Les ciels et astres nocturnes restent des couches à part.

**Aucune animation ajoutée.** Les vagues, flammes et éclairs figurant sur les planches sources ne sont pas interprétés comme une demande d’animation. Les planches originales sont conservées intégralement au dépôt.

La grotte derrière Waterfall Lake est une entrée **visuelle**. Le lac et l’îlot n’ont pas été remplacés par un pont pour inventer un accès ; navigation, collisions et transition vers une zone restent à définir dans PMDO.

## Sources et méthode
Commit utilisateur **54d3731** : 8 fichiers, dont `Energetic Forest (1).png` et `Energetic Forest.png` sont **identiques par SHA-256**. Il y a donc 7 références uniques ; les planches Murky Forest et Beach sont déclinées en plusieurs scènes.

Les compositions sont de nouvelles propositions générées à partir des références, avec masquage et mise au format nearest. **Leur dessin n’est pas certifié identique à des tuiles natives**. Les dispositions et proportions ont des variations artistiques, notamment la seconde clairière. Il n’y a pas eu de recoloration certifiée en palette native complète.

Les bruts initiaux et corrigés restent dans `bruts/`. Les rendus retenus utilisent explicitement `01_murky_entree_corrigee`, les trois fichiers `*_entree` de Friend Areas et `10_foret_neige_corrigee` ; les premiers essais correspondants restent historiques et ne sont pas les compositions proposées.

Les références recadrées pour guider le générateur et leurs empreintes figurent dans `source/references_54d3731/`. Les originaux fournis à la racine ne sont pas modifiés. Attributions imprimées sur les sources : Haalfpack / Noctowl2000 pour Murky Forest, redblueyellow pour Beach, Toastypk pour les Friend Areas concernées. Respecter également les droits Pokémon Mystery Dungeon et les autres crédits des planches. La disponibilité publique n’est pas une licence générale de réutilisation.

## Vérifications
`verification.json` : **160 PNG décodés**, 8 fichiers sources vérifiés par SHA-256, doublon confirmé, **20 recompositions exactes**, conversions nocturnes terrain comparées au filtre Abyss, absence d’astres dans les scènes sans ciel, absence de fichier animé. Galerie : contrôles avec DOM simulé ; pas de validation GPU.

Scripts : `source/references_54d3731/build.py`, `gallery.py`, `verify.py`, `test_viewer.cjs`. Dépendances : Pillow, numpy. **Pas de modification de `.rsground`, collisions ou mod natif ; aucune validation en jeu.**
