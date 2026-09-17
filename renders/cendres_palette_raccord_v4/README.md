# Grotte cendrée V4 — raccord rocheux et palette thermique commune

Correction non destructive de V3 (`cafe488`). Le chemin mène toujours à la grotte, et les six éruptions restent uniquement dans la lave latérale.

## Raccord près de la grotte

La découpe verticale artificielle à gauche de l’approche, qui faisait remonter le magma dans un rectangle entre la falaise et le chemin, est comblée par un pied rocheux irrégulier. Un petit raccord a été généré sur magenta depuis le détail existant, détouré puis ajouté **uniquement sur les pixels auparavant vides** dans la région `(107,198)–(189,294)`.

Les pixels rocheux de V3, le chemin et la grotte restent inchangés. `masque_reparation_locale.png` délimite les ajouts ; `RACCORD_AVANT_APRES.png` permet d’inspecter la correction. Un fin liseré refroidi suit la nouvelle limite roche/magma, sans décalage de vagues.

## Magma, bulles et jets assortis

Tous utilisent une même gamme de **16 couleurs** : bordeaux sombre → rouge → orange → ambre → jaune chaud. Les jets peuvent atteindre les couleurs les plus claires, mais ne passent pas à une palette blanche ou différente. Les corps des bulles reçoivent un grain léger tiré du matériau de magma, tout en préservant les fissures et leurs contours.

Les huit poses générées de V3 sont conservées et recolorées. Chaque site garde l’ordre bulle basse → gonflement → fissures → éclatement → jet naissant → colonne → retombée → résidu → repos. Le calque de chauffe locale augmente avant/après l’apparition de la bulle, culmine vers l’éclatement, puis décroît. Aucune éruption ne recouvre le chemin.

## Véritable palette cycling, sans déplacement arbitraire du décor

La texture est stabilisée sur une image clé déjà générée de V3. **Il n’y a plus de morphing entre quatre textures ni de flot optique.**

- `MAGMA_INDICES_FIXES.png` : plan d’indices immuable.
- Un indice encode une des 16 classes thermiques artistiques et une des 16 phases spatiales des veines, soit 256 entrées.
- La phase se propage le long du réseau chaud, via une distance pondérée dont le coût est plus faible dans les veines incandescentes. La roche constitue un obstacle à cette propagation.
- `PALETTES_064.json` contient les **64 tables de palette**, la gamme commune et les classes froides immobiles.
- Les PNG `01_magma_palette_cycling` sont réellement **indexés en mode P** : mêmes indices dans toutes les images, tables RGB différentes.
- Les classes froides 0–3 gardent exactement le même RGB. Seule l’intensité des classes chaudes varie dans une plage bornée, avec retour continu vers l’état initial ; pas de cycle arc-en-ciel ni de bascule d’une croûte froide directement au jaune.
- Le contact refroidi reste stable et la chauffe locale des événements est sur un calque indépendant.

Cette animation traduit une **logique visuelle de chauffe, émission et refroidissement**. Le palette cycling ne simule pas à lui seul un écoulement ou la thermodynamique : les classes ne sont pas des températures mesurées, et les jets restent une stylisation PMD. Ce n’est pas une affirmation de validité physique d’un feu réel sortant de lave.

## Fichiers

Scène : `cendres_palette_raccord/`, 648×504.
- `COMPOSITION.png`, `ANIMATION_COMPLETE.webp`.
- 64 compositions PNG, 100 ms par phase, boucle de 6,4 s.
- 8 groupes animés de 64 PNG : magma indexé, chauffe locale, six séquences d’éruption.
- 6 calques statiques : contact refroidi, sol, rebords, parois, profondeur de grotte, raccord local.
- `cendres_palette_raccord.ora` : **14 calques** à la phase zéro. Les séquences PNG portent l’animation, pas l’ORA.
- Les masques de contrôle, palettes, poses recolorées et la planche de séquence sont fournis à côté du dossier de scène.
- `GROTTE_PALETTE_V4_calques.zip` : scène, calques, palettes, contrôles et documentation ; bruts et galerie exclus.
- Galerie autonome à la racine : `apercu_cendres_palette_raccord_v4.html`, avec animation, sélection des calques, curseur des phases et comparaison du raccord.

L’ordre exact de composition est dans `manifest.json`. Les calques de terrain sont des surfaces visibles, pas des objets complets avec leurs faces cachées reconstruites. Les références et poses V3 restent nécessaires pour reconstruire le lot depuis les scripts du dépôt.

## Vérifications

Exécuter `source/cendres_palette_raccord_v4/build.py` puis `verify.py` avec Pillow, numpy et scipy.

Contrôles : 64 compositions distinctes et opaques, recomposition exacte depuis les PNG et l’ORA ; indices du magma identiques dans les 64 PNG ; palettes intégrées identiques aux tables JSON ; classes froides figées ; couleurs du magma et des éruptions dans la même gamme ; pixels de roche V3 préservés ; modifications du terrain limitées au masque local ; corridor jusqu’à la grotte inchangé ; aucune éruption sur le terrain ; ordre causal des six séquences conservé. La jonction fin/début du magma a une variation comparable aux autres transitions (valeurs dans le manifeste).

Pas de test runtime PMDO/GPU, de collisions, de dégâts ou de script de zone configurés. Le masque de passage est un contrôle géométrique, pas une carte de collisions validée. Les générations et adaptations ne sont pas des nouveaux sprites officiels.
