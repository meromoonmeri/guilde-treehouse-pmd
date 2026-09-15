# Chemin forestier — printemps, automne, hiver

Un dessin de printemps généré en style PMD, puis deux passages au générateur pour l’automne et l’hiver en conservant son cadrage et ses principaux éléments. **Un même masque de chemin** est utilisé dans les six versions jour/nuit. Il relie le bord sud au bord nord sans interruption.

640×480,8calques par scène : sol saisonnier, chemin commun, deux rochers regroupés, tronc couché, végétation arrière, arbres gauche, arbres droite et canopée avant. PNG et ORA. Le sol sous les éléments est reconstruit par voisinage ; les groupes de végétation ne sont pas des arbres individuels complets avec leurs parties cachées retrouvées.

Les masques structuraux sont partagés entre saisons ; les détails de neige, feuillage, fleurs, brindilles et couleurs proviennent des éditions générées. Cela ne signifie pas que tous les contours dessinés des trois bruts sont bit-identiques. Aucune déformation ligne par ligne n’est appliquée aux images : elle endommagerait les petits motifs pixel-art.

Arbres et textures **générés dans une DA PMD**, pas des sprites natifs canoniques récupérés. Références locales fournies au générateur : Apple Woods Entrance et Mystifying Forest Entrance. Le même chemin clair en S, les deux rochers et le tronc servent de repères communs.

Nuit : filtre exact Abyss, appliqué aux calques. Les trois forêts sont statiques ; aucune animation de vent/neige/pétales n’est revendiquée.

Vérification commune dans `renders/tours_hooh_v1/verification.json` : masque de chemin identique et connecté, recomposition des6scènes et6ORA, nuit exacte. **Pas de test PMDO/collisions**. PNG Ground640×480, import éventuel8px sans changement d’échelle.
